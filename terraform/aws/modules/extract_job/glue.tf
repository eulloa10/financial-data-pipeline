resource "aws_glue_job" "fred_ingestion_etl_job" {
  name     = "${var.project}-fred_extract_job"
  role_arn = aws_iam_role.glue_role.arn
  glue_version = var.glue_version

  command {
    name="glueetl"
    script_location = "s3://${aws_s3_bucket.scripts.id}/${aws_s3_object.glue_job_extract_fred_api.id}"
    python_version = var.python_version
  }

  timeout = var.timeout
  number_of_workers = var.number_of_workers
  worker_type = var.worker_type
}
