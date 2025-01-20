import sys
import logging
import traceback
from datetime import datetime
import boto3
from awsglue.utils import getResolvedOptions
from pyspark.context import SparkContext
from awsglue.context import GlueContext
from awsglue.job import Job
import pyspark.sql.functions as F

class Logger:
    @staticmethod
    def setup():
        logger = logging.getLogger(__name__)
        logger.setLevel(logging.INFO)
        handler = logging.StreamHandler(sys.stdout)
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        if not logger.handlers:
            logger.addHandler(handler)
        return logger

class SparkManager:
    def __init__(self, args, logger):
        self.args = args
        self.logger = logger
        self.sc = SparkContext()
        self.glueContext = GlueContext(self.sc)
        self.spark = self.glueContext.spark_session
        self.job = Job(self.glueContext)
        self.job.init(args['JOB_NAME'], args)

    def read_indicator_data(self, indicator, year):
        """Reads indicator data from S3"""
        try:
            input_path = f"s3://{self.args['SRC_BUCKET']}/aggregated_data/indicator={indicator}/observation_year={year}"
            self.logger.debug(f"Reading data from: {input_path}")
            return self.spark.read.parquet(input_path)
        except Exception as e:
            self.logger.error(f"Error reading data for {indicator}, year {year}: {str(e)}")
            return None

    def write_to_postgres(self, df, table_name):
        """Write DataFrame to PostgreSQL using JDBC"""
        if df is None or df.rdd.isEmpty():
            return 0

        try:
            db_host = self.args['DB_HOST'].split(':')[0]  # Remove port if present
            jdbc_url = f"jdbc:postgresql://{db_host}:{self.args['DB_PORT']}/{self.args['DB_NAME']}"

            # Create temporary view of the DataFrame
            df.createOrReplaceTempView("source_data")

            # Execute upsert using Spark SQL
            upsert_sql = f"""
            INSERT INTO {table_name} (
                indicator,
                observation_year,
                observation_month,
                observation_value
            )
            VALUES (?, ?, ?, ?)
            ON CONFLICT (indicator, observation_year, observation_month)
            DO UPDATE SET
                observation_value = EXCLUDED.observation_value,
                created_at = CURRENT_TIMESTAMP
            """

            # Write directly to the target table with upsert logic
            df.write \
                .format("jdbc") \
                .option("url", jdbc_url) \
                .option("dbtable", table_name) \
                .option("user", self.args['DB_USER']) \
                .option("password", self.args['DB_PASSWORD']) \
                .mode("append") \
                .save()

            return df.count()
        except Exception as e:
            self.logger.error(f"Error writing to PostgreSQL: {str(e)}")
            raise

class S3Manager:
    def __init__(self, bucket, logger):
        self.bucket = bucket
        self.logger = logger
        self.s3_client = boto3.client('s3')

    def get_indicators(self, specific_indicator=None):
        """Get list of indicators from S3"""
        if specific_indicator:
            return [specific_indicator]

        try:
            indicators = []
            paginator = self.s3_client.get_paginator('list_objects_v2')
            prefix = "aggregated_data/indicator="

            for page in paginator.paginate(Bucket=self.bucket, Prefix=prefix, Delimiter='/'):
                if 'CommonPrefixes' in page:
                    for prefix_obj in page['CommonPrefixes']:
                        indicator = prefix_obj['Prefix'].split('=')[-1].rstrip('/')
                        indicators.append(indicator)

            self.logger.info(f"Found {len(indicators)} indicators")
            return indicators

        except Exception as e:
            self.logger.error(f"Error fetching indicators: {str(e)}")
            raise

def get_year_range(start_year, end_year=None):
    """Generate list of years to process"""
    end_year = end_year or start_year
    return range(start_year, end_year + 1)

def main():
    logger = Logger.setup()

    try:
        # Get required parameters
        args = getResolvedOptions(sys.argv, [
            'JOB_NAME',
            'SRC_BUCKET',
            'START_YEAR',
            'DB_HOST',
            'DB_NAME',
            'DB_USER',
            'DB_PASSWORD',
            'DB_PORT',
            'TABLE_NAME'
        ])

        # Initialize managers
        spark_manager = SparkManager(args, logger)
        s3_manager = S3Manager(args['SRC_BUCKET'], logger)

        # Get optional parameters
        start_year = int(args['START_YEAR'])
        end_year = int(args.get('END_YEAR', start_year))
        specific_indicator = args.get('INDICATOR')

        # Get indicators and years to process
        indicators = s3_manager.get_indicators(specific_indicator)
        years = get_year_range(start_year, end_year)

        if not indicators:
            raise ValueError("No indicators found in S3")

        logger.info(f"Processing {len(indicators)} indicators for years {start_year}-{end_year}")

        # Process data
        successful_loads = 0
        failed_loads = 0
        total_records = 0

        for indicator in indicators:
            for year in years:
                try:
                    logger.info(f"Processing {indicator} for {year}")
                    df = spark_manager.read_indicator_data(indicator, year)

                    if df is not None and df.count() > 0:
                        records = spark_manager.write_to_postgres(df, args['TABLE_NAME'])
                        total_records += records
                        successful_loads += 1
                        logger.info(f"Processed {records} records for {indicator} {year}")
                    else:
                        logger.warning(f"No data found for {indicator} {year}")
                        failed_loads += 1

                except Exception as e:
                    failed_loads += 1
                    logger.error(f"Failed processing {indicator} {year}: {str(e)}")
                    continue

        # Log results
        total_combinations = len(indicators) * len(list(years))
        logger.info(
            f"Job completed: "
            f"Successful: {successful_loads}/{total_combinations}, "
            f"Failed: {failed_loads}/{total_combinations}, "
            f"Total records: {total_records}"
        )

        spark_manager.job.commit()

    except Exception as e:
        logger.error(f"Job failed: {str(e)}")
        logger.error(traceback.format_exc())
        sys.exit(1)

if __name__ == "__main__":
    main()
