import sys
import datetime
from datetime import date
import logging
import traceback
import pyspark.sql.functions as F
from pyspark.sql.types import DoubleType, IntegerType
from awsglue.utils import getResolvedOptions
from pyspark.context import SparkContext
from awsglue.context import GlueContext
from awsglue.job import Job
import boto3
from functools import reduce
from pyspark.sql import DataFrame

class Logger:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.INFO)
        handler = logging.StreamHandler(sys.stdout)
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        if not self.logger.handlers:
            self.logger.addHandler(handler)

class S3Manager:
    def __init__(self, bucket, prefix):
        self.bucket = bucket
        self.prefix = prefix
        self.s3_client = boto3.client('s3')
        self.logger = logging.getLogger(__name__)

    def get_indicator_list(self):
        self.logger.info(f"Fetching indicator list from s3://{self.bucket}/{self.prefix}")
        indicators = []
        try:
            paginator = self.s3_client.get_paginator('list_objects_v2')
            first_level_prefix = f"{self.prefix}/"
            second_level_pages = paginator.paginate(Bucket=self.bucket, Prefix=first_level_prefix, Delimiter='/')

            for page in second_level_pages:
                if 'CommonPrefixes' in page:
                    for common_prefix in page['CommonPrefixes']:
                        prefix = common_prefix['Prefix']
                        if "indicator=" in prefix:
                            indicator = prefix.split("indicator=")[-1].rstrip('/')
                            indicators.append(indicator)
                            self.logger.debug(f"Found indicator: {indicator}")
                else:
                    self.logger.warning(f"No CommonPrefixes found in page")

            if not indicators:
                self.logger.warning("No indicators found in S3")
            else:
                self.logger.info(f"Found {len(indicators)} indicators")

            return indicators

        except Exception as e:
            self.logger.error(f"Error fetching indicator list: {str(e)}")
            self.logger.error(traceback.format_exc())
            raise

class DataProcessor:
    def __init__(self, spark_session, src_bucket, src_prefix, dest_bucket, dest_prefix):
        self.spark = spark_session
        self.src_bucket = src_bucket
        self.src_prefix = src_prefix
        self.dest_bucket = dest_bucket
        self.dest_prefix = dest_prefix
        self.logger = logging.getLogger(__name__)

    def read_yearly_data(self, indicator, year):
        self.logger.info(f"Reading data for indicator {indicator}, year {year}")
        monthly_dfs = []
        months_processed = 0
        months_with_data = 0

        for month in range(1, 13):
            input_path = f"s3://{self.src_bucket}/{self.src_prefix}/indicator={indicator}/observation_year={year}/observation_month={month}"
            try:
                self.logger.debug(f"Attempting to read: {input_path}")
                df = self.spark.read.parquet(input_path)
                months_processed += 1

                row_count = df.count()
                if row_count > 0:
                    self.logger.debug(f"Found {row_count} rows for {indicator}, {year}-{month}")
                    df_with_dates = df.withColumn("observation_year", F.year("observation_date")) \
                                    .withColumn("observation_month", F.month("observation_date"))
                    monthly_dfs.append(df_with_dates)
                    months_with_data += 1
                else:
                    self.logger.debug(f"No data found for {indicator}, {year}-{month}")
            except Exception as e:
                self.logger.debug(f"No data found for {indicator}, {year}-{month}: {str(e)}")
                continue

        self.logger.info(f"Processed {months_processed} months, found data in {months_with_data} months for {indicator}, {year}")

        if not monthly_dfs:
            self.logger.warning(f"No data found for indicator {indicator} in year {year}")
            return None

        try:
            if len(monthly_dfs) == 1:
                self.logger.debug(f"Returning single month of data for {indicator}, {year}")
                return monthly_dfs[0]
            else:
                self.logger.debug(f"Combining {len(monthly_dfs)} months of data for {indicator}, {year}")
                return reduce(DataFrame.union, monthly_dfs)
        except Exception as e:
            self.logger.error(f"Error combining monthly data for {indicator}, {year}: {str(e)}")
            self.logger.error(traceback.format_exc())
            raise

    def determine_frequency(self, df):
        try:
            monthly_counts = df.groupBy("observation_year", "observation_month") \
                .agg(F.count("*").alias("observations_per_month"))

            avg_observations = monthly_counts.select(F.avg("observations_per_month")).first()[0]

            frequency = 'daily' if avg_observations > 1.5 else 'monthly'
            self.logger.debug(f"Determined frequency: {frequency} (avg observations per month: {avg_observations:.2f})")
            return frequency

        except Exception as e:
            self.logger.error(f"Error determining data frequency: {str(e)}")
            self.logger.error(traceback.format_exc())
            raise

    def process_indicator_data(self, indicator, year, df):
        self.logger.info(f"Processing data for indicator {indicator}, year {year}")
        try:
            if df is None:
                self.logger.warning(f"No data to process for indicator {indicator}, year {year}")
                return None

            frequency = self.determine_frequency(df)
            self.logger.info(f"Indicator {indicator} for year {year} has {frequency} frequency")

            if frequency == 'daily':
                self.logger.debug(f"Aggregating daily data to monthly for {indicator}, {year}")
                monthly_data = df.groupBy("observation_year", "observation_month") \
                    .agg(F.avg("observation_value").alias("observation_value"))
            else:
                self.logger.debug(f"Keeping monthly data as is for {indicator}, {year}")
                monthly_data = df.select("observation_year", "observation_month", "observation_value")

            monthly_data = monthly_data \
                .withColumn("indicator", F.lit(indicator)) \
                .withColumn("observation_value", F.round("observation_value", 2))

            row_count = monthly_data.count()
            self.logger.info(f"Processed {row_count} months of data for {indicator}, {year}")

            return monthly_data.orderBy("observation_month")

        except Exception as e:
            self.logger.error(f"Error processing data for indicator {indicator}, year {year}: {str(e)}")
            self.logger.error(traceback.format_exc())
            return None

    def write_yearly_data(self, df, indicator, year):
        if df is not None and df.count() > 0:
            output_path = f"s3://{self.dest_bucket}/{self.dest_prefix}/indicator={indicator}/observation_year={year}"
            self.logger.info(f"Writing data to: {output_path}")

            try:
                final_df = df.select(
                    "indicator",
                    "observation_year",
                    "observation_month",
                    "observation_value"
                ).orderBy("observation_month")

                row_count = final_df.count()
                self.logger.info(f"Writing {row_count} rows for {indicator}, {year}")

                final_df.write.mode("overwrite").parquet(output_path)
                self.logger.info(f"Successfully wrote yearly data for indicator {indicator}, year {year}")

            except Exception as e:
                self.logger.error(f"Error writing data for indicator {indicator}, year {year}: {str(e)}")
                self.logger.error(traceback.format_exc())
                raise

