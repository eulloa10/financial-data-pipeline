terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
    postgresql = {
      source  = "cyrilgdn/postgresql"
      version = "~> 1.0"
    }
  }
}

provider "aws" {
  region = var.region
}

provider "postgresql" {
  host     = module.rds.db_endpoint
  port     = 5432
  database = var.db_name
  username = var.db_username
  password = var.db_password
  sslmode  = "require"
}
