variable "project" {
  description = "Project name"
  type        = string
}

variable "environment" {
  description = "Environment name"
  type        = string
}

variable "region" {
  description = "AWS region"
  type        = string
}

variable "airflow_instance_id" {
  description = "ID of the Airflow EC2 instance"
  type        = string
}

variable "rds_instance_id" {
  description = "ID of the RDS instance"
  type        = string
}

variable "alert_email" {
  description = "Email address for monitoring alerts"
  type        = string
}
