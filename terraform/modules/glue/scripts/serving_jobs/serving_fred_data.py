import sys
import logging
import traceback
from datetime import datetime
import boto3
import psycopg2
import pandas as pd
from awsglue.utils import getResolvedOptions
from pyspark.context import SparkContext
from awsglue.context import GlueContext
from awsglue.job import Job
from pyspark.sql import SparkSession
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

    # Get job parameters
    args = getResolvedOptions(sys.argv, [
        'JOB_NAME',
        'SRC_BUCKET',
        'SRC_PREFIX',
        'YEAR',
        'DB_SECRET_NAME',
        'DB_NAME',
        'TABLE_NAME'
    ])

    job = Job(glueContext)
    job.init(args['JOB_NAME'], args)

    src_bucket = args['SRC_BUCKET']
    src_prefix = args['SRC_PREFIX']
    year = int(args['YEAR'])
    db_secret_name = args['DB_SECRET_NAME']
    db_name = args['DB_NAME']
    table_name = args['TABLE_NAME']

    logger.info(f"Job parameters loaded successfully")

except Exception as e:
    logger.error(f"Failed to initialize job: {str(e)}")
    logger.error(traceback.format_exc())
    sys.exit(1)

def get_db_credentials():
    """
    Retrieve database credentials from AWS Secrets Manager
    """
    try:
        logger.info("Retrieving database credentials from Secrets Manager")
        session = boto3.session.Session()
        client = session.client(
            service_name='secretsmanager'
        )

        secret_value = client.get_secret_value(SecretId=db_secret_name)
        secret = eval(secret_value['SecretString'])

        return {
            'host': secret['host'],
            'user': secret['username'],
            'password': secret['password'],
            'port': secret['port']
        }

    except Exception as e:
        logger.error(f"Failed to retrieve database credentials: {str(e)}")
        raise

def get_indicator_list_from_s3(bucket, prefix):
    """
    Fetches list of indicators from S3
    """
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

def read_indicator_data(indicator, year):
    """
    Reads indicator data from S3
    """
    try:
        input_path = f"s3://{src_bucket}/{src_prefix}/indicator={indicator}/observation_year={year}"
        logger.debug(f"Reading data from: {input_path}")

        df = spark.read.parquet(input_path)
        return df

    except Exception as e:
        logger.error(f"Error reading data for indicator {indicator}, year {year}: {str(e)}")
        return None

def check_existing_records(connection, table_name, indicator, year):
    """
    Checks which months already exist in the database for a given indicator and year
    """
    try:
        with connection.cursor() as cursor:
            sql = f"""
            SELECT observation_month
            FROM {table_name}
            WHERE indicator = %s AND observation_year = %s
            """
            cursor.execute(sql, (indicator, year))
            existing_months = [row[0] for row in cursor.fetchall()]
            logger.info(f"Found existing months for {indicator} {year}: {existing_months}")
            return existing_months
    except Exception as e:
        logger.error(f"Error checking existing records: {str(e)}")
        raise

def load_data_to_rds(connection, df, table_name, indicator, year):
    """
    Loads only new data into RDS
    """
    try:
        # Convert Spark DataFrame to Pandas
        pandas_df = df.toPandas()

        # Get existing months
        existing_months = check_existing_records(connection, table_name, indicator, year)

        # Filter out existing records
        new_records = pandas_df[~pandas_df['observation_month'].isin(existing_months)]

        if new_records.empty:
            logger.info(f"No new records to insert for {indicator} {year}")
            return 0

        # Prepare the SQL statement for insert only
        insert_sql = f"""
        INSERT INTO {table_name}
        (indicator, observation_year, observation_month, observation_value)
        VALUES (%s, %s, %s, %s)
        ON CONFLICT (indicator, observation_year, observation_month) DO NOTHING
        """

        # Insert new data
        records_inserted = 0
        with connection.cursor() as cursor:
            for _, row in new_records.iterrows():
                cursor.execute(
                    insert_sql,
                    (
                        row['indicator'],
                        row['observation_year'],
                        row['observation_month'],
                        row['observation_value']
                    )
                )
                records_inserted += cursor.rowcount

            connection.commit()
            logger.info(f"Successfully inserted {records_inserted} new records for {indicator} {year}")

        return records_inserted

    except Exception as e:
        logger.error(f"Error loading data to RDS: {str(e)}")
        connection.rollback()
        raise

try:
    # Get database credentials
    db_creds = get_db_credentials()

    # Establish database connection
    logger.info("Connecting to database")
    connection = psycopg2.connect(
        host=db_creds['host'],
        user=db_creds['user'],
        password=db_creds['password'],
        port=db_creds['port'],
        database=db_name
    )

    # Create table if it doesn't exist
    create_table_if_not_exists(connection, table_name)

    # Get list of indicators
    indicator_list = get_indicator_list_from_s3(src_bucket, src_prefix)

    if not indicator_list:
        raise ValueError("No indicators found in S3")

    logger.info(f"Processing {len(indicator_list)} indicators for year {year}")

    # Track processing statistics
    successful_loads = 0
    failed_loads = 0
    total_records_inserted = 0

    # Process each indicator
    for indicator in indicator_list:
        try:
            logger.info(f"Processing indicator: {indicator}")

            # Read data from S3
            df = read_indicator_data(indicator, year)

            if df is not None and df.count() > 0:
                # Load new data to RDS
                records_inserted = load_data_to_rds(connection, df, table_name, indicator, year)
                total_records_inserted += records_inserted
                successful_loads += 1
            else:
                logger.warning(f"No data found for indicator {indicator}, year {year}")
                failed_loads += 1

        except Exception as e:
            failed_loads += 1
            logger.error(f"Failed to process indicator {indicator}: {str(e)}")
            continue

    # Log final statistics
    logger.info(f"Job completed. "
                f"Successfully loaded: {successful_loads}/{len(indicator_list)} indicators. "
                f"Failed: {failed_loads}/{len(indicator_list)}. "
                f"Total new records inserted: {total_records_inserted}")

    connection.close()
    job.commit()

except Exception as e:
    logger.error(f"Job failed: {str(e)}")
    logger.error(traceback.format_exc())
    if 'connection' in locals():
        connection.close()
    sys.exit(1)
