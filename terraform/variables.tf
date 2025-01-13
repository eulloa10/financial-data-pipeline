variable "project" {
  description = "Project name"
  type        = string
}

variable "region" {
  description = "AWS region"
  type        = string
  default     = "us-west-1"
}

variable "fred_api_key" {
  description = "API key"
  type        = string
  sensitive   = true
}

variable "environment" {
  description = "Environment (dev/prod)"
  type        = string
  default     = "dev"
}

variable "vpc_cidr" {
  description = "VPC CIDR block"
  type        = string
  default     = "10.0.0.0/16"
}

# Glue
variable "data_lake_name" {
  description = "S3 bucket for fred data lake"
  type        = string
}

variable "glue_scripts_bucket" {
  description = "S3 bucket for glue scripts"
  type        = string
}

variable "python_version" {
  description = "Python version"
  type        = number
  default     = 3
}

variable "worker_type" {
  description = "The type of worker to use"
  type        = string
  default     = "G.1X"
}

variable "timeout" {
  description = "Timeout for glue job"
  type        = number
  default     = 20
}

variable "glue_version" {
  type    = string
  default = "4.0"
}

variable "number_of_workers" {
  type    = number
  default = 2
}

# Airflow
variable "allowed_ips" {
  description = "List of IPs allowed to access Airflow UI"
  type        = list(string)
}

variable "key_name" {
  description = "SSH key name"
  type        = string
}

variable "airflow_instance_type" {
  description = "Airflow EC2 instance type"
  type        = string
}

variable "airflow_db_password" {
  description = "Password for Airflow's internal PostgreSQL database"
  type        = string
  sensitive   = true
}

variable "airflow_webserver_secret_key" {
  description = "Secret key for Airflow webserver"
  type        = string
  sensitive   = true
}

variable "airflow_fernet_key" {
  description = "Fernet key for Airflow"
  type        = string
  sensitive   = true
}

# RDS
variable "db_name" {
  description = "Database name"
  type        = string
  default     = "fred_db"
}

variable "db_instance_class" {
  description = "Database instance class"
  type        = string
  default     = "db.t3.micro"
}

variable "db_username" {
  description = "Database username"
  type        = string
  sensitive   = true
}

variable "db_password" {
  description = "Database password"
  type        = string
  sensitive   = true
}

# Monitoring
variable "alert_email" {
  description = "Email to send alerts to"
  type        = string
}
