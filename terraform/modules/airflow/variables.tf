variable "name_prefix" {
  description = "Prefix for naming resources"
  type        = string
  default     = "dev"
}

variable "vpc_id" {
  description = "VPC ID where Airflow EC2 instance will be deployed"
  type        = string
}

variable "subnet_id" {
  description = "Subnet ID within the VPC for the EC2 instance"
  type        = string
}

variable "ami" {
  description = "AMI ID for the EC2 instance"
  type        = string
}

variable "instance_type" {
  description = "EC2 instance type"
  type        = string
}

variable "key_name" {
  description = "Name of the SSH key pair for EC2 access"
  type        = string
}

variable "airflow_admin_username" {
  description = "Airflow admin username"
  type        = string
  default     = "admin"
}

variable "airflow_admin_password" {
  description = "Airflow admin password"
  type        = string
  sensitive   = true
}

variable "airflow_admin_firstname" {
  description = "Airflow admin first name"
  type        = string
  default     = "Admin"
}

variable "airflow_admin_lastname" {
  description = "Airflow admin last name"
  type        = string
  default     = "User"
}

variable "airflow_admin_email" {
  description = "Airflow admin email"
  type        = string
}

variable "region" {
  description = "AWS region for Airflow configuration"
  type        = string
  default     = "us-west-1"
}

variable "ssh_ingress_cidr_blocks" {
  description = "CIDR blocks allowed to access SSH (port 22)"
  type        = list(string)
}

variable "airflow_ingress_cidr_blocks" {
  description = "CIDR blocks allowed to access Airflow web UI (port 8080)"
  type        = list(string)
}

variable "tags" {
  description = "Tags to apply to all resources"
  type        = map(string)
  default     = {}
}

variable "project" {
  description = "The name of the project"
  type        = string
}

variable "environment" {
  description = "The deployment environment (e.g., dev, staging, prod)"
  type        = string
}
