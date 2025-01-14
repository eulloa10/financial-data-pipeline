# terraform {
#   required_providers {
#     aws = {
#       source  = "hashicorp/aws"
#       version = "~> 5.0"
#     }
#   }
# }

# provider "aws" {
#   region = var.region

#   endpoints {
#     s3 = "s3.${var.region}.amazonaws.com"
#   }
# }
