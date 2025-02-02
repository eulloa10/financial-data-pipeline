from airflow import DAG
from airflow.providers.amazon.aws.operators.glue import GlueJobOperator
from airflow.operators.python import PythonOperator
from airflow.utils.dates import days_ago
from datetime import datetime, timedelta

default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'start_date': days_ago(1),
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=5)
}

def get_indicator(**context):
    return context['dag_run'].conf.get('indicator')

def get_start_year(**context):
    return context['dag_run'].conf.get('start_year', '2023')

def get_end_year(**context):
    return context['dag_run'].conf.get('end_year', '2024')

with DAG(
    'fred_single_indicator_etl',
    default_args=default_args,
    description='FRED Data ETL Pipeline for Single Indicator',
    schedule_interval=None,
    catchup=False
) as dag:

    def create_extract_task(indicator):
        return GlueJobOperator(
            task_id=f'extract',
            job_name='fred-fdp-extract-job',
            script_args={
                '--INDICATOR': indicator,
                '--OBSERVATION_START_DATE': '{{ dag_run.conf["start_year"] }}-01-01',
                '--OBSERVATION_END_DATE': '{{ dag_run.conf["end_year"] }}-12-31'
            },
            aws_conn_id='aws_default',
            region_name='us-west-1'
        )

    def create_transform_task(indicator):
        return GlueJobOperator(
            task_id=f'transform',
            job_name='fred-fdp-transform-job',
            script_args={
                '--INDICATOR': indicator,
                '--OBSERVATION_START_DATE': '{{ dag_run.conf["start_year"] }}-01-01',
                '--OBSERVATION_END_DATE': '{{ dag_run.conf["end_year"] }}-12-31'
            },
            aws_conn_id='aws_default',
            region_name='us-west-1'
        )

    def create_aggregate_task(indicator):
        return GlueJobOperator(
            task_id=f'aggregate',
            job_name='fred-fdp-aggregate-job',
            script_args={
                '--INDICATOR': indicator,
                '--START_YEAR': '{{ dag_run.conf["start_year"] }}',
                '--END_YEAR': '{{ dag_run.conf["end_year"] }}'
            },
            aws_conn_id='aws_default',
            region_name='us-west-1'
        )

    def create_load_task(indicator):
        return GlueJobOperator(
            task_id=f'load',
            job_name='fred-fdp-load-indicators-to-rds',
            script_args={
                '--INDICATOR': indicator,
                '--START_YEAR': '{{ dag_run.conf["start_year"] }}',
                '--END_YEAR': '{{ dag_run.conf["end_year"] }}'
            },
            aws_conn_id='aws_default',
            region_name='us-west-1'
        )

    # Create tasks with static task_ids
    extract_task = create_extract_task('{{ dag_run.conf["indicator"] }}')
    transform_task = create_transform_task('{{ dag_run.conf["indicator"] }}')
    aggregate_task = create_aggregate_task('{{ dag_run.conf["indicator"] }}')
    load_task = create_load_task('{{ dag_run.conf["indicator"] }}')

    extract_task >> transform_task >> aggregate_task >> load_task
