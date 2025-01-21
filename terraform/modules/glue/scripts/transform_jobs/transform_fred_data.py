import sys
import datetime
from datetime import date
import logging
import pyspark.sql.functions as F
from pyspark.sql.types import DoubleType, IntegerType
from awsglue.utils import getResolvedOptions
from pyspark.context import SparkContext
from awsglue.context import GlueContext
from awsglue.job import Job
import boto3

# Default indicators list
DEFAULT_INDICATORS = [
    "DGS10", "EFFR", "CSUSHPINSA", "UNRATE", "CPIAUCSL",
    "PCE", "JTSJOL", "JTSHIR", "JTSTSR", "PSAVERT", "CSCICP03USM665S"
]

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
        """Fetches list of indicators from S3"""
        indicators = []
        paginator = self.s3_client.get_paginator('list_objects_v2')
        first_level_prefix = f"{self.prefix}/"

        try:
            second_level_pages = paginator.paginate(
                Bucket=self.bucket,
                Prefix=first_level_prefix,
                Delimiter='/'
            )

            for page in second_level_pages:
                if 'CommonPrefixes' in page:
                    for common_prefix in page['CommonPrefixes']:
                        prefix = common_prefix['Prefix']
                        if "indicator=" in prefix:
                            indicator = prefix.split("indicator=")[-1].rstrip('/')
                            indicators.append(indicator)

            return indicators
        except Exception as e:
            self.logger.error(f"Error fetching indicators: {e}")
            raise

class DataTransformer:
    def __init__(self, spark_session):
        self.spark = spark_session
        self.logger = logging.getLogger(__name__)

    def process_data(self, df, indicator, start_date, end_date):
        return (
            df.filter(F.col("value") != ".")
            .filter(F.col("date").between(start_date.strftime('%Y-%m-%d'), end_date.strftime('%Y-%m-%d')))
            .withColumn("observation_value", F.col("value").cast(DoubleType()))
            .withColumn("observation_value", F.round("observation_value", 2))
            .withColumnRenamed("date", "observation_date")
            .drop("value", "realtime_end", "realtime_start")
            .withColumn("indicator", F.lit(indicator))
            .withColumn("observation_year", F.year("observation_date").cast(IntegerType()))
            .withColumn("observation_month", F.month("observation_date").cast(IntegerType()))
        )

    def transform_and_save(self, indicator, src_bucket, src_prefix, dest_bucket, dest_prefix, start_date, end_date):
        try:
            input_path = f"s3://{src_bucket}/{src_prefix}/indicator={indicator}"
            self.logger.info(f"Reading data from: {input_path}")
            filtered_df = self.spark.read.json(input_path)

            transformed_df = self.process_data(filtered_df, indicator, start_date, end_date)

            if transformed_df.count() > 0:
                output_base_path = f"s3://{dest_bucket}/{dest_prefix}/indicator={indicator}"

                # Write only to specific year partitions
                for year in range(start_date.year, end_date.year + 1):
                    year_data = transformed_df.filter(F.col("observation_year") == year)
                    if year_data.count() > 0:
                        output_path = f"{output_base_path}/observation_year={year}"

                        months = year_data.select('observation_month').distinct().collect()
                        self.logger.info(f"Processing {len(months)} months for {indicator} year {year}")

                        # Write to specific year partition
                        year_data.write \
                            .partitionBy("observation_month") \
                            .mode("overwrite") \
                            .parquet(output_path)

                        for month in months:
                            self.logger.info(f"Processed month {month.observation_month} for {indicator} year {year}")
                        self.logger.info(f"Data transformed for {indicator} year {year}")

                return True
            else:
                self.logger.info(f"No data found for {indicator} between {start_date} and {end_date}")
                return False
        except Exception as e:
            self.logger.error(f"Error transforming {indicator}: {e}")
            return False

def validate_indicators(indicators):
    """Validate that provided indicators exist in the default list"""
    invalid_indicators = [ind for ind in indicators if ind not in DEFAULT_INDICATORS]
    if invalid_indicators:
        raise ValueError(f"Invalid indicators provided: {invalid_indicators}")
    return indicators

def parse_indicators(indicator_param):
    """Parse and validate indicator parameter"""
    if not indicator_param or indicator_param.strip() == '':
        return DEFAULT_INDICATORS

    indicators = [ind.strip() for ind in indicator_param.split(',') if ind.strip()]
    if not indicators:
        return DEFAULT_INDICATORS

    return validate_indicators(indicators)

def main():
    logger_setup = Logger()
    logger = logging.getLogger(__name__)

    try:
        # Initialize Spark/Glue
        sc = SparkContext()
        glueContext = GlueContext(sc)
        spark = glueContext.spark_session
        job = Job(glueContext)

        # Get job parameters
        args = getResolvedOptions(sys.argv, [
            'JOB_NAME',
            'SRC_BUCKET',
            'SRC_PREFIX',
            'DEST_BUCKET',
            'DEST_PREFIX',
            'START_DATE',
            'END_DATE',
            'INDICATOR'
        ])

        job.init(args['JOB_NAME'], args)

        # Parse dates
        try:
            start_date = datetime.datetime.strptime(args['START_DATE'], '%Y-%m-%d').date()
            end_date = datetime.datetime.strptime(args['END_DATE'], '%Y-%m-%d').date()
            if start_date > end_date:
                raise ValueError("START_DATE cannot be after END_DATE.")
        except ValueError as e:
            logger.error(f"Invalid date format or range: {e}")
            sys.exit(1)

        # Initialize components
        s3_manager = S3Manager(args['SRC_BUCKET'], args['SRC_PREFIX'])
        transformer = DataTransformer(spark)

        # Parse indicators
        try:
            indicators_to_process = parse_indicators(args['INDICATOR'])
            logger.info(f"Processing indicators: {indicators_to_process}")
        except ValueError as e:
            logger.error(f"Invalid indicators provided: {e}")
            sys.exit(1)

        # Process data
        successful_transforms = 0
        failed_transforms = 0

        for indicator in indicators_to_process:
            success = transformer.transform_and_save(
                indicator,
                args['SRC_BUCKET'],
                args['SRC_PREFIX'],
                args['DEST_BUCKET'],
                args['DEST_PREFIX'],
                start_date,
                end_date
            )

            if success:
                successful_transforms += 1
            else:
                failed_transforms += 1

        # Log results
        logger.info(
            f"Job completed. "
            f"Successful transforms: {successful_transforms}/{len(indicators_to_process)} indicators. "
            f"Failed transforms: {failed_transforms}/{len(indicators_to_process)}. "
        )

        job.commit()

    except Exception as e:
        logger.error(f"Job failed: {e}")
        logger.error(traceback.format_exc())
        sys.exit(1)

if __name__ == "__main__":
    main()
