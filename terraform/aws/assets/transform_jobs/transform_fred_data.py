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

# Get indicator list from S3 (using Boto3)
s3 = boto3.client('s3')

# def get_indicator_list_from_s3(bucket, prefix):
#     indicators = []
#     s3 = boto3.client('s3')
#     paginator = s3.get_paginator('list_objects_v2')
#     logger.info(f"s3.get_paginator('list_objects_v2') - {paginator}")
#     pages = paginator.paginate(Bucket=bucket, Prefix=prefix, Delimiter='/')
#     logger.info(f"paginator.paginate(Bucket=bucket, Prefix=prefix, Delimiter='/') - {pages}")
#     for page in pages:
#         if 'CommonPrefixes' in page:
#             for common_prefix in page['CommonPrefixes']:
#                 parts = common_prefix['Prefix'].split('/')
#                 if len(parts) >= 3 and parts[1].startswith("indicator="):
#                     indicator_folder = parts[1]
#                     indicator = indicator_folder.split("=")[1]
#                     indicators.append(indicator)
#                 else:
#                     logger.warning(f"Unexpected prefix format: {common_prefix['Prefix']}")
#     return indicators

def get_indicator_list_from_s3(bucket, prefix):
    indicators = []
    s3 = boto3.client('s3')
    paginator = s3.get_paginator('list_objects_v2')
    logger.info(f"s3.get_paginator('list_objects_v2') - {paginator}")
    pages = paginator.paginate(Bucket=bucket, Prefix=prefix, Delimiter='/')
    logger.info(f"paginator.paginate(Bucket=bucket, Prefix=prefix, Delimiter='/') - {pages}")

    for page in pages:
        if 'CommonPrefixes' in page:
            for common_prefix in page['CommonPrefixes']:
                parts = common_prefix['Prefix'].split('/')
                logger.info(f"Processing prefix: {common_prefix['Prefix']} - Parts: {parts}")

                # Check if 'indicator=' is in the path after 'raw_data/'
                if len(parts) >= 4 and parts[2].startswith("indicator="):
                    indicator_folder = parts[2]
                    indicator = indicator_folder.split("=")[1]
                    indicators.append(indicator)
                else:
                    logger.warning(f"Unexpected prefix format: {common_prefix['Prefix']} - Parts: {parts}")
    return indicators


indicator_list = get_indicator_list_from_s3(src_bucket, src_prefix)

if not indicator_list:
    logger.error("Could not retrieve indicator list from S3. Exiting.")
    sys.exit(1)

logger.info(f"Indicators found: {indicator_list}")

# Helper functions
def generate_indicator_month_paths(src_bucket, src_prefix, indicator, year, month):
    return f"s3://{src_bucket}/{src_prefix}/indicator={indicator}/observation_year={year}/observation_month={month}"

def process_data(df):
    def process_value(value):
        try:
            num = float(value)
            return int(num) if num.is_integer() else round(num, 2)
        except (ValueError, TypeError):
            return None

    process_value_udf = F.udf(process_value, returnType=DoubleType())
    return (
        df.filter(F.col("value") != ".")
        .withColumn("observation_value", process_value_udf(F.col("value")))
        .drop("value", "realtime_end", "realtime_start", "date")
    )

def next_month(current_date):
    if current_date.month == 12:
        return date(current_date.year + 1, 1, 1)
    else:
        return date(current_date.year, current_date.month + 1, 1)

# Main processing loop
for indicator in indicator_list:
    current_date = date(start_date.year, start_date.month, 1)
    end_loop = date(end_date.year, end_date.month, 1)
    while current_date <= end_loop:
        input_path = generate_indicator_month_paths(src_bucket, src_prefix, indicator, current_date.year, current_date.month)
        try:
            filtered_df = spark.read.json(input_path)
            logger.info(f"Read data from: {input_path}")

            filtered_df = filtered_df.withColumn("indicator_path", F.input_file_name())
            filtered_df = filtered_df.withColumn("series_id", F.regexp_extract(F.col("indicator_path"), r'indicator=([^/]+)', 1))
            filtered_df = filtered_df.drop('indicator_path')

            transformed_df = process_data(filtered_df)

            transformed_df = transformed_df.withColumn("observation_year", F.year("observation_date").cast(IntegerType()))
            transformed_df = transformed_df.withColumn("observation_month", F.month("observation_date").cast(IntegerType()))

            output_path = f"s3://{dest_bucket}/{dest_prefix}"
            transformed_df.write.mode("overwrite") \
                .partitionBy("indicator", "observation_year", "observation_month") \
                .parquet(output_path)
            logger.info(f"Data for indicator {indicator} - {current_date.strftime('%Y-%m')} transformed and saved.")

        except Exception as e:
            logger.warning(f"No data found at {input_path}: {e}")

        current_date = next_month(current_date)

job.commit()
