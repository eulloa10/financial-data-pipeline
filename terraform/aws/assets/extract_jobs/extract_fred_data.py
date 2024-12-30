import boto3
import json
import requests
from datetime import datetime, timezone
import sys
from awsglue.utils import getResolvedOptions
from pyspark.context import SparkContext
from awsglue.context import GlueContext
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

args = getResolvedOptions(sys.argv, ["JOB_NAME", "raw_data_bucket", "target_path", "obs_start_date", "obs_end_date", "API_KEY"])
bucket_name = args["raw_data_bucket"]
target_path = args["target_path"]
obs_start_date_str = args["obs_start_date"]
obs_end_date_str = args["obs_end_date"]
fred_api_key = args["API_KEY"]

job.init(args["JOB_NAME"], args)

indicator_list = ["DGS10", "EFFR" ]

# indicator_list = ["DGS10", "EFFR", "CSUSHPINSA", "UNRATE", "CPIAUCSL", "PCE", "JTSJOL", "JTSHIR", "JTSTSR", "PSAVERT", "CSCICP03USM665S"]

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

for indicator in indicator_list:
    logger.info(f"Processing indicator: {indicator}")
    data = extract_fred_data(indicator, start_date, end_date, fred_api_key)

    if data:
        try:
            observations = data.get('observations')
            if observations and len(observations) > 0:
                observation_year = start_date.year
                observation_month = start_date.month

                # Check if data already exists
                s3_key_prefix = f"{target_path}/indicator={indicator}/observation_year={observation_year}/observation_month={observation_month}/"
                try:
                    response = s3.list_objects_v2(Bucket=bucket_name, Prefix=s3_key_prefix)
                    if 'Contents' in response:
                        logger.info(f"Data for {indicator} in {observation_year}-{observation_month} already exists. Skipping ingestion.")
                        continue
                except Exception as e:
                    logger.error(f"Error checking for existing files: {e}")
                    continue

                ingestion_timestamp = datetime.now(timezone.utc).isoformat()

                df = spark.read.json(sc.parallelize([json.dumps(data)]))

                df = df.withColumn("ingestion_timestamp", lit(ingestion_timestamp))
                df = df.withColumn("indicator", lit(indicator))
                df = df.withColumn("observation_year", lit(observation_year))
                df = df.withColumn("observation_month", lit(observation_month))

                glueContext.write_dynamic_frame.from_options(
                    frame=glueContext.create_dynamic_frame.from_df(df, glueContext.spark_session, "fred_data"),
                    connection_type="s3",
                    connection_options={
                        "path": f"s3://{bucket_name}/{target_path}/indicator={indicator}/observation_year={observation_year}/observation_month={observation_month}/",
                        "partitionKeys": ["indicator", "observation_year", "observation_month"]
                    },
                    format="json"
                )
                logger.info(f"Data for {indicator} ingested at {ingestion_timestamp} stored in S3 at s3://{bucket_name}/{target_path}/indicator={indicator}/observation_year={observation_year}/observation_month={observation_month}/")
            else:
                logger.warning(f"No observations found for {indicator} within the specified date range")

        except Exception as e:
            logger.error(f"Error processing or storing data for {indicator}: {e}")
    else:
        logger.warning(f"Extraction failed for {indicator}, skipping S3 upload.")

job.commit()
