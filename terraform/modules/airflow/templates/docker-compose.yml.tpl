services:
  postgres:
    image: postgres:13
    environment:
      POSTGRES_USER: airflow
      POSTGRES_PASSWORD: ${airflow_db_password}
      POSTGRES_DB: airflow
    volumes:
      - postgres-db-volume:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD", "pg_isready", "-U", "airflow"]
      interval: 5s
      retries: 5

  redis:
    image: redis:latest
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 5s
      timeout: 30s
      retries: 50

  airflow-webserver:
    image: apache/airflow:2.7.1
    command: webserver
    ports:
      - "8080:8080"
    environment:
      - AIRFLOW__CORE__EXECUTOR=CeleryExecutor
      - AIRFLOW__CORE__SQL_ALCHEMY_CONN=postgresql+psycopg2://airflow:${airflow_db_password}@postgres/airflow
      - AIRFLOW__CELERY__RESULT_BACKEND=db+postgresql://airflow:${airflow_db_password}@postgres/airflow
      - AIRFLOW__CELERY__BROKER_URL=redis://:@redis:6379/0
      - AIRFLOW__CORE__FERNET_KEY=${fernet_key}
      - AIRFLOW__CORE__LOAD_EXAMPLES=False
      - AIRFLOW__WEBSERVER__SECRET_KEY=${webserver_secret_key}
      - AIRFLOW__CORE__DAGS_FOLDER=/opt/airflow/dags
      - AIRFLOW__CORE__REMOTE_LOGGING=True
      - AIRFLOW__CORE__REMOTE_BASE_LOG_FOLDER=s3://${dags_bucket}/logs
      - AIRFLOW__CORE__REMOTE_LOG_CONN_ID=aws_default
    volumes:
      - ./dags:/opt/airflow/dags
      - ./logs:/opt/airflow/logs
      - ./plugins:/opt/airflow/plugins
    depends_on:
      - postgres
      - redis

  airflow-scheduler:
    image: apache/airflow:2.7.1
    command: scheduler
    environment:
      - AIRFLOW__CORE__EXECUTOR=CeleryExecutor
      - AIRFLOW__CORE__SQL_ALCHEMY_CONN=postgresql+psycopg2://airflow:${airflow_db_password}@postgres/airflow
      - AIRFLOW__CELERY__RESULT_BACKEND=db+postgresql://airflow:${airflow_db_password}@postgres/airflow
      - AIRFLOW__CELERY__BROKER_URL=redis://:@redis:6379/0
      - AIRFLOW__CORE__FERNET_KEY=${fernet_key}
      - AIRFLOW__CORE__LOAD_EXAMPLES=False
      - AIRFLOW__CORE__DAGS_FOLDER=/opt/airflow/dags
      - AIRFLOW__CORE__REMOTE_LOGGING=True
      - AIRFLOW__CORE__REMOTE_BASE_LOG_FOLDER=s3://${dags_bucket}/logs
      - AIRFLOW__CORE__REMOTE_LOG_CONN_ID=aws_default
    volumes:
      - ./dags:/opt/airflow/dags
      - ./logs:/opt/airflow/logs
      - ./plugins:/opt/airflow/plugins
    depends_on:
      - postgres
      - redis

volumes:
  postgres-db-volume:
