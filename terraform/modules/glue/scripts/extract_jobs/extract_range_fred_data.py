import boto3
import requests
from datetime import datetime, timezone
import sys
import pandas as pd  # Add pandas to handle date range logic
from awsglue.utils import getResolvedOptions
from pyspark.context import SparkContext
from awsglue.context import GlueContext
from awsglue.dynamicframe import DynamicFrame
from awsglue.job import Job
import logging
from pyspark.sql.functions import lit

# logging configuration
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
handler = logging.StreamHandler(sys.stdout)
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)

s3 = boto3.client('s3')

sc = SparkContext.getOrCreate()
glueContext = GlueContext(sc)
spark = glueContext.spark_session
job = Job(glueContext)

args = getResolvedOptions(sys.argv, ["JOB_NAME", "RAW_DATA_BUCKET", "TARGET_PATH", "START_DATE", "END_DATE", "API_KEY"])
bucket_name = args["RAW_DATA_BUCKET"]
target_path = args["TARGET_PATH"]
obs_start_date_str = args["START_DATE"]
obs_end_date_str = args["END_DATE"]
fred_api_key = args["API_KEY"]

job.init(args["JOB_NAME"], args)

indicator_list = ["DGS10", "EFFR", "CSUSHPINSA", "UNRATE", "CPIAUCSL", "PCE", "JTSJOL", "JTSHIR", "JTSTSR", "PSAVERT", "CSCICP03USM665S"]

try:
    start_date = datetime.strptime(obs_start_date_str, '%Y-%m-%d').date()
    end_date = datetime.strptime(obs_end_date_str, '%Y-%m-%d').date()
except ValueError as e:
    logger.error(f"Error parsing dates: {e}. Please use %Y-%m-%d format.")
    sys.exit(1)

def extract_fred_data(series_id, start_date, end_date, fred_api_key):
    url = f"https://api.stlouisfed.org/fred/series/observations?series_id={series_id}&api_key={fred_api_key}&file_type=json&observation_start={start_date}&observation_end={end_date}"
    try:
        response = requests.get(url)
        response.raise_for_status()
        logger.info(f"Successfully retrieved data for {series_id} from FRED API")
        return response.json()
    except requests.exceptions.RequestException as e:
        logger.error(f"Error fetching data for {series_id}: {e}")
        return None

# Generate list of months between start_date and end_date
date_range = pd.date_range(start=start_date, end=end_date, freq='MS')  # Monthly start frequency
months = [(date.year, date.month) for date in date_range]

for indicator in indicator_list:
    logger.info(f"Processing indicator: {indicator}")

    for year, month in months:  # Iterate over each year and month
        logger.info(f"Processing data for {indicator} for {year}-{month:02d}")

        data = extract_fred_data(indicator, f"{year}-{month:02d}-01", f"{year}-{month:02d}-28", fred_api_key)

        if data:
            try:
                observations = data.get('observations')
                if observations and len(observations) > 0:
                    # Check if data already exists
                    s3_key_prefix = f"{target_path}/indicator={indicator}/observation_year={year}/observation_month={month:02d}/"
                    try:
                        response = s3.list_objects_v2(Bucket=bucket_name, Prefix=s3_key_prefix)
                        if 'Contents' in response:
                            logger.info(f"Data for {indicator} in {year}-{month:02d} already exists. Skipping ingestion.")
                            continue
                    except Exception as e:
                        logger.error(f"Error checking for existing files: {e}")
                        continue

                    ingestion_timestamp = datetime.now(timezone.utc).isoformat()

                    # Add additional columns to each observation
                    for observation in observations:
                        observation['indicator'] = indicator
                        observation['observation_year'] = year
                        observation['observation_month'] = month
                        observation['ingestion_timestamp'] = ingestion_timestamp

                    # Create a Spark DataFrame from the list of dictionaries (observations)
                    df = spark.createDataFrame(observations)

                    # Coalesce to 1 partition to ensure only one file per partition
                    df = df.coalesce(1)

                    dynamic_frame = DynamicFrame.fromDF(df, glueContext, "fred_data")

                    glueContext.write_dynamic_frame.from_options(
                        frame=dynamic_frame,
                        connection_type="s3",
                        connection_options={
                            "path": f"s3://{bucket_name}/{target_path}",
                            "partitionKeys": ["indicator", "observation_year", "observation_month"]
                        },
                        format="json"
                    )
                    logger.info(f"Data for {indicator} ingested for {year}-{month:02d} stored in S3 at s3://{bucket_name}/{target_path}/indicator={indicator}/observation_year={year}/observation_month={month:02d}/")
                else:
                    logger.warning(f"No observations found for {indicator} for {year}-{month:02d} within the specified date range")

            except Exception as e:
                logger.error(f"Error processing or storing data for {indicator} for {year}-{month:02d}: {e}")
        else:
            logger.warning(f"Extraction failed for {indicator} for {year}-{month:02d}, skipping S3 upload.")

job.commit()
