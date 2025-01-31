import sys
from awsglue.transforms import *
from awsglue.context import GlueContext
from awsglue.job import Job
from awsglue.utils import getResolvedOptions
from pyspark.context import SparkContext
import requests
from datetime import datetime, timezone
from urllib.parse import urlencode
import logging
from pyspark.sql.functions import col


args = getResolvedOptions(sys.argv, ['JOB_NAME', 'API_KEY', 'RAW_DATA_BUCKET', 'TARGET_PATH', 'OBSERVATION_START_DATE',
    'OBSERVATION_END_DATE',
    'INDICATOR'])

logger = logging.getLogger()
logger.setLevel(logging.INFO)

handler = logging.StreamHandler(sys.stdout)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)

logger.info(f"Arguments received: {args}")

sc = SparkContext.getOrCreate()
glueContext = GlueContext(sc)
spark = glueContext.spark_session
job = Job(glueContext)
job.init(args['JOB_NAME'], args)

api_key = args['API_KEY']
raw_data_bucket = args['RAW_DATA_BUCKET']
target_path = args['TARGET_PATH']
observation_start_date = args["OBSERVATION_START_DATE"]
observation_end_date = args["OBSERVATION_END_DATE"]
indicator = args["INDICATOR"]

logger.info(f"Observation start date: {observation_start_date}")
logger.info(f"Observation end date: {observation_end_date}")
logger.info(f"Indicator: {indicator}")

# Function to fetch data from the API
def fetch_data(indicator, api_key, start_date, end_date):
    base_url = "https://api.stlouisfed.org/fred/series/observations"
    params = {
        "series_id": indicator,
        "api_key": api_key,
        "file_type": "json",
        "observation_start": start_date,
        "observation_end": end_date
    }
    url = f"{base_url}?{urlencode(params)}"
    try:
        logger.info(f"Fetching data for {indicator} from {start_date} to {end_date}")
        response = requests.get(url)
        response.raise_for_status()
        logger.info(f"Successfully fetched data for {indicator}")
        return response.json()
    except requests.exceptions.RequestException as e:
        logger.error(f"Error fetching data for {indicator}: {e}")
        return None

# Function to transform data into structured format
def transform_data(data, indicator):
    logger.info(f"Transforming data for {indicator}")
    if data is None:
        logger.info("No data to transform")
        return []

    observations = data.get("observations", [])
    transformed_data = []
    ingestion_timestamp = datetime.now(timezone.utc).replace(microsecond=0).isoformat()

    for obs in observations:
        date_str = obs['date']
        try:
            date_obj = datetime.strptime(date_str, '%Y-%m-%d')
            transformed_data.append({
                "indicator": indicator,
                "observation_year": date_obj.year,
                "observation_month": date_obj.month,
                "observation_date": date_str,
                "value": obs['value'],
                "ingestion_timestamp": ingestion_timestamp
            })
        except ValueError as e:
            logger.error(f"Error parsing date '{date_str}' for {indicator}: {e}")
            return None
    return transformed_data

def write_data(df, output_path):
    try:
        df.coalesce(1).write.mode("overwrite").json(output_path)
        logger.info(f"Data written to {output_path}.")
    except Exception as e:
        logger.error(f"Error writing data to S3: {e}")

# Process the indicator
logger.info(f"Processing indicator: {indicator}")
api_data = fetch_data(indicator, api_key, observation_start_date, observation_end_date)

if api_data:
    transformed_data = transform_data(api_data, indicator)

    if transformed_data:
        df_new = spark.createDataFrame(transformed_data)

        if not df_new.rdd.isEmpty():
            year_months = df_new.select("observation_year", "observation_month").distinct().collect()

            for row in year_months:
                year = row["observation_year"]
                month = row["observation_month"]

                df_month = df_new.filter((col("observation_year") == year) & (col("observation_month") == month))

                output_path = f"s3://{raw_data_bucket}/{target_path}/indicator={indicator}/year={year}/month={month}"
                write_data(df_month, output_path)
        else:
            logger.warning(f"No data to write for {indicator} (DataFrame is empty).")
    else:
        logger.warning(f"No observations found or error during transform for {indicator} from {observation_start_date} to {observation_end_date}.")
else:
    logger.warning(f"No data returned from API for {indicator} from {observation_start_date} to {observation_end_date}.")

job.commit()
