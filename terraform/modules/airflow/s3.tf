resource "aws_s3_bucket" "airflow_dags" {
  bucket = "${var.project}-airflow-dags-${var.environment}"

  tags = {
    Name        = "${var.project}-airflow-dags"
    Environment = var.environment
  }
}

resource "aws_s3_bucket_versioning" "airflow_dags" {
  bucket = aws_s3_bucket.airflow_dags.id
  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_public_access_block" "airflow_dags" {
  bucket = aws_s3_bucket.airflow_dags.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}
