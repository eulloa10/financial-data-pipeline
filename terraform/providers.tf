terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }

  # backend "s3" {
  #   bucket = "terraform-state"
  #   key    = "fred-etl/terraform.tfstate"
  #   region = "us-west-1"
  # }
}

provider "aws" {
  region = var.region
}
