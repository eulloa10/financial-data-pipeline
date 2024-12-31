resource "aws_glue_job" "fred_transform_etl_job" {
  name     = "${var.project}-fred-transform-job"
  role_arn = aws_iam_role.glue_role.arn
  glue_version = var.glue_version

  command {
    name="glueetl"
    script_location = "s3://${aws_s3_bucket.scripts.id}/${aws_s3_object.glue_job_transform_fred_api.id}"
    python_version = var.python_version
  }

  default_arguments = {
    "--SRC_BUCKET"   = "${var.project}-${var.data_lake_name}"
    "--SRC_PREFIX"     = "raw_data"
    "--DEST_BUCKET"     = "${var.project}-${var.data_lake_name}"
    "--DEST_PREFIX"     = "processed_data"
    "--START_DATE"      = var.observation_start_date
    "--END_DATE"        = var.observation_end_date
    "--API_KEY"         = var.fred_api_key
  }

  timeout = var.timeout
  number_of_workers = var.number_of_workers
  worker_type = var.worker_type
}
