# Financial and Economic Indicators Tracking and Analysis

## Background

Tracking and analyzing key financial and economic indicators is essential for informed investment decisions, but manually collecting, processing, and analyzing this data is time-consuming, error-prone, and inefficient. While FRED provides individual indicator visualizations, it lacks an integrated view of multiple indicators, limiting the ability to analyze trends and relationships. This project addresses these challenges by automating the extraction of financial and economic data from the FRED API, transforming it for analysis, and visualizing it through an intuitive dashboard, providing investors with a comprehensive, timely, and accurate view of key financial trends to inform better investment decisions.

### Key Financial and Economic Indicators Tracked:
- Case-Shiller Index
- Consumer Confidence
- CPI
- Federal Funds Rate
- JOLTS Hires (Nonfarm)
- JOLTS Openings (Nonfarm)
- JOLTS Turnover (Nonfarm)
- Personal Consumption Expenditures
- Personal Saving Rate
- Unemployment Rate
- Yield Curve

---

## Project Overview

This project builds an automated data pipeline to track financial and economic indicators over time. The data is ingested from the FRED API, stored in an S3-based data lake, and then transformed across multiple layers (bronze, silver, gold). Finally, the transformed data is moved to a data warehouse for analysis and reporting. The project culminates in an interactive dashboard that visualizes key metrics, helping investors monitor trends and make data-driven investment decisions.

The core components of the project include:
- **Data Ingestion**: Fetching data from external APIs (FRED) and storing it in Amazon S3.
- **Data Transformation**: Using AWS Glue scripts to clean and prepare the data across the various layers of the data lake.
- **Data Warehouse**: Storing the transformed data in Amazon RDS for further analysis and reporting.
- **Dashboard**: Visualizing the financial indicators using Apache Superset, Tableau, or Power BI.
- **Automation**: Orchestrating the workflow with Apache Airflow to manage the data pipeline and ensure regular updates.
- **Infrastructure as Code**: Using Terraform to automate the provisioning and management of AWS resources, including S3 buckets, Glue jobs, and RDS instances

---

## Technologies Used

- **Cloud**: Amazon Web Services (AWS)
  - **S3**: Data storage (Data Lake)
  - **RDS**: Data warehouse
  - **Glue**: Data transformation
  - **Lambda**: Serverless compute (optional)
  - **SES**: Sending reports via email (optional)
- **Orchestration**: Apache Airflow for workflow automation and scheduling
- **Data Transformation**: AWS Glue
- **Dashboard**: Apache Superset for data visualization
- **Infrastructure as Code**: Terraform for provisioning cloud resources

---

## Architecture

![Architecture Diagram](https://github.com/eulloa10/financial-data-pipeline/blob/main/fred_fdp_architecture_diagram.png?raw=true)

---

## Setup and Installation

### Prerequisites

To run this project, you need the following:

- **Terraform** installed on your machine for provisioning cloud resources.
- **AWS CLI** configured with your AWS credentials.
- **Python** (for Apache Airflow and custom transformations).
- **Apache Airflow** setup for orchestrating the workflow.
- **Docker** (for containerization).

### Steps to Set Up

1. **Clone the repository**:

    ```bash
    git clone https://github.com/your-username/financial-indicators-pipeline.git
    cd financial-indicators-pipeline
    ```

2. **Terraform Setup**:

    Ensure you have Terraform installed, then initialize the Terraform configuration to provision the required AWS resources.

    ```bash
    terraform init
    terraform apply
    ```

3. **Airflow Setup**:

    - Install Apache Airflow:

      ```bash
      pip install apache-airflow
      ```

    - Start the Airflow web server and scheduler:

      ```bash
      airflow webserver --port 8080
      airflow scheduler
      ```

4. **Running the Data Pipeline**:

    The pipeline is orchestrated via Airflow. You can trigger the DAGs to fetch data, transform it, and load it into the data warehouse.

    - Check the Airflow web UI at `http://localhost:8080` for task statuses.
    - The DAGs are defined in the `airflow/dags` directory.

5. **Data Transformation**:

    Custom transformation scripts (e.g., using AWS Glue or DBT) will clean and format the data. Refer to the `transformations` directory for transformation logic.

6. **Dashboard Setup**:

    - Install Apache Superset or configure Tableau/Power BI to connect to your data warehouse (Redshift or RDS).
    - Follow the instructions in the `dashboard` directory to configure your visualizations.

---

## Usage

Once the project is set up, you can perform the following tasks:

- **Monitor the Pipeline**: Use Airflow to trigger and monitor the ETL pipeline and data transformations.
- **View Dashboards**: Access the dashboard tool to view trends for various financial indicators over time.
- **Generate Reports**: Configure Airflow to run monthly reports and send them via email using AWS SES.

---
