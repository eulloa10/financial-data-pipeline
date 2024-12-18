provider "aws" {
  region = "us-west-2"  # Any AWS region is fine for LocalStack
  access_key = "test" # LocalStack requires fake AWS credentials
  secret_key = "test"
  endpoints {
    s3 = "http://localhost:4566"
    glue = "http://localhost:4566"
    # Add more services if needed
  }
}
