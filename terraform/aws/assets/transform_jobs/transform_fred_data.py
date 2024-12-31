import sys
import datetime
import pyspark.sql.functions as F
from awsglue.utils import getResolvedOptions
from pyspark.context import SparkContext
from awsglue.context import GlueContext
from awsglue.job import Job


args = getResolvedOptions(sys.argv, ['JOB_NAME', 'SRC_BUCKET', 'SRC_PREFIX', 'DEST_BUCKET', 'DEST_PREFIX', 'START_DATE', 'END_DATE'])
sc = SparkContext()
glueContext = GlueContext(sc)
spark = glueContext.spark_session
job = Job(glueContext)
job.init(args['JOB_NAME'], args)


src_bucket = args['SRC_BUCKET']
src_prefix = args['SRC_PREFIX']
dest_bucket = args['DEST_BUCKET']
dest_prefix = args['DEST_PREFIX']

# Parse and validate the date parameters
try:
    start_date = datetime.datetime.strptime(args['START_DATE'], '%Y-%m-%d').date()
    end_date = datetime.datetime.strptime(args['END_DATE'], '%Y-%m-%d').date()
except ValueError as e:
    print("Invalid date format. Please use YYYY-MM-DD.")
    sys.exit(1)

# Read JSON data from S3
input_path = f"s3://{src_bucket}/{src_prefix}"
df = spark.read.option("basePath", input_path).json(input_path)

# Ensure 'observation_date' is in date format
df = df.withColumn("observation_date", F.to_date(F.col("date"), "yyyy-MM-dd"))

# Filter data within the specified date range
df = df.filter((F.col("observation_date") >= F.lit(start_date)) & (F.col("observation_date") <= F.lit(end_date)))

# Proceed with data transformations
def process_value(value):
    try:
        num = float(value)
        if num.is_integer():
            return int(num)
        else:
            return round(num, 1)
    except (ValueError, TypeError):
        return None

process_value_udf = F.udf(process_value)

transformed_df = (
    df.filter(F.col("value") != ".")
    .withColumn("observation_value", process_value_udf(F.col("value")))
    .drop("value", "realtime_end", "realtime_start", "date")  # Drop 'date' as it's renamed
)

# Ensure partition columns are present
if 'indicator' not in transformed_df.columns:
    transformed_df = transformed_df.withColumn("indicator", F.input_file_name())
    transformed_df = transformed_df.withColumn("indicator", F.regexp_extract(F.col("indicator"), r'indicator=([^/]+)', 1))

transformed_df = transformed_df.withColumn("observation_year", F.year("observation_date"))
transformed_df = transformed_df.withColumn("observation_month", F.month("observation_date"))

# Deduplicate data if necessary
transformed_df = transformed_df.dropDuplicates(['indicator', 'observation_date'])

# Configure Spark for dynamic partition overwrite
spark.conf.set("spark.sql.sources.partitionOverwriteMode", "dynamic")

# Write transformed data back to S3, partitioned by indicator/year/month
output_path = f"s3://{dest_bucket}/{dest_prefix}"

try:
    transformed_df.write.mode("overwrite") \
        .partitionBy("indicator", "observation_year", "observation_month") \
        .parquet(output_path)
    print(f"Data successfully transformed and saved to {output_path}")
except Exception as e:
    print(f"An error occurred during data write: {e}")

job.commit()
