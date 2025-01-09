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

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

handler = logging.StreamHandler(sys.stdout)
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)

if not logger.handlers:
    logger.addHandler(handler)

sc = SparkContext()
glueContext = GlueContext(sc)
spark = glueContext.spark_session

args = getResolvedOptions(sys.argv, [
                          'JOB_NAME', 'SRC_BUCKET', 'SRC_PREFIX', 'DEST_BUCKET', 'DEST_PREFIX', 'START_DATE', 'END_DATE'])

job = Job(glueContext)
job.init(args['JOB_NAME'], args)

src_bucket = args['SRC_BUCKET']
src_prefix = args['SRC_PREFIX']
dest_bucket = args['DEST_BUCKET']
dest_prefix = args['DEST_PREFIX']

# Parse and validate the date parameters
try:
    start_date = datetime.datetime.strptime(
        args['START_DATE'], '%Y-%m-%d').date()
    end_date = datetime.datetime.strptime(args['END_DATE'], '%Y-%m-%d').date()
    if start_date > end_date:
        raise ValueError("START_DATE cannot be after END_DATE.")
except ValueError as e:
    logger.error(f"Invalid date format or range: {e}. Please use YYYY-MM-DD.")
    sys.exit(1)

# Function to generate S3 paths based on date range
def generate_date_paths(start_date, end_date, src_bucket, src_prefix):
    path_list = []
    current_date = date(start_date.year, start_date.month, 1)
    end_month = date(end_date.year, end_date.month, 1)
    while current_date <= end_month:
        year = current_date.year
        month = current_date.month
        # Construct the path for this year and month
        path = f"s3://{src_bucket}/{src_prefix}/indicator=*/observation_year={year}/observation_month={month}"
        path_list.append(path)
        # Move to the next month
        if month == 12:
            current_date = date(year + 1, 1, 1)
        else:
            current_date = date(year, month + 1, 1)
    return path_list


# Generate the list of paths to read
paths_to_read = generate_date_paths(
    start_date, end_date, src_bucket, src_prefix)

# Read JSON data from the generated paths
try:
    df = spark.read \
        .option("basePath", f"s3://{src_bucket}/{src_prefix}") \
        .json(paths_to_read)
    logger.info("Data successfully read into DataFrame.")
except Exception as e:
    logger.error(f"An error occurred while reading data: {e}")
    sys.exit(1)

# Ensure 'observation_date' is in date format
df = df.withColumn("observation_date", F.to_date(F.col("date"), "yyyy-MM-dd"))
df = df.withColumn("observation_date", F.date_format(
    F.col("observation_date"), "yyyy-MM-dd"))

# Filter data within the specified date range
df = df.filter(
    (F.col("observation_date") >= F.lit(start_date)) &
    (F.col("observation_date") <= F.lit(end_date))
)
logger.info(f"Data filtered between {start_date} and {end_date}.")

# Transform the 'value' column to numeric, handling non-numeric values
def process_value(value):
    try:
        num = float(value)
        if num.is_integer():
            return int(num)
        else:
            return round(num, 2)
    except (ValueError, TypeError):
        return None


process_value_udf = F.udf(process_value, returnType=DoubleType())

transformed_df = (
    df.filter(F.col("value") != ".")
    .withColumn("observation_value", process_value_udf(F.col("value")))
    .drop("value", "realtime_end", "realtime_start", "date")
)
logger.info("Data transformation complete.")

# Extract 'indicator' from file path using temporary column
transformed_df = transformed_df.withColumn(
    "indicator_path", F.input_file_name())

# Extract 'indicator' value from 'indicator_path' using regex
transformed_df = transformed_df.withColumn(
    "indicator",
    F.regexp_extract(F.col("indicator_path"), r'indicator=([^/]+)', 1)
)
logger.info("Indicator column extracted from file paths.")

# Check for missing 'indicator' values
missing_indicators = transformed_df.filter(
    (F.col("indicator").isNull()) | (F.col("indicator") == ""))
missing_count = missing_indicators.count()
if missing_count > 0:
    logger.warning(
        f"There are {missing_count} records with missing 'indicator' values.")
else:
    logger.info("All records have 'indicator' values.")

# Drop the 'indicator_path' column as it's no longer needed
transformed_df = transformed_df.drop('indicator_path')

transformed_df = transformed_df.withColumn(
    "observation_year",
    F.year("observation_date").cast(IntegerType())
)

transformed_df = transformed_df.withColumn(
    "observation_month",
    F.month("observation_date").cast(IntegerType())
)
logger.info("Partition columns 'observation_year' and 'observation_month' added.")

# Deduplicate data if necessary
transformed_df = transformed_df.dropDuplicates(
    ['indicator', 'observation_date'])
logger.info(
    "Duplicate records removed based on 'indicator' and 'observation_date'.")

# Configure Spark for dynamic partition overwrite
spark.conf.set("spark.sql.sources.partitionOverwriteMode", "dynamic")

# Write transformed data back to S3, partitioned by indicator/year/month
output_path = f"s3://{dest_bucket}/{dest_prefix}"

try:
    transformed_df.write.mode("overwrite") \
        .partitionBy("indicator", "observation_year", "observation_month") \
        .parquet(output_path)
    logger.info(f"Data successfully transformed and saved to {output_path}")

except Exception as e:
    logger.error(f"An error occurred during data write: {e}")
    sys.exit(1)


# Commit the Glue job
job.commit()
