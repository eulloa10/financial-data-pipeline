import sys
import datetime
from datetime import date
import logging
import traceback
import pyspark.sql.functions as F
from pyspark.sql.types import DoubleType, IntegerType
from awsglue.utils import getResolvedOptions
from pyspark.context import SparkContext
from awsglue.context import GlueContext
from awsglue.job import Job
import boto3
from functools import reduce
from pyspark.sql import DataFrame

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
    # Spark and Glue context initialization
    logger.info("Initializing Spark and Glue context")
    sc = SparkContext()
    glueContext = GlueContext(sc)
    spark = glueContext.spark_session
    logger.info("Successfully initialized Spark and Glue context")

    # Job arguments
    required_args = [
        'JOB_NAME',
        'SRC_BUCKET',
        'SRC_PREFIX',
        'DEST_BUCKET',
        'DEST_PREFIX',
        'YEAR',
        'MONTH'
    ]

    logger.info("Reading job arguments")
    args = getResolvedOptions(sys.argv, required_args)

    # Validate all required arguments are present
    missing_args = [arg for arg in required_args if not args.get(arg)]
    if missing_args:
        raise ValueError(f"Missing required arguments: {', '.join(missing_args)}")

    job = Job(glueContext)
    job.init(args['JOB_NAME'], args)

    src_bucket = args['SRC_BUCKET']
    src_prefix = args['SRC_PREFIX']
    dest_bucket = args['DEST_BUCKET']
    dest_prefix = args['DEST_PREFIX']

    try:
        year = int(args['YEAR'])
        month = int(args['MONTH'])

        if not (1 <= month <= 12):
            raise ValueError(f"Invalid month: {month}. Month must be between 1 and 12")

        current_year = datetime.datetime.now().year
        if year > current_year + 1:  # Allow for next year's data
            raise ValueError(f"Year ({year}) cannot be more than one year in the future")

    except ValueError as e:
        logger.error(f"Invalid year or month format: {str(e)}")
        raise

    logger.info(f"Job parameters validated successfully: "
                f"src_bucket={src_bucket}, "
                f"src_prefix={src_prefix}, "
                f"dest_bucket={dest_bucket}, "
                f"dest_prefix={dest_prefix}, "
                f"year={year}, "
                f"month={month}")

except Exception as e:
    logger.error(f"Failed to initialize job: {str(e)}")
    logger.error(traceback.format_exc())
    sys.exit(1)

def get_indicator_list_from_s3(bucket, prefix):
    """
    Fetches a list of indicators from the given bucket and prefix in S3.
    """
    logger.info(f"Fetching indicator list from s3://{bucket}/{prefix}")
    indicators = []
    try:
        s3 = boto3.client('s3')
        paginator = s3.get_paginator('list_objects_v2')

        first_level_prefix = f"{prefix}/"
        second_level_pages = paginator.paginate(Bucket=bucket, Prefix=first_level_prefix, Delimiter='/')

        for page in second_level_pages:
            if 'CommonPrefixes' in page:
                for common_prefix in page['CommonPrefixes']:
                    prefix = common_prefix['Prefix']
                    if "indicator=" in prefix:
                        indicator = prefix.split("indicator=")[-1].rstrip('/')
                        indicators.append(indicator)
                        logger.debug(f"Found indicator: {indicator}")

        if not indicators:
            logger.warning("No indicators found in S3")
        else:
            logger.info(f"Found {len(indicators)} indicators")

        return indicators

    except Exception as e:
        logger.error(f"Error fetching indicator list: {str(e)}")
        logger.error(traceback.format_exc())
        raise

def determine_frequency(df):
    """
    Determines if an indicator has daily or monthly data.
    Returns 'daily' or 'monthly'.
    """
    try:
        row_count = df.count()
        # If more than one observation for the month, consider it daily data
        return 'daily' if row_count > 1 else 'monthly'

    except Exception as e:
        logger.error(f"Error determining data frequency: {str(e)}")
        logger.error(traceback.format_exc())
        raise

def process_monthly_data(indicator, year, month):
    """
    Processes data for a specific indicator, year, and month.
    """
    logger.info(f"Processing data for indicator {indicator}, year {year}, month {month}")

    try:
        # Read the monthly data
        input_path = f"s3://{src_bucket}/{src_prefix}/indicator={indicator}/observation_year={year}/observation_month={month}"
        logger.debug(f"Reading data from: {input_path}")

        df = spark.read.parquet(input_path)

        if df.count() == 0:
            logger.warning(f"No data found for indicator {indicator}, year {year}, month {month}")
            return None

        # Add year and month columns
        df = df.withColumn("observation_year", F.year("observation_date")) \
               .withColumn("observation_month", F.month("observation_date"))

        # Determine frequency
        frequency = determine_frequency(df)
        logger.info(f"Indicator {indicator} for {year}-{month} has {frequency} frequency")

        if frequency == 'daily':
            logger.debug(f"Aggregating daily data to monthly for {indicator}, {year}-{month}")
            # For daily data, calculate monthly average
            monthly_data = df.groupBy("observation_year", "observation_month") \
                .agg(F.avg("observation_value").alias("observation_value"))
        else:
            logger.debug(f"Keeping monthly data as is for {indicator}, {year}-{month}")
            # For monthly data, keep as is
            monthly_data = df.select("observation_year", "observation_month", "observation_value")

        # Add indicator column and round values
        monthly_data = monthly_data \
            .withColumn("indicator", F.lit(indicator)) \
            .withColumn("observation_value", F.round("observation_value", 2))

        return monthly_data

    except Exception as e:
        logger.error(f"Error processing data for indicator {indicator}, year {year}, month {month}: {str(e)}")
        logger.error(traceback.format_exc())
        return None

