import psycopg2
import logging
import json
import os
from dotenv import load_dotenv

def setup_logging():
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.INFO)
    handler = logging.StreamHandler()
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    if not logger.handlers:
        logger.addHandler(handler)
    return logger

logger = setup_logging()

def create_table(connection):
    try:
        with connection.cursor() as cursor:
            drop_table_sql = "DROP TABLE IF EXISTS indicator_metadata;"
            cursor.execute(drop_table_sql)

            create_table_sql = """
            CREATE TABLE IF NOT EXISTS indicator_metadata (
                series_id VARCHAR(255) PRIMARY KEY,
                full_name VARCHAR(255) NOT NULL,
                common_name VARCHAR(255) NOT NULL,
                data_release_frequency VARCHAR(255) NOT NULL,
                description TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            """
            cursor.execute(create_table_sql)
            connection.commit()
            logger.info("Table 'indicator_metadata' created successfully.")
    except Exception as e:
        logger.error(f"Error creating table: {str(e)}")
        connection.rollback()
        raise

def insert_data(connection, data):
    try:
        with connection.cursor() as cursor:
            insert_data_sql = """
            INSERT INTO indicator_metadata (full_name, common_name, series_id, description, data_release_frequency) VALUES (%s, %s, %s, %s, %s);
            """
            for item in data:
                cursor.execute(insert_data_sql, (item['full_name'], item['common_name'],item['series_id'],item['description'],item['data_release_frequency']))
            connection.commit()
            logger.info("Data inserted into 'indicator_metadata' table successfully.")
    except Exception as e:
        logger.error(f"Error inserting data: {str(e)}")
        connection.rollback()
        raise

def main():
    try:
        load_dotenv()
        with open('scripts/indicator_metadata.json', 'r') as f:
            data = json.load(f)

        rds_host = os.getenv('RDS_HOST')
        rds_user = os.getenv('RDS_USER')
        rds_password = os.getenv('RDS_PASSWORD')
        rds_port = os.getenv('RDS_PORT')
        rds_database = os.getenv('RDS_DATABASE')

        connection = psycopg2.connect(
            host=rds_host,
            user=rds_user,
            password=rds_password,
            port=rds_port,
            database=rds_database
        )
        create_table(connection)
        insert_data(connection, data)
        connection.close()
    except Exception as e:
        logger.error(f"Error connecting to the database: {str(e)}")
        raise

if __name__ == "__main__":
    main()