class GlueJobManager:
    def __init__(self):
        self.logger = Logger()
        self.sc = SparkContext()
        self.glue_context = GlueContext(self.sc)
        self.spark = self.glue_context.spark_session
        self.job = None
        self.args = None

    def initialize_job(self):
        required_args = [
            'JOB_NAME', 'SRC_BUCKET', 'SRC_PREFIX', 'DEST_BUCKET',
            'DEST_PREFIX', 'START_YEAR', 'END_YEAR', 'INDICATORS'
        ]
        self.args = getResolvedOptions(sys.argv, required_args)
        self.job = Job(self.glue_context)
        self.job.init(self.args['JOB_NAME'], self.args)
        return self.args

    def validate_years(self, start_year, end_year):
        if start_year > end_year:
            raise ValueError(f"START_YEAR ({start_year}) cannot be greater than END_YEAR ({end_year})")
        current_year = datetime.datetime.now().year
        if end_year > current_year + 1:
            raise ValueError(f"END_YEAR ({end_year}) cannot be more than one year in the future")

def parse_indicators(indicator_param, available_indicators):
    logger = logging.getLogger(__name__)
    if not indicator_param or indicator_param.strip() == '':
        logger.info("No specific indicators provided, processing all available indicators")
        return available_indicators

    requested_indicators = [ind.strip() for ind in indicator_param.split(',') if ind.strip()]
    invalid_indicators = [ind for ind in requested_indicators if ind not in available_indicators]
    if invalid_indicators:
        raise ValueError(f"Invalid indicators provided: {invalid_indicators}")

    logger.info(f"Processing specific indicators: {requested_indicators}")
    return requested_indicators

def main():
    logger = logging.getLogger(__name__)
    try:
        job_manager = GlueJobManager()
        args = job_manager.initialize_job()

        s3_manager = S3Manager(args['SRC_BUCKET'], args['SRC_PREFIX'])
        data_processor = DataProcessor(
            job_manager.spark,
            args['SRC_BUCKET'],
            args['SRC_PREFIX'],
            args['DEST_BUCKET'],
            args['DEST_PREFIX']
        )

        start_year = int(args['START_YEAR'])
        end_year = int(args['END_YEAR'])
        job_manager.validate_years(start_year, end_year)

        available_indicators = s3_manager.get_indicator_list()
        if not available_indicators:
            raise ValueError("No indicators found in S3. Exiting.")

        indicator_list = parse_indicators(args['INDICATORS'], available_indicators)
        logger.info(f"Processing {len(indicator_list)} indicators for years {start_year} to {end_year}")

        successful_processes = 0
        failed_processes = 0
        total_processes = len(indicator_list) * (end_year - start_year + 1)

        for indicator in indicator_list:
            logger.info(f"Processing indicator: {indicator}")
            for year in range(start_year, end_year + 1):
                try:
                    logger.info(f"Processing year: {year}")
                    yearly_data = data_processor.read_yearly_data(indicator, year)
                    if yearly_data is None:
                        failed_processes += 1
                        logger.warning(f"No data found for indicator {indicator}, year {year}")
                        continue

                    processed_months = yearly_data.select("observation_year", "observation_month").distinct().collect()

                    for row in processed_months:
                        month = row.observation_month
                        monthly_data = yearly_data.filter((F.col("observation_year") == year) & (F.col("observation_month") == month))
                        processed_data = data_processor.process_indicator_data(indicator, year, monthly_data)
                        if processed_data is not None:
                            data_processor.write_yearly_data(processed_data, indicator, year)
                            successful_processes += 1
                            logger.info(f"Successfully processed {indicator} for year {year}, Month {month}")
                        else:
                            logger.warning(f"No data processed for indicator {indicator}, year {year}, Month {month}")

                except Exception as e:
                    failed_processes += 1
                    logger.error(f"Failed processing {indicator} for year {year}: {str(e)}")
                    logger.error(traceback.format_exc()) # Include traceback here
                    continue

        logger.info(f"Job completed. Success: {successful_processes}/{total_processes}, Failed: {failed_processes}/{total_processes}")
        job_manager.job.commit()

    except Exception as e:
        logger.error(f"Job failed: {e}")
        logger.error(traceback.format_exc()) # Include traceback here
        sys.exit(1)

if __name__ == "__main__":
    main()
