variable "project" {
  description = "The project name"
  type        = string
}

variable "data_lake_name" {
  type        = string
  description = "Data lake bucket name"
}

variable "region" {
  type        = string
  description = "AWS region"

}

variable "glue_scripts_bucket" {
  description = "S3 bucket for glue scripts"
  type = string
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
  type = string
  default = "G.1X"
}

variable "python_version" {
  description = "Python version"
  type = number
  default = 3
}

variable "timeout" {
  description = "Timeout for glue job"
  type = number
  default = 5
}

variable "long_timeout" {
  description = "Timeout for glue job"
  type = number
  default = 30
}

variable "fred_api_key" {
  description = "API key for FRED"
  type = string
  sensitive = true
}

variable "scripts_bucket_id" {
  description = "ID of the scripts S3 bucket"
  type        = string
}

variable "glue_assume_role_policy" {
  description = "IAM assume role policy for Glue"
  type        = string
}

variable "glue_access_policy" {
  description = "IAM access policy for Glue"
  type        = string
}

variable "glue_role_arn" {
  description = "ARN of the Glue IAM role"
  type        = string
}
