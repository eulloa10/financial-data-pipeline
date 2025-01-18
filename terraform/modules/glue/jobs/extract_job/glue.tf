resource "aws_glue_job" "fred_ingestion_monthly_etl_job" {
  name     = "${var.project}-fred-extract-month-job"
  role_arn = var.glue_role_arn
  glue_version = var.glue_version

  command {
    name="glueetl"
    script_location = "s3://${var.project}-${var.scripts_bucket_id}/${aws_s3_object.glue_job_extract_fred_api.id}"
    python_version = var.python_version
  }

  default_arguments = {
    "--RAW_DATA_BUCKET"   = "${var.project}-${var.data_lake_name}"
    "--TARGET_PATH"     = "raw_data"
    "--START_DATE"      = var.observation_start_date
    "--END_DATE"        = var.observation_end_date
    "--API_KEY"         = var.fred_api_key
  }

  timeout = var.timeout
  number_of_workers = var.number_of_workers
  worker_type = var.worker_type
}

resource "aws_glue_job" "fred_ingestion_range_etl_job" {
  name     = "${var.project}-fred-extract-range-job"
  role_arn = aws_iam_role.glue_role.arn
  glue_version = var.glue_version

  command {
    name = "glueetl"
    script_location = "s3://${var.scripts_bucket_id}/${aws_s3_object.glue_job_extract_range_fred_api.id}"
    python_version = var.python_version
  }

  default_arguments = {
    "--RAW_DATA_BUCKET" = "${var.project}-${var.data_lake_name}"
    "--TARGET_PATH"     = "raw_data"
    "--START_DATE"      = var.observation_start_date
    "--END_DATE"        = var.observation_end_date
    "--API_KEY"         = var.fred_api_key
  }

  timeout = var.long_timeout
  number_of_workers = var.number_of_workers
  worker_type = var.worker_type
}