def update_yearly_aggregation(new_monthly_data, indicator, year):
    """
    Updates the existing yearly aggregation with new monthly data.
    Preserves existing months and adds/updates only the specified month.
    """
    if new_monthly_data is None:
        logger.warning(f"No new monthly data to update for indicator {indicator}, year {year}")
        return

    try:
        # Get the month we're adding/updating
        new_month = new_monthly_data.first()["observation_month"]
        logger.info(f"Preparing to add/update month {new_month} for indicator {indicator}, year {year}")

        # Try to read existing yearly data
        existing_data_path = f"s3://{dest_bucket}/{dest_prefix}/indicator={indicator}/observation_year={year}"
        try:
            existing_data = spark.read.parquet(existing_data_path)
            existing_count = existing_data.count()
            logger.info(f"Found existing aggregated data for indicator {indicator}, year {year} with {existing_count} months")

            # Check if the month already exists
            existing_months = [row.observation_month for row in existing_data.select('observation_month').distinct().collect()]
            logger.info(f"Existing months for indicator {indicator}, year {year}: {sorted(existing_months)}")

            if new_month in existing_months:
                logger.info(f"Month {new_month} already exists, will update it")
                # Remove the month we're updating from existing data
                existing_data = existing_data.filter(F.col("observation_month") != new_month)
            else:
                logger.info(f"Month {new_month} is new, will add it")

        except Exception as e:
            logger.info(f"No existing aggregated data found for indicator {indicator}, year {year}")
            existing_data = None

        # Combine existing data with new monthly data
        if existing_data is not None and existing_data.count() > 0:
            logger.info(f"Combining existing data with new data for month {new_month}")
            final_df = existing_data.union(new_monthly_data)
            final_count = final_df.count()
            logger.info(f"Combined data now has {final_count} months")
        else:
            logger.info(f"No existing data, creating new file with month {new_month}")
            final_df = new_monthly_data

        # Verify the data before writing
        final_months = [row.observation_month for row in final_df.select('observation_month').distinct().collect()]
        logger.info(f"Final months for indicator {indicator}, year {year}: {sorted(final_months)}")

        # Additional verification
        if existing_data is not None:
            expected_month_count = len(existing_months) if new_month in existing_months else len(existing_months) + 1
            actual_month_count = len(final_months)
            if actual_month_count != expected_month_count:
                raise ValueError(f"Expected {expected_month_count} months but got {actual_month_count} months after combining data")

        # Order the data and write it back
        final_df = final_df.select(
            "indicator",
            "observation_year",
            "observation_month",
            "observation_value"
        ).orderBy("observation_month")

        # Write with additional verification
        logger.info(f"Writing updated data with {len(final_months)} months to {existing_data_path}")
        final_df.write.mode("overwrite").parquet(existing_data_path)

        # Verify the write was successful
        verification_df = spark.read.parquet(existing_data_path)
        verification_months = [row.observation_month for row in verification_df.select('observation_month').distinct().collect()]
        logger.info(f"Verified written data has months: {sorted(verification_months)}")

        if sorted(verification_months) != sorted(final_months):
            raise ValueError(f"Data verification failed. Written data does not match expected months.")

        logger.info(f"Successfully updated aggregated data for indicator {indicator}, year {year}")

    except Exception as e:
        logger.error(f"Error updating yearly aggregation for indicator {indicator}, year {year}: {str(e)}")
        logger.error(traceback.format_exc())
        raise

try:
    # Get list of indicators
    indicator_list = get_indicator_list_from_s3(src_bucket, src_prefix)

    if not indicator_list:
        raise ValueError("No indicators found in S3. Exiting.")

    logger.info(f"Processing {len(indicator_list)} indicators for {year}-{month}")

    # Track processing statistics
    successful_processes = 0
    failed_processes = 0
    total_processes = len(indicator_list)

    # Process each indicator for the specified month/year
    for indicator in indicator_list:
        try:
            logger.info(f"Processing indicator: {indicator}")

            # Process the monthly data
            monthly_data = process_monthly_data(indicator, year, month)

            # Update the yearly aggregation
            if monthly_data is not None:
                update_yearly_aggregation(monthly_data, indicator, year)
                successful_processes += 1
            else:
                failed_processes += 1
                logger.warning(f"No data processed for indicator {indicator}, {year}-{month}")

        except Exception as e:
            failed_processes += 1
            logger.error(f"Failed to process indicator {indicator}: {str(e)}")
            logger.error(traceback.format_exc())
            continue

    # Log final statistics
    logger.info(f"Job completed. "
                f"Successfully processed: {successful_processes}/{total_processes} "
                f"Failed: {failed_processes}/{total_processes}")

    job.commit()

except Exception as e:
    logger.error(f"Job failed: {str(e)}")
    logger.error(traceback.format_exc())
    sys.exit(1)
