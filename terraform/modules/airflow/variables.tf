variable "project" {
  description = "Project name"
  type        = string
}

variable "environment" {
  description = "Environment name"
  type        = string
}

variable "vpc_id" {
  description = "VPC ID where Airflow will be deployed"
  type        = string
}

variable "subnet_id" {
  description = "Subnet ID where Airflow EC2 will be deployed"
  type        = string
}

variable "allowed_ips" {
  description = "List of IP addresses allowed to access Airflow UI"
  type        = list(string)
}

variable "instance_type" {
  description = "EC2 instance type for Airflow"
  type        = string
  default     = "t3.small"
}

variable "key_name" {
  description = "Name of the SSH key pair to use for EC2 instance"
  type        = string
}

variable "region" {
  description = "AWS region"
  type        = string
}

variable "backup_bucket" {
  description = "S3 bucket for Airflow backups"
  type        = string
}

variable "cloudwatch_config_parameter" {
  description = "SSM parameter name for CloudWatch agent configuration"
  type        = string
  default     = "/airflow/cloudwatch-config"
}

variable "airflow_db_password" {
  description = "Password for Airflow's internal PostgreSQL database"
  type        = string
  sensitive   = true
}

variable "webserver_secret_key" {
  description = "Secret key for Airflow webserver"
  type        = string
  sensitive   = true
}

variable "fernet_key" {
  description = "Fernet key for Airflow"
  type        = string
  sensitive   = true
}

variable "tags" {
  description = "Additional tags for resources"
  type        = map(string)
  default     = {}
}
