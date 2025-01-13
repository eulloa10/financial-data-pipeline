variable "project" {
  description = "Project name"
  type        = string
}

variable "region" {
  description = "AWS Region"
  type        = string
}

variable "data_lake_name" {
  description = "S3 bucket for fred data lake"
  type        = string
}

variable "glue_scripts_bucket" {
  description = "S3 bucket for glue scripts"
  type        = string
}

variable "glue_version" {
  type    = string
  default = "4.0"
}

variable "number_of_workers" {
  type    = number
  default = 2
}

variable "worker_type" {
  description = "The type of worker to use"
  type        = string
  default     = "G.1X"
}

variable "python_version" {
  description = "Python version"
  type        = number
  default     = 3
}

variable "timeout" {
  description = "Timeout for glue job"
  type        = number
  default     = 20
}

variable "fred_api_key" {
  description = "API key"
  type        = string
  sensitive   = true
}

variable "vpc_id" {
  description = "ID of the VPC"
  type        = string
}

variable  "environment" {
  description = "Environment name"
  type        = string
}

variable "security_group_id" {
  description = "ID of the security group for Glue jobs"
  type        = string
}
