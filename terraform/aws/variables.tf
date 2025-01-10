# variable "access_key" {
#   description = "AWS access key"
#   type = string
# }

# variable "secret_key" {
#   description = "AWS secret key"
#   type = string
# }
variable "project" {
  description = "Project name"
  type        = string
}

variable "region" {
  description = "AWS region"
  type        = string
}

variable "aws_user" {
  description = "AWS user name"
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

variable "terraform_bucket" {
  description = "Terraform state bucket"
  type        = string
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

# variable "transform_glue_scripts" {
#   type = map(object({
#     type     = string # "extract", "transform", "load"
#     filename = string
#   }))
#   default = {
#     extract_customer = {
#       type     = "extract"
#       filename = "extract_customer_data.py"
#     }
#     transform_customer = {
#       type     = "transform"
#       filename = "transform_customer_data.py"
#     }
#     transform_product = {
#       type = "transform"
#       filename = "transform_product_data.py"
#     }
#     load_customer = {
#         type = "load"
#         filename = "load_customer_data.py"
#     }
#   }
# }
