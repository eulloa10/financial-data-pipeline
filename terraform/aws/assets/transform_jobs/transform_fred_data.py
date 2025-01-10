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

# Logging setup
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
handler = logging.StreamHandler(sys.stdout)
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
if not logger.handlers:
    logger.addHandler(handler)

# Spark and Glue context initialization
sc = SparkContext()
glueContext = GlueContext(sc)
spark = glueContext.spark_session

# Job arguments
args = getResolvedOptions(sys.argv, [
    'JOB_NAME', 'SRC_BUCKET', 'SRC_PREFIX', 'DEST_BUCKET', 'DEST_PREFIX', 'START_DATE', 'END_DATE'
])
job = Job(glueContext)
job.init(args['JOB_NAME'], args)

src_bucket = args['SRC_BUCKET']
src_prefix = args['SRC_PREFIX']
dest_bucket = args['DEST_BUCKET']
dest_prefix = args['DEST_PREFIX']

# Date parsing and validation
try:
    start_date = datetime.datetime.strptime(args['START_DATE'], '%Y-%m-%d').date()
    end_date = datetime.datetime.strptime(args['END_DATE'], '%Y-%m-%d').date()
    if start_date > end_date:
        raise ValueError("START_DATE cannot be after END_DATE.")
except ValueError as e:
    logger.error(f"Invalid date format or range: {e}. Please use YYYY-MM-DD.")
    sys.exit(1)

s3 = boto3.client('s3')

def get_indicator_list_from_s3(bucket, prefix):
    """
    Fetches a list of indicators from the given bucket and prefix in S3.

    Args:
        bucket (str): The name of the S3 bucket.
        prefix (str): The prefix of the first-level folder ("raw_data/").

    Returns:
        list: A list of indicator names.
    """
    indicators = []
    s3 = boto3.client('s3')
    paginator = s3.get_paginator('list_objects_v2')

    first_level_prefix = f"{prefix}/"

    # Paginate over the second-level prefixes under the first-level prefix
    logger.info(f"Fetching second-level prefixes under {first_level_prefix}")
    second_level_pages = paginator.paginate(Bucket=bucket, Prefix=first_level_prefix, Delimiter='/')

    for page in second_level_pages:
        if 'CommonPrefixes' in page:
            for common_prefix in page['CommonPrefixes']:
                prefix = common_prefix['Prefix']
                logger.info(f"Processing prefix: {prefix}")

                # Extract the indicator name from the prefix
                if "indicator=" in prefix:
                    indicator = prefix.split("indicator=")[-1].rstrip('/')
                    indicators.append(indicator)
                else:
                    logger.warning(f"Unexpected prefix format: {prefix}")
        else:
            logger.warning(f"No CommonPrefixes found in page: {page}")

    return indicators

indicator_list = get_indicator_list_from_s3(src_bucket, src_prefix)

if not indicator_list:
    logger.error("Could not retrieve indicator list from S3. Exiting.")
    sys.exit(1)

logger.info(f"Indicators found: {indicator_list}")

def process_data(df):
    return (
        df.filter(F.col("value") != ".")  # Early filtering
        .withColumn("observation_value", F.col("value").cast(DoubleType()))
        .withColumn("observation_value", F.round("observation_value", 2))  # Use round
        .withColumnRenamed("date", "observation_date")
        .drop("value", "realtime_end", "realtime_start")
        .withColumn("indicator", F.lit(indicator))
        .withColumn("observation_year", F.year("observation_date").cast(IntegerType()))
        .withColumn("observation_month", F.month("observation_date").cast(IntegerType()))
    )

def next_month(current_date):
    if current_date.month == 12:
        return date(current_date.year + 1, 1, 1)
    else:
        return date(current_date.year, current_date.month + 1, 1)

for indicator in indicator_list:
    current_date = date(start_date.year, start_date.month, 1)
    end_loop = date(end_date.year, end_date.month, 1)
    while current_date <= end_loop:
        input_path = f"s3://{src_bucket}/{src_prefix}/indicator={indicator}"
        try:
            filtered_df = spark.read.json(input_path)
            logger.info(f"Read data from: {input_path}")

            transformed_df = process_data(filtered_df)

            output_path = f"s3://{dest_bucket}/{dest_prefix}/indicator={indicator}"

            transformed_df.write.mode("overwrite") \
                .partitionBy("observation_year", "observation_month") \
                .parquet(output_path)
            logger.info(f"Data for indicator {indicator} - {current_date.strftime('%Y-%m')} transformed and saved.")

        except Exception as e:
            logger.warning(f"Error processing data: {e}")

        current_date = next_month(current_date)

job.commit()
