# Automated Financial and Economic Indicator Dashboard using AWS and Preset

## Background

Investors need quick access to key financial indicators without sifting through an overwhelming amount of data. [FRED](https://fred.stlouisfed.org/) offers a wealth of financial data, but doesn't provide a way to easily view a customized set of indicators. This project automates the extraction of selected financial data from the FRED API, processes it for analysis, and delivers a dashboard and reports tailored to the investor’s specific interests.

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

**NOTE: This product uses the FRED® API but is not endorsed or certified by the Federal Reserve Bank of St. Louis.**

---

## Project Overview

This project builds an automated data pipeline to track financial and economic indicators over time. The data is ingested from the [FRED API](https://fred.stlouisfed.org/docs/api/fred/), stored in an S3-based data lake, and then transformed across multiple layers (bronze, silver, gold). Finally, the transformed data is stored in an RDS database for analysis and reporting.  An interactive Preset dashboard visualizes key economic indicators, helping investors track trends and make data-driven decisions.

The core components of the project include:
- **Data Ingestion**: Fetching data from external APIs (FRED) and storing it in Amazon S3
- **Data Transformation**: Using AWS Glue scripts to clean and prepare the data across the various layers of the data lake
- **Data Storage**: Storing the transformed data in Amazon RDS for further analysis and reporting
- **Dashboard**: Visualizing the financial indicators using Preset
- **Automation**: Managing the data pipeline and ensuring regular updates using Apache Airflow, running in a container on an EC2 instance
- **Infrastructure as Code**: Automating the provisioning and management of AWS resources (S3, Glue, RDS, EC2) using Terraform.

---

## Technologies Used

- **Cloud**: Amazon Web Services (AWS)
  - **S3**: Data lake storage for raw and processed financial data
  - **RDS(PostgreSQL)**: Relational database for storing transformed financial data, used for reporting and analysis
  - **Glue**: ETL (Extract, Transform, Load) processes for cleaning, transforming, and preparing financial data for analysis
  - **EC2**: Hosts the Apache Airflow container for workflow orchestration and data pipeline management
  - **Cloudwatch**: Monitors EC2 and RDS instances, along with tracking billing metrics
  - **SNS**: Sends email alerts regarding the status of AWS resources
- **Dashboard**: Apache Superset ([Preset](https://preset.io/)) for data visualization
- **Infrastructure as Code**: Terraform for provisioning cloud resources

---

## Architecture

![Architecture Diagram](https://github.com/eulloa10/financial-data-pipeline/blob/main/fred_fdp_architecture_diagram.png?raw=true)

---

## Setup and Installation

### Prerequisites

To run this project, you need the following:

- **AWS Credentials:** Ensure you have configured your AWS credentials (access key ID and secret access key) with appropriate permissions to create the necessary resources (S3, RDS, Glue, EC2, CloudWatch, SNS). You can set these up using environment variables, the [AWS CLI](https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html) configuration, or an IAM role.
- **Terraform:** Install Terraform on your local machine. See the [Terraform website](https://www.terraform.io/downloads) for installation instructions.
- **Preset Account:** Create an account on [Preset's website](https://preset.io/). You'll need this to visualize the data.

### Steps to Set Up

1. **Clone the repository**:

    ```bash
    git clone https://github.com/eulloa10/financial-indicators-pipeline.git
    cd financial-indicators-pipeline
    ```

2. **Environment variables and Terraform Variables**:

    - Copy the `.env.example` file to `.env`:
    ```bash
    cp .env.example .env
    ```
    - Edit the `.env` file and fill in the required environment variables. This file contains sensitive information such as API keys and database credentials.

    - Copy the `terraform.tfvars.example` file to `terraform.tfvars`:
    ```bash
    cp terraform.tfvars.example terraform.tfvars
    ```
    - Edit the `terraform.tfvars` file and fill in the required variables. This file will contain settings like your RDS password, database name, and other configuration parameters.

3. **Terraform Deployment**:

    Ensure you have Terraform installed, then initialize the Terraform configuration to provision the required AWS resources:

    ```bash
    cd terraform

    # Initialize Terraform to download the necessary providers and modules:
    terraform init

    # Apply the Terraform configuration to create the AWS infrastructure:
    terraform apply
    ```

    Terraform will output the URL of the Airflow web UI

4. **Run Airflow DAGs**:

    - Wait for EC2: After `terraform apply` completes, it takes a few minutes for the EC2 instance (hosting Airflow) to fully boot up and for the Airflow web UI to become accessible. Be patient

    - Access the Airflow web UI (the URL will be available after `terraform apply`).

    - Trigger the `fred_all_indicators_etl` DAG responsible for the ETL process for an entire year. This will start the ETL process and populate the RDS database with data for the year you have provided by passing the following *required* parameters:

      ```bash
      {
        "start_year": "desired_start_year_goes_here",
        "end_year": "desired_end_year_goes_here"
      }
      ```

5. **Preset Database Connection**:

    - Log in to your Preset account and follow Preset's instructions to connect to your RDS PostgreSQL database. You'll need the RDS endpoint, database name, username, and password (which you configured through Terraform). This step is crucial and must be done after the DAGs have successfully run and populated the database.

---

## Usage

Once the project is set up, you can perform the following tasks:

- **Monitor the Pipeline**: Use Airflow to trigger and monitor the ETL pipeline and data transformations
- **View Dashboards**: Access Preset to view trends for various financial indicators over time
- **Generate Reports**: Configure Preset to run monthly reports and send them via email

---
