import sys
import logging
import traceback
from datetime import datetime
from awsglue.utils import getResolvedOptions
from pyspark.context import SparkContext
from awsglue.context import GlueContext
from awsglue.job import Job
import pyspark.sql.functions as F

class Logger:
    @staticmethod
    def setup():
        logger = logging.getLogger(__name__)
        logger.setLevel(logging.INFO)
        handler = logging.StreamHandler(sys.stdout)
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        if not logger.handlers:
            logger.addHandler(handler)
        return logger

class SparkManager:
    def __init__(self, args, logger):
        self.args = args
        self.logger = logger
        self.sc = SparkContext()
        self.glueContext = GlueContext(self.sc)
        self.spark = self.glueContext.spark_session
        self.job = Job(self.glueContext)
        self.job.init(args['JOB_NAME'], args)

    def ensure_table_exists(self):
        """Ensure the target table exists with the correct schema"""
        create_table_sql = f"""
        CREATE TABLE IF NOT EXISTS {self.args['TABLE_NAME']} (
            indicator VARCHAR(255),
            observation_year INTEGER,
            observation_month INTEGER,
            value DECIMAL(10,2),
            observation_count INTEGER,
            aggregation_timestamp TIMESTAMP,
            load_timestamp TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (indicator, observation_year, observation_month)
        );

        CREATE INDEX IF NOT EXISTS idx_{self.args['TABLE_NAME']}_indicator
            ON {self.args['TABLE_NAME']}(indicator);
        CREATE INDEX IF NOT EXISTS idx_{self.args['TABLE_NAME']}_year_month
            ON {self.args['TABLE_NAME']}(observation_year, observation_month);
        """

        try:
            jvm = self.sc._jvm
            DriverManager = jvm.java.sql.DriverManager
            jdbc_url = f"jdbc:postgresql://{self.args['DB_HOST']}:{self.args['DB_PORT']}/{self.args['DB_NAME']}"
            conn = DriverManager.getConnection(jdbc_url, self.args['DB_USER'], self.args['DB_PASSWORD'])
            stmt = conn.createStatement()
            stmt.execute(create_table_sql)
            stmt.close()
            conn.close()
            self.logger.info("Table schema verified/created successfully")
        except Exception as e:
            self.logger.error(f"Error ensuring table exists: {str(e)}")
            raise

    def read_indicator_data(self, indicator, year):
        """Reads indicator data from S3"""
        try:
            input_path = f"s3://{self.args['SRC_BUCKET']}/{self.args['SRC_PREFIX']}/indicator={indicator}/year={year}"
            self.logger.debug(f"Reading data from: {input_path}")
            return self.spark.read.parquet(input_path)
        except Exception as e:
            self.logger.error(f"Error reading data for {indicator}, year {year}: {str(e)}")
            return None

    def write_to_postgres(self, df, table_name):
        """Write DataFrame to PostgreSQL using JDBC and perform upsert operation using Java JDBC."""
        if df is None or df.rdd.isEmpty():
            return 0

        try:
            self.logger.info("Starting write_to_postgres")

            db_host = self.args['DB_HOST'].split(':')[0]  # Remove port if present
            jdbc_url = f"jdbc:postgresql://{db_host}:{self.args['DB_PORT']}/{self.args['DB_NAME']}"

            # Write the DataFrame to a temporary table
            temp_table = f"{table_name}_temp"

            self.logger.info(f"Writing data to temporary table {temp_table}")
            df.write \
                .format("jdbc") \
                .option("url", jdbc_url) \
                .option("dbtable", temp_table) \
                .option("user", self.args['DB_USER']) \
                .option("password", self.args['DB_PASSWORD']) \
                .option("driver", "org.postgresql.Driver") \
                .mode("overwrite") \
                .save()

            # Use PySpark's ability to access Java JDBC to execute the upsert
            self.logger.info("Executing upsert operation using Java JDBC")
            jvm = self.sc._jvm
            DriverManager = jvm.java.sql.DriverManager
            conn = DriverManager.getConnection(jdbc_url, self.args['DB_USER'], self.args['DB_PASSWORD'])
            stmt = conn.createStatement()

            upsert_sql = f"""
            INSERT INTO {table_name} (
                indicator,
                observation_year,
                observation_month,
                value,
                observation_count,
                aggregation_timestamp,
                load_timestamp,
                created_at,
                updated_at
            )
            SELECT
                indicator,
                observation_year,
                observation_month,
                value,
                observation_count,
                aggregation_timestamp::timestamp,
                '{datetime.now().isoformat()}'::timestamp as load_timestamp,
                CURRENT_TIMESTAMP as created_at,
                CURRENT_TIMESTAMP as updated_at
            FROM {temp_table}
            ON CONFLICT (indicator, observation_year, observation_month)
            DO UPDATE SET
                value = EXCLUDED.value,
                observation_count = EXCLUDED.observation_count,
                aggregation_timestamp = EXCLUDED.aggregation_timestamp,
                load_timestamp = EXCLUDED.load_timestamp,
                updated_at = CURRENT_TIMESTAMP
            WHERE (
                {table_name}.value IS DISTINCT FROM EXCLUDED.value OR
                {table_name}.observation_count IS DISTINCT FROM EXCLUDED.observation_count OR
                {table_name}.aggregation_timestamp IS DISTINCT FROM EXCLUDED.aggregation_timestamp
            );
            DROP TABLE IF EXISTS {temp_table};
            """
            stmt.execute(upsert_sql)
            stmt.close()
            conn.close()

            self.logger.info("Successfully completed upsert operation")
            return df.count()

        except Exception as e:
            self.logger.error(f"Error writing to PostgreSQL: {str(e)}")
            self.logger.error(traceback.format_exc())
            raise

