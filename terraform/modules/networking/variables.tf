variable "project" {
  description = "Project name"
  type        = string
}

variable "environment" {
  description = "Environment (dev/prod)"
  type        = string
}

variable "vpc_cidr" {
  description = "VPC CIDR block"
  type        = string
  default     = "10.0.0.0/16"
}
