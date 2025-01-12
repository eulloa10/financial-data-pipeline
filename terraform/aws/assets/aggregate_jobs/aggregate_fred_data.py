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

# Enhanced logging setup
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
        'START_YEAR',
        'END_YEAR'
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
        start_year = int(args['START_YEAR'])
        end_year = int(args['END_YEAR'])

        if start_year > end_year:
            raise ValueError(f"START_YEAR ({start_year}) cannot be greater than END_YEAR ({end_year})")

        current_year = datetime.datetime.now().year
        if end_year > current_year + 1:  # Allow for next year's data
            raise ValueError(f"END_YEAR ({end_year}) cannot be more than one year in the future")

    except ValueError as e:
        logger.error(f"Invalid year format or range: {str(e)}")
        raise

    logger.info(f"Job parameters validated successfully: "
                f"src_bucket={src_bucket}, "
                f"src_prefix={src_prefix}, "
                f"dest_bucket={dest_bucket}, "
                f"dest_prefix={dest_prefix}, "
                f"year_range={start_year}-{end_year}")

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
            else:
                logger.warning(f"No CommonPrefixes found in page")

        if not indicators:
            logger.warning("No indicators found in S3")
        else:
            logger.info(f"Found {len(indicators)} indicators")

        return indicators

    except Exception as e:
        logger.error(f"Error fetching indicator list: {str(e)}")
        logger.error(traceback.format_exc())
        raise

def read_yearly_data(indicator, year):
    """
    Reads all monthly data for a given indicator and year.
    """
    logger.info(f"Reading data for indicator {indicator}, year {year}")
    monthly_dfs = []
    months_processed = 0
    months_with_data = 0

    for month in range(1, 13):
        input_path = f"s3://{src_bucket}/{src_prefix}/indicator={indicator}/observation_year={year}/observation_month={month}"
        try:
            logger.debug(f"Attempting to read: {input_path}")
            df = spark.read.parquet(input_path)
            months_processed += 1

            row_count = df.count()
            if row_count > 0:
                logger.debug(f"Found {row_count} rows for {indicator}, {year}-{month}")
                df_with_dates = df.withColumn("observation_year", F.year("observation_date")) \
                                .withColumn("observation_month", F.month("observation_date"))
                monthly_dfs.append(df_with_dates)
                months_with_data += 1
            else:
                logger.debug(f"No data found for {indicator}, {year}-{month}")
        except Exception as e:
            logger.debug(f"No data found for {indicator}, {year}-{month}: {str(e)}")
            continue

    logger.info(f"Processed {months_processed} months, found data in {months_with_data} months for {indicator}, {year}")

    if not monthly_dfs:
        logger.warning(f"No data found for indicator {indicator} in year {year}")
        return None

    try:
        # Union all monthly dataframes
        if len(monthly_dfs) == 1:
            logger.debug(f"Returning single month of data for {indicator}, {year}")
            return monthly_dfs[0]
        else:
            logger.debug(f"Combining {len(monthly_dfs)} months of data for {indicator}, {year}")
            return reduce(DataFrame.union, monthly_dfs)
    except Exception as e:
        logger.error(f"Error combining monthly data for {indicator}, {year}: {str(e)}")
        logger.error(traceback.format_exc())
        raise

def determine_frequency(df):
    """
    Determines if an indicator has daily or monthly data.
    Returns 'daily' or 'monthly'.
    """
    try:
        # Count observations per month
        monthly_counts = df.groupBy("observation_year", "observation_month") \
            .agg(F.count("*").alias("observations_per_month"))

        avg_observations = monthly_counts.select(F.avg("observations_per_month")).first()[0]

        frequency = 'daily' if avg_observations > 1.5 else 'monthly'
        logger.debug(f"Determined frequency: {frequency} (avg observations per month: {avg_observations:.2f})")
        return frequency

    except Exception as e:
        logger.error(f"Error determining data frequency: {str(e)}")
        logger.error(traceback.format_exc())
        raise

def process_indicator_data(indicator, year):
    """
    Processes data for a specific indicator and year.
    Returns monthly values (either original monthly data or aggregated daily data).
    """
    logger.info(f"Processing data for indicator {indicator}, year {year}")
    try:
        # Read all monthly data for the year
        df = read_yearly_data(indicator, year)

        if df is None:
            logger.warning(f"No data to process for indicator {indicator}, year {year}")
            return None

        # Determine frequency
        frequency = determine_frequency(df)
        logger.info(f"Indicator {indicator} for year {year} has {frequency} frequency")

        if frequency == 'daily':
            logger.debug(f"Aggregating daily data to monthly for {indicator}, {year}")
            # For daily data, calculate monthly averages
            monthly_data = df.groupBy("observation_year", "observation_month") \
                .agg(F.avg("observation_value").alias("observation_value"))
        else:
            logger.debug(f"Keeping monthly data as is for {indicator}, {year}")
            # For monthly data, keep as is
            monthly_data = df.select("observation_year", "observation_month", "observation_value")

        # Add indicator column and round values
        monthly_data = monthly_data \
            .withColumn("indicator", F.lit(indicator)) \
            .withColumn("observation_value", F.round("observation_value", 2))

        row_count = monthly_data.count()
        logger.info(f"Processed {row_count} months of data for {indicator}, {year}")

        # Return the data ordered by month (no null values included)
        return monthly_data.orderBy("observation_month")

    except Exception as e:
        logger.error(f"Error processing data for indicator {indicator}, year {year}: {str(e)}")
        logger.error(traceback.format_exc())
        return None

def write_yearly_data(df, indicator, year):
    """
    Writes the yearly data (containing all months) to the serving layer.
    """
    if df is not None and df.count() > 0:
        output_path = f"s3://{dest_bucket}/{dest_prefix}/indicator={indicator}/observation_year={year}"
        logger.info(f"Writing data to: {output_path}")

        try:
            # Select and order columns before writing
            final_df = df.select(
                "indicator",
                "observation_year",
                "observation_month",
                "observation_value"
            ).orderBy("observation_month")

            row_count = final_df.count()
            logger.info(f"Writing {row_count} rows for {indicator}, {year}")

            final_df.write.mode("overwrite").parquet(output_path)
            logger.info(f"Successfully wrote yearly data for indicator {indicator}, year {year}")

        except Exception as e:
            logger.error(f"Error writing data for indicator {indicator}, year {year}: {str(e)}")
            logger.error(traceback.format_exc())
            raise

try:
    # Get list of indicators
    indicator_list = get_indicator_list_from_s3(src_bucket, src_prefix)

    if not indicator_list:
        raise ValueError("No indicators found in S3. Exiting.")

    logger.info(f"Processing {len(indicator_list)} indicators for years {start_year} to {end_year}")

    # Track processing statistics
    successful_processes = 0
    failed_processes = 0
    total_processes = len(indicator_list) * (end_year - start_year + 1)

    # Process each indicator for each year
    for indicator in indicator_list:
        logger.info(f"Processing indicator: {indicator}")

        for year in range(start_year, end_year + 1):
            try:
                logger.info(f"Processing year: {year}")

                # Process the data
                yearly_data = process_indicator_data(indicator, year)

                # Write the results
                if yearly_data is not None:
                    write_yearly_data(yearly_data, indicator, year)
                    successful_processes += 1
                else:
                    failed_processes += 1
                    logger.warning(f"No data processed for indicator {indicator}, year {year}")

            except Exception as e:
                failed_processes += 1
                logger.error(f"Failed to process indicator {indicator} for year {year}: {str(e)}")
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
