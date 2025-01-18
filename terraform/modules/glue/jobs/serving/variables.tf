variable "project" {
  description = "The project name"
  type        = string
}

variable "glue_scripts_bucket" {
  description = "The S3 bucket where the Glue scripts are stored"
  type        = string
}

variable "python_version" {
  description = "The Python version to use for the Glue job"
  type        = string
}

variable "data_lake_name" {
  description = "The name of the data lake"
  type        = string
}

variable "db_host" {
  description = "The host of the RDS database"
  type        = string
}

variable "db_name" {
  description = "The name of the RDS database"
  type        = string
}

variable "db_username" {
  description = "The username to connect to the RDS database"
  type        = string
  sensitive   = true
}

variable "db_password" {
  description = "The password to connect to the RDS database"
  type        = string
  sensitive   = true
}

variable "glue_role_arn" {
  description = "The ARN of the IAM role to use for the Glue job"
  type        = string
}

variable "glue_assume_role_policy" {
  description = "The JSON policy document for the Glue assume role policy"
  type        = string
}

variable "glue_access_policy" {
  description = "The JSON policy document for the Glue access policy"
  type        = string
}

variable "glue_version" {
  type    = string
  default = "4.0"
}

variable "timeout" {
  description = "The timeout for the Glue job"
  type        = number
  default     = 20
}

variable "worker_type" {
  description = "The type of worker to use for the Glue job"
  type        = string
  default     = "G.1X"
}

variable "number_of_workers" {
  description = "The number of workers to use for the Glue job"
  type        = number
  default     = 2
}

variable "start_year" {
  description = "The start year for the data"
  type        = number
}

variable "start_month" {
  description = "The start month for the data"
  type        = number
}

variable "end_year" {
  description = "The end year for the data"
  type        = number
  default     = null
}

variable "end_month" {
  description = "The end month for the data"
  type        = number
  default     = null
}

variable "indicator" {
  description = "The indicator to load data for"
  type        = string
  default     = null
}

variable "vpc_id" {
  description = "VPC ID for Glue connection"
  type        = string
}

variable "private_subnet_id" {
  description = "Private subnet ID for Glue connection"
  type        = string
}

variable "private_subnet_az" {
  description = "Private subnet availability zone for Glue connection"
  type        = string
}

variable "glue_security_group_id" {
  description = "Security group ID for Glue jobs"
  type        = string
}
