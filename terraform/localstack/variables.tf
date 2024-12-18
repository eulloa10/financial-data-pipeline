variable "access_key" {
  description = "AWS access key"
  type = string
}

variable "secret_key" {
  description = "AWS secret key"
  type = string
}

variable "region" {
  description = "AWS region"
  type = string
}

variable "localstack_endpoint" {
  description = "LocalStack endpoint"
  type = string
}

variable "fred_data_bucket" {
  description = "S3 bucket for fred data"
  type = string
}

variable "glue_scripts_bucket" {
  description = "S3 bucket for glue scripts"
  type = string
}
