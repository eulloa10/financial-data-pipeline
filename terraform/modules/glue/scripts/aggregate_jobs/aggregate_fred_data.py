import sys
from awsglue.transforms import *
from awsglue.context import GlueContext
from awsglue.job import Job
from awsglue.utils import getResolvedOptions
from pyspark.context import SparkContext
import logging
from pyspark.sql.functions import col, lit, round
from datetime import datetime

args = getResolvedOptions(sys.argv, ['JOB_NAME', 'SRC_BUCKET', 'SRC_PREFIX',
                                   'DEST_BUCKET', 'DEST_PREFIX', 'START_YEAR',
                                   'END_YEAR', 'INDICATOR'])

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

src_bucket = args['SRC_BUCKET']
src_prefix = args['SRC_PREFIX']
dest_bucket = args['DEST_BUCKET']
dest_prefix = args['DEST_PREFIX']
start_year = int(args['START_YEAR'])
end_year = int(args['END_YEAR'])
indicator = args['INDICATOR']

def aggregate_year(year):
    """Aggregate all monthly files for a given year into a single file"""
    try:
        source_path = f"s3://{src_bucket}/{src_prefix}/indicator={indicator}/year={year}/month=*"

        logger.info(f"Reading monthly files for year {year} from: {source_path}")

        df = spark.read.parquet(source_path)

        if df.rdd.isEmpty():
            logger.warning(f"No data found for year {year}")
            return

        month_count = df.select("observation_month").distinct().count()
        logger.info(f"Found data for {month_count} months in year {year}")

        df_with_metadata = df.withColumn(
            "value",
            round(col("value"), 2)
        ).withColumn(
            "aggregation_timestamp",
            lit(datetime.now().isoformat())
        )

        dest_path = f"s3://{dest_bucket}/{dest_prefix}/indicator={indicator}/year={year}"

        logger.info(f"Writing aggregated data for year {year} to: {dest_path}")

        df_with_metadata.coalesce(1).write.mode("overwrite")\
            .option("compression", "snappy")\
            .parquet(dest_path)

        logger.info(f"Successfully aggregated data for year {year}")

    except Exception as e:
        logger.error(f"Error processing year {year}: {e}")
        raise

def process_all_years():
    """Process all years in the specified range"""
    logger.info(f"Processing years {start_year} to {end_year} for indicator {indicator}")

    for year in range(start_year, end_year + 1):
        logger.info(f"Processing year {year}")
        aggregate_year(year)

try:
    process_all_years()
    logger.info("All years processed successfully")

except Exception as e:
    logger.error(f"Job failed: {e}")
    raise

job.commit()
