import boto3
import requests
from datetime import datetime, timezone
import sys
import pandas as pd
from awsglue.utils import getResolvedOptions
from pyspark.context import SparkContext
from awsglue.context import GlueContext
from awsglue.dynamicframe import DynamicFrame
from awsglue.job import Job
import logging
from pyspark.sql.functions import lit

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

class FREDDataExtractor:
    def __init__(self, api_key):
        self.api_key = api_key
        self.logger = logging.getLogger(__name__)

    def extract_data(self, series_id, start_date, end_date):
        url = f"https://api.stlouisfed.org/fred/series/observations"
        params = {
            'series_id': series_id,
            'api_key': self.api_key,
            'file_type': 'json',
            'observation_start': start_date,
            'observation_end': end_date
        }
        try:
            response = requests.get(url, params=params)
            response.raise_for_status()
            self.logger.info(f"Successfully retrieved data for {series_id}")
            return response.json()
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Error fetching data for {series_id}: {e}")
            return None

class S3Manager:
    def __init__(self, bucket_name, target_path):
        self.bucket_name = bucket_name
        self.target_path = target_path
        self.s3_client = boto3.client('s3')
        self.logger = logging.getLogger(__name__)

    def check_data_exists(self, indicator, year, month):
        s3_key_prefix = f"{self.target_path}/indicator={indicator}/observation_year={year}/observation_month={month:02d}/"
        try:
            response = self.s3_client.list_objects_v2(
                Bucket=self.bucket_name,
                Prefix=s3_key_prefix
            )
            return 'Contents' in response
        except Exception as e:
            self.logger.error(f"Error checking for existing files: {e}")
            return False

class DataProcessor:
    def __init__(self, glue_context, bucket_name, target_path):
        self.glue_context = glue_context
        self.spark = glue_context.spark_session
        self.bucket_name = bucket_name
        self.target_path = target_path
        self.logger = logging.getLogger(__name__)

    def process_and_store_data(self, observations, indicator, year, month):
        try:
            ingestion_timestamp = datetime.now(timezone.utc).isoformat()

            # Add additional columns
            for observation in observations:
                observation['indicator'] = indicator
                observation['observation_year'] = year
                observation['observation_month'] = month
                observation['ingestion_timestamp'] = ingestion_timestamp

            # Create and process DataFrame
            df = self.spark.createDataFrame(observations).coalesce(1)
            dynamic_frame = DynamicFrame.fromDF(df, self.glue_context, "fred_data")

            # Write to S3
            self.glue_context.write_dynamic_frame.from_options(
                frame=dynamic_frame,
                connection_type="s3",
                connection_options={
                    "path": f"s3://{self.bucket_name}/{self.target_path}",
                    "partitionKeys": ["indicator", "observation_year", "observation_month"]
                },
                format="json"
            )
            self.logger.info(f"Data stored for {indicator} {year}-{month:02d}")
            return True
        except Exception as e:
            self.logger.error(f"Error processing data: {e}")
            return False

def validate_indicators(indicators):
    """
    Validate that provided indicators exist in the default list
    """
    invalid_indicators = [ind for ind in indicators if ind not in DEFAULT_INDICATORS]
    if invalid_indicators:
        raise ValueError(f"Invalid indicators provided: {invalid_indicators}")
    return indicators

def parse_indicators(indicator_param):
    """
    Parse and validate indicator parameter
    Returns list of indicators to process
    """

    if not indicator_param or indicator_param.strip() == '':
        return DEFAULT_INDICATORS

    indicators = [ind.strip() for ind in indicator_param.split(',') if ind.strip()]

    if not indicators:
        return DEFAULT_INDICATORS

    return validate_indicators(indicators)

def main():
    # Initialize logger
    logger_setup = Logger()
    logger = logging.getLogger(__name__)

    try:
        # Initialize Spark/Glue
        sc = SparkContext.getOrCreate()
        glue_context = GlueContext(sc)
        job = Job(glue_context)

        # Get job parameters
        args = getResolvedOptions(sys.argv, [
            "JOB_NAME",
            "RAW_DATA_BUCKET",
            "TARGET_PATH",
            "START_DATE",
            "END_DATE",
            "API_KEY",
            "INDICATOR"
        ])

        job.init(args["JOB_NAME"], args)

        # Optional indicator parameter
        indicator_param = args["INDICATOR"]

        # Parse and validate indicators
        try:
            indicators_to_process = parse_indicators(indicator_param)
            logger.info(f"Processing indicators: {indicators_to_process}")
        except ValueError as e:
            logger.error(f"Invalid indicators provided: {e}")
            sys.exit(1)

        # Initialize components
        extractor = FREDDataExtractor(args["API_KEY"])
        s3_manager = S3Manager(args["RAW_DATA_BUCKET"], args["TARGET_PATH"])
        processor = DataProcessor(glue_context, args["RAW_DATA_BUCKET"], args["TARGET_PATH"])

        # Process date range
        try:
            start_date = datetime.strptime(args["START_DATE"], '%Y-%m-%d').date()
            end_date = datetime.strptime(args["END_DATE"], '%Y-%m-%d').date()
            date_range = pd.date_range(start=start_date, end=end_date, freq='MS')
        except ValueError as e:
            logger.error(f"Error parsing dates: {e}. Please use YYYY-MM-DD format.")
            sys.exit(1)

        # Track processing statistics
        successful_indicators = 0
        failed_indicators = 0
        total_records_processed = 0

        # Main processing loop
        for indicator in indicators_to_process:
            indicator_success = True
            indicator_records = 0

            for date in date_range:
                year, month = date.year, date.month

                # Skip if data exists
                if s3_manager.check_data_exists(indicator, year, month):
                    logger.info(f"Data exists for {indicator} {year}-{month:02d}")
                    continue

                # Extract and process data
                data = extractor.extract_data(
                    indicator,
                    f"{year}-{month:02d}-01",
                    f"{year}-{month:02d}-28"
                )

                if data and data.get('observations'):
                    success = processor.process_and_store_data(
                        data['observations'],
                        indicator,
                        year,
                        month
                    )
                    if success:
                        indicator_records += len(data['observations'])
                    else:
                        indicator_success = False
                else:
                    indicator_success = False

            # Update statistics
            if indicator_success:
                successful_indicators += 1
                total_records_processed += indicator_records
            else:
                failed_indicators += 1

        # Log final statistics
        logger.info(
            f"Job completed. "
            f"Successfully processed: {successful_indicators}/{len(indicators_to_process)} indicators. "
            f"Failed: {failed_indicators}/{len(indicators_to_process)}. "
            f"Total records processed: {total_records_processed}"
        )

        job.commit()

    except Exception as e:
        logger.error(f"Job failed: {e}")
        logger.error(traceback.format_exc())
        sys.exit(1)

if __name__ == "__main__":
    main()
