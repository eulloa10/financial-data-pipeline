import sys
import logging
import traceback
from datetime import datetime
import boto3
import psycopg2
from awsglue.utils import getResolvedOptions
from pyspark.context import SparkContext
from awsglue.context import GlueContext
from awsglue.job import Job
import pyspark.sql.functions as F

def setup_logging():
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.INFO)
    handler = logging.StreamHandler(sys.stdout)
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    if not logger.handlers:
        logger.addHandler(handler)
    return logger

logger = setup_logging()

try:
    # Initialize Spark and Glue contexts
    logger.info("Initializing Spark and Glue contexts")
    sc = SparkContext()
    glueContext = GlueContext(sc)
    spark = glueContext.spark_session

    # Get required parameters
    args = getResolvedOptions(sys.argv, [
        'JOB_NAME',
        'SRC_BUCKET',
        'SRC_PREFIX',
        'START_YEAR',
        'START_MONTH',
        'DB_HOST',
        'DB_NAME',
        'DB_USER',
        'DB_PASSWORD',
        'DB_PORT',
        'TABLE_NAME'
    ])

    job = Job(glueContext)
    job.init(args['JOB_NAME'], args)

    # Handle optional parameters with defaults
    src_bucket = args['SRC_BUCKET']
    src_prefix = args['SRC_PREFIX']
    start_year = int(args['START_YEAR'])
    start_month = int(args['START_MONTH'])
    db_name = args['DB_NAME']
    table_name = args['TABLE_NAME']

    # Get optional parameters from job arguments
    try:
        end_year = int(args.get('END_YEAR', start_year))
        end_month = int(args.get('END_MONTH', start_month))
        specific_indicator = args.get('INDICATOR')
    except:
        end_year = start_year
        end_month = start_month
        specific_indicator = None

    logger.info(f"Job parameters loaded successfully for period: {start_year}/{start_month} to {end_year}/{end_month}")

except Exception as e:
    logger.error(f"Initialization failed: {str(e)}")
    logger.error(traceback.format_exc())
    sys.exit(1)

def generate_year_month_combinations(start_year, start_month, end_year, end_month):
    """
    Generate all year/month combinations in the range
    """
    combinations = []
    current_year = start_year
    current_month = start_month

    while (current_year < end_year) or (current_year == end_year and current_month <= end_month):
        combinations.append((current_year, current_month))
        current_month += 1
        if current_month > 12:
            current_month = 1
            current_year += 1

    return combinations

def get_indicator_list_from_s3(bucket, prefix, specific_indicator=None):
    """
    Fetches list of indicators from S3, optionally filtering for a specific one
    """
    if specific_indicator:
        return [specific_indicator]

    logger.info(f"Fetching indicator list from s3://{bucket}/{prefix}")
    indicators = []
    try:
        s3 = boto3.client('s3')
        paginator = s3.get_paginator('list_objects_v2')

        prefix = f"{prefix}/indicator="
        pages = paginator.paginate(Bucket=bucket, Prefix=prefix, Delimiter='/')

        for page in pages:
            if 'CommonPrefixes' in page:
                for prefix_obj in page['CommonPrefixes']:
                    indicator = prefix_obj['Prefix'].split('=')[-1].rstrip('/')
                    indicators.append(indicator)
                    logger.debug(f"Found indicator: {indicator}")

        logger.info(f"Found {len(indicators)} indicators")
        return indicators

    except Exception as e:
        logger.error(f"Error fetching indicator list: {str(e)}")
        raise

def create_table_if_not_exists(connection, table_name):
    """
    Creates the table if it doesn't exist
    """
    try:
        logger.info(f"Checking/Creating table {table_name}")
        with connection.cursor() as cursor:
            create_table_sql = f"""
            CREATE TABLE IF NOT EXISTS {table_name} (
                indicator VARCHAR(50),
                observation_year INTEGER,
                observation_month INTEGER,
                observation_value NUMERIC(20,2),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (indicator, observation_year, observation_month)
            )
            """
            cursor.execute(create_table_sql)
            connection.commit()
            logger.info(f"Table {table_name} is ready")

    except Exception as e:
        logger.error(f"Failed to create/check table: {str(e)}")
        raise