def get_year_range(start_year, end_year=None):
    """Generate list of years to process"""
    end_year = end_year or start_year
    return range(start_year, end_year + 1)

logger = Logger.setup()

try:
    # Get required parameters
    args = getResolvedOptions(sys.argv, [
        'JOB_NAME',
        'SRC_BUCKET',
        'SRC_PREFIX',
        'START_YEAR',
        'END_YEAR',
        'INDICATOR',
        'DB_HOST',
        'DB_NAME',
        'DB_USER',
        'DB_PASSWORD',
        'DB_PORT',
        'TABLE_NAME'
    ])

    # Initialize spark manager
    spark_manager = SparkManager(args, logger)

    # Ensure table exists with correct schema
    spark_manager.ensure_table_exists()

    # Get parameters
    start_year = int(args['START_YEAR'])
    end_year = int(args['END_YEAR'])
    indicator = args['INDICATOR']

    logger.info(f"Processing indicator {indicator} for years {start_year}-{end_year}")

    # Process data
    successful_loads = 0
    failed_loads = 0
    total_records = 0

    for year in get_year_range(start_year, end_year):
        try:
            logger.info(f"Processing {indicator} for {year}")
            df = spark_manager.read_indicator_data(indicator, year)

            if df is not None and df.count() > 0:
                records = spark_manager.write_to_postgres(df, args['TABLE_NAME'])
                total_records += records
                successful_loads += 1
                logger.info(f"Processed {records} records for {indicator} {year}")
            else:
                logger.warning(f"No data found for {indicator} {year}")
                failed_loads += 1

        except Exception as e:
            failed_loads += 1
            logger.error(f"Failed processing {indicator} {year}: {str(e)}")
            continue

    # Log results
    total_years = len(list(get_year_range(start_year, end_year)))
    logger.info(
        f"Job completed: "
        f"Successful: {successful_loads}/{total_years}, "
        f"Failed: {failed_loads}/{total_years}, "
        f"Total records: {total_records}"
    )

    spark_manager.job.commit()

except Exception as e:
    logger.error(f"Job failed: {str(e)}")
    logger.error(traceback.format_exc())
    sys.exit(1)
