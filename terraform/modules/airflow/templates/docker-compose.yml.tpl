services:
  postgres:
    image: postgres:13
    environment:
      POSTGRES_USER: airflow
      POSTGRES_PASSWORD: airflow
      POSTGRES_DB: airflow
    volumes:
      - postgres_data:/var/lib/postgresql/data

  webserver:
    image: apache/airflow:2.6.3
    restart: always
    user: "$${AIRFLOW_UID:-50000}:0"
    depends_on:
      - postgres
    environment:
      AIRFLOW__CORE__EXECUTOR: LocalExecutor
      AIRFLOW__CORE__SQL_ALCHEMY_CONN: postgresql+psycopg2://airflow:airflow@postgres/airflow
      AIRFLOW__CORE__LOAD_EXAMPLES: 'false'
      AIRFLOW__CORE__DAGS_FOLDER: /opt/airflow/dags
      AIRFLOW__WEBSERVER__WORKERS: 4
      AIRFLOW__CORE__REMOTE_LOGGING: 'false'
      AIRFLOW__CORE__DAG_DISCOVERY_SAFE_MODE: 'False'
      AIRFLOW_CONN_AWS_DEFAULT: "aws://?region_name=$${aws_region}"
    ports:
      - "8080:8080"
    volumes:
      - ./dags:/opt/airflow/dags
      - ./logs:/opt/airflow/logs
      - ./plugins:/opt/airflow/plugins
      - ./config:/opt/airflow/config
    command: webserver

  scheduler:
    image: apache/airflow:2.6.3
    restart: always
    user: "$${AIRFLOW_UID:-50000}:0"
    depends_on:
      - webserver
      - postgres
    environment:
      AIRFLOW__CORE__EXECUTOR: LocalExecutor
      AIRFLOW__CORE__SQL_ALCHEMY_CONN: postgresql+psycopg2://airflow:airflow@postgres/airflow
      AIRFLOW__CORE__LOAD_EXAMPLES: 'false'
      AIRFLOW__CORE__DAGS_FOLDER: /opt/airflow/dags
      AIRFLOW__CORE__REMOTE_LOGGING: 'false'
      AIRFLOW_CONN_AWS_DEFAULT: "aws://?region_name=$${aws_region}"
    volumes:
      - ./dags:/opt/airflow/dags
      - ./logs:/opt/airflow/logs
      - ./plugins:/opt/airflow/plugins
      - ./config:/opt/airflow/config
    command: scheduler

volumes:
  postgres_data:
