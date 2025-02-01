import sys
from awsglue.transforms import *
from awsglue.context import GlueContext
from awsglue.job import Job
from awsglue.utils import getResolvedOptions
from pyspark.context import SparkContext
import logging
from pyspark.sql.functions import col, avg, count, lit, when
from pyspark.sql.types import DoubleType
from datetime import datetime, date


args = getResolvedOptions(sys.argv, ['JOB_NAME', 'SRC_BUCKET','SRC_PREFIX',
            'DEST_BUCKET',
            'DEST_PREFIX', 'INDICATOR', 'OBSERVATION_START_DATE', 'OBSERVATION_END_DATE'])


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

source_bucket = args['SRC_BUCKET']
source_prefix = args['SRC_PREFIX']
dest_bucket = args['DEST_BUCKET']
dest_prefix = args['DEST_PREFIX']
indicator = args['INDICATOR']
start_date = datetime.strptime(args['OBSERVATION_START_DATE'], '%Y-%m-%d').date()
end_date = datetime.strptime(args['OBSERVATION_END_DATE'], '%Y-%m-%d').date()

source_path = f's3://{source_bucket}/{source_prefix}'
target_path = f's3://{dest_bucket}/{dest_prefix}'

def get_year_month_combinations(start_date, end_date):
    """Generate all year/month combinations between start_date and end_date"""
    combinations = []
    current_date = start_date
    while current_date <= end_date:
        combinations.append((current_date.year, current_date.month))
        # Move to the first day of the next month
        if current_date.month == 12:
            current_date = date(current_date.year + 1, 1, 1)
        else:
            current_date = date(current_date.year, current_date.month + 1, 1)
    return combinations

def process_data(input_path, output_path):
    """Process a single month's data"""
    try:
        try:
            logger.info(f"Reading data from: {input_path}")
            df = spark.read.json(input_path)
        except Exception as e:
            logger.warning(f"No data found or error reading from {input_path}: {e}")
            return

        if df.rdd.isEmpty():
            logger.warning(f"No data found in {input_path}")
            return

        df_cleaned = df.withColumn(
            "value",
            when(col("value") == ".", None)
            .otherwise(col("value").cast(DoubleType()))
        )

        df_cleaned = df_cleaned.filter(col("value").isNotNull())

        if df_cleaned.rdd.isEmpty():
            logger.warning(f"No valid data after cleaning in {input_path}")
            return

        df_aggregated = df_cleaned.groupBy(
            "indicator",
            "observation_year",
            "observation_month"
        ).agg(
            avg("value").alias("value"),
            count("value").alias("observation_count")
        )

        df_final = df_aggregated.withColumn(
            "processing_timestamp",
            lit(datetime.now().isoformat())
        )

        logger.info(f"Writing processed data to: {output_path}")
        df_final.coalesce(1).write.mode("overwrite")\
            .option("compression", "snappy")\
            .parquet(output_path)

        logger.info(f"Successfully processed data for {input_path}")

    except Exception as e:
        logger.error(f"Error processing data: {e}")
        logger.error(f"Skipping {input_path}")

def process_all_periods():
    """Process all periods within the date range"""
    year_month_combinations = get_year_month_combinations(start_date, end_date)

    logger.info(f"Processing data for indicator {indicator} from {start_date} to {end_date}")
    logger.info(f"Will process {len(year_month_combinations)} year/month combinations")

    for year, month in year_month_combinations:
        input_path = f"{source_path}/indicator={indicator}/year={year}/month={month}"
        output_path = f"{target_path}/indicator={indicator}/year={year}/month={month}"

        logger.info(f"Processing year={year}, month={month}")
        process_data(input_path, output_path)

try:
    process_all_periods()
    logger.info("All processing completed successfully")

except Exception as e:
    logger.error(f"Job failed: {e}")
    raise

job.commit()