def read_indicator_data(indicator, year, month):
    """
    Reads indicator data from S3 for specific month
    """
    try:
        input_path = f"s3://{src_bucket}/{src_prefix}/indicator={indicator}/observation_year={year}"
        logger.debug(f"Reading data from: {input_path}")

        df = spark.read.parquet(input_path)
        # Filter for specific month
        df = df.filter(F.col("observation_month") == month)
        return df

    except Exception as e:
        logger.error(f"Error reading data for indicator {indicator}, year {year}, month {month}: {str(e)}")
        return None

def load_data_to_rds(connection, df, table_name, indicator, year):
    """
    Loads data into RDS using PySpark DataFrame
    """
    try:
        rows = df.collect()

        upsert_sql = f"""
        INSERT INTO {table_name}
        (indicator, observation_year, observation_month, observation_value)
        VALUES (%s, %s, %s, %s)
        ON CONFLICT (indicator, observation_year, observation_month)
        DO UPDATE SET
            observation_value = EXCLUDED.observation_value,
            created_at = CURRENT_TIMESTAMP
        """

        records_processed = 0
        with connection.cursor() as cursor:
            for row in rows:
                cursor.execute(
                    upsert_sql,
                    (
                        row['indicator'],
                        row['observation_year'],
                        row['observation_month'],
                        row['observation_value']
                    )
                )
                records_processed += cursor.rowcount

            connection.commit()
            logger.info(f"Successfully processed {records_processed} records for {indicator} {year}")

        return records_processed

    except Exception as e:
        logger.error(f"Error loading data to RDS: {str(e)}")
        connection.rollback()
        raise

try:
    # Establish database connection
    logger.info("Connecting to database")
    connection = psycopg2.connect(
        host=args['DB_HOST'].replace(':5432', ''),  # Remove port from host
        user=args['DB_USER'],
        password=args['DB_PASSWORD'],
        port=args['DB_PORT'],
        database=args['DB_NAME']
    )

    # Create table if it doesn't exist
    create_table_if_not_exists(connection, table_name)

    # Get date range
    date_combinations = generate_year_month_combinations(start_year, start_month, end_year, end_month)
    logger.info(f"Processing data for period: {start_year}/{start_month} to {end_year}/{end_month}")

    # Get indicators (filtered or all)
    indicator_list = get_indicator_list_from_s3(src_bucket, src_prefix, specific_indicator)

    if not indicator_list:
        raise ValueError("No indicators found in S3")

    logger.info(f"Processing {len(indicator_list)} indicators for {len(date_combinations)} time periods")

    # Track processing statistics
    successful_loads = 0
    failed_loads = 0
    total_records_processed = 0

    # Process each indicator
    for indicator in indicator_list:
        for year, month in date_combinations:
            try:
                logger.info(f"Processing indicator: {indicator} for {year}/{month}")

                # Read data from S3 for specific month
                df = read_indicator_data(indicator, year, month)

                if df is not None and df.count() > 0:
                    # Load data to RDS
                    records_processed = load_data_to_rds(connection, df, table_name, indicator, year)
                    total_records_processed += records_processed
                    successful_loads += 1
                else:
                    logger.warning(f"No data found for indicator {indicator}, year {year}, month {month}")
                    failed_loads += 1

            except Exception as e:
                failed_loads += 1
                logger.error(f"Failed to process indicator {indicator} for {year}/{month}: {str(e)}")
                continue

    # Log final statistics
    logger.info(f"Job completed. "
                f"Successfully loaded: {successful_loads}/{len(indicator_list) * len(date_combinations)} combinations. "
                f"Failed: {failed_loads}/{len(indicator_list) * len(date_combinations)}. "
                f"Total records processed: {total_records_processed}")

    connection.close()
    job.commit()

except Exception as e:
    logger.error(f"Job failed: {str(e)}")
    logger.error(traceback.format_exc())
    if 'connection' in locals():
        connection.close()
    sys.exit(1)
