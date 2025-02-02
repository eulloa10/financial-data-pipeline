# dags/fred_etl_dag.py
from airflow import DAG
from airflow.providers.amazon.aws.operators.glue import GlueJobOperator
from airflow.utils.dates import days_ago
from datetime import datetime, timedelta

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

with DAG(
    'fred_all_indicators_etl',
    default_args=default_args,
    description='FRED Data ETL Pipeline',
    schedule_interval=None,  # Set to None so it only runs when triggered
    catchup=False,
    max_active_runs=2,
    max_active_tasks=5
) as dag:

    # Get start and end year from DAG run configuration
    START_YEAR = "{{ dag_run.conf['start_year'] }}"
    END_YEAR = "{{ dag_run.conf['end_year'] }}"
    START_DATE = f"{START_YEAR}-01-01"
    END_DATE = f"{END_YEAR}-12-31"

    # Create tasks for each indicator
    for indicator in INDICATORS:
        extract_task = GlueJobOperator(
            task_id=f'extract_{indicator}',
            job_name='fred-fdp-extract-job',
            script_args={
                '--INDICATOR': indicator,
                '--OBSERVATION_START_DATE': START_DATE,
                '--OBSERVATION_END_DATE': END_DATE
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
                '--OBSERVATION_START_DATE': START_DATE,
                '--OBSERVATION_END_DATE': END_DATE
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
                '--START_YEAR': START_YEAR,
                '--END_YEAR': END_YEAR
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
                '--START_YEAR': START_YEAR,
                '--END_YEAR': END_YEAR
            },
            aws_conn_id='aws_default',
            region_name='us-west-1',
            dag=dag
        )

        extract_task >> transform_task >> aggregate_task >> load_task
