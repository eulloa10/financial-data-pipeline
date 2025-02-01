# dags/weekly_dynamic_dag.py
from airflow import DAG
from airflow.providers.amazon.aws.operators.glue import GlueJobOperator
from airflow.utils.dates import days_ago
from datetime import datetime, timedelta
import calendar

INDICATORS = [
    'DGS10',
    'EFFR',
    'CSUSHPINSA',
    'UNRATE',
    'CPIAUCSL',
    'PCE',
    'JTSJOL',
    'JTSHIR',
    'JTSTSR',
    'PSAVERT',
    'CSCICP03USM665S'
]

default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'start_date': days_ago(1),
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=5)
}

def get_current_month_range():
    """Calculate the date range for the current month"""
    today = datetime.now()
    year = today.year
    month = today.month

    # Get the last day of the current month
    _, last_day = calendar.monthrange(year, month)

    # Format dates as strings
    start_date = f"{year}-{month:02d}-01"
    end_date = f"{year}-{month:02d}-{last_day}"

    return start_date, end_date, str(year), str(month)

with DAG(
    'fred_weekly_etl',
    default_args=default_args,
    description='FRED Data Weekly ETL Pipeline',
    schedule_interval='30 0 * * 4',  # 4:30 PM PST Wednesday = 00:30 UTC Thursday
    catchup=False,
    tags=['fred', 'etl', 'weekly']
) as dag:

    start_date, end_date, year, month = get_current_month_range()

    for indicator in INDICATORS:
        extract_task = GlueJobOperator(
            task_id=f'extract_{indicator}',
            job_name='fred-fdp-extract-job',
            script_args={
                '--INDICATOR': indicator,
                '--OBSERVATION_START_DATE': start_date,
                '--OBSERVATION_END_DATE': end_date
            },
            aws_conn_id='aws_default',
            region_name='us-west-1',
            dag=dag
        )

        transform_task = GlueJobOperator(
            task_id=f'transform_{indicator}',
            job_name='fred-fdp-transform-job',
            script_args={
                '--INDICATOR': indicator,
                '--START_YEAR': year,
                '--END_YEAR': year
            },
            aws_conn_id='aws_default',
            region_name='us-west-1',
            dag=dag
        )

        aggregate_task = GlueJobOperator(
            task_id=f'aggregate_{indicator}',
            job_name='fred-fdp-aggregate-job',
            script_args={
                '--INDICATOR': indicator,
                '--START_YEAR': year,
                '--END_YEAR': year
            },
            aws_conn_id='aws_default',
            region_name='us-west-1',
            dag=dag
        )

        load_task = GlueJobOperator(
            task_id=f'load_{indicator}',
            job_name='fred-fdp-load-indicators-to-rds',
            script_args={
                '--INDICATOR': indicator,
                '--START_YEAR': year,
                '--END_YEAR': year
            },
            aws_conn_id='aws_default',
            region_name='us-west-1',
            dag=dag
        )

        # Add logging for date range
        print(f"Processing {indicator} for period: {start_date} to {end_date}")

        extract_task >> transform_task >> aggregate_task >> load_task
