resource "aws_glue_job" "fred_aggregate_etl_job" {
  name     = "${var.project}-fred-aggregate-job"
  role_arn = var.glue_role_arn
  glue_version = var.glue_version

  command {
    name="glueetl"
    script_location = "s3://${var.project}-${var.glue_scripts_bucket}/${aws_s3_object.glue_job_aggregate_fred_data.id}"
    python_version = var.python_version
  }

  default_arguments = {
    "--SRC_BUCKET"   = "${var.project}-${var.data_lake_name}"
    "--SRC_PREFIX"     = "processed_data"
    "--DEST_BUCKET"     = "${var.project}-${var.data_lake_name}"
    "--DEST_PREFIX"     = "aggregated_data"
    "--START_YEAR"      = var.observation_start_year
    "--END_YEAR"        = var.observation_end_year
    "--API_KEY"         = var.fred_api_key
  }

  timeout = var.timeout
  number_of_workers = var.number_of_workers
  worker_type = var.worker_type
}

resource "aws_glue_job" "fred_aggregate_month_etl_job" {
  name         = "${var.project}-fred-aggregate-month-job"
  role_arn     = var.glue_role_arn
  glue_version = var.glue_version

  command {
    name            = "glueetl"
    script_location = "s3://${var.glue_scripts_bucket}/${aws_s3_object.glue_job_aggregate_month_fred_data.id}"
    python_version  = var.python_version
  }

  default_arguments = {
    "--SRC_BUCKET"  = "${var.project}-${var.data_lake_name}"
    "--SRC_PREFIX"  = "processed_data"
    "--DEST_BUCKET" = "${var.project}-${var.data_lake_name}"
    "--DEST_PREFIX" = "aggregated_data"
    "--YEAR"        = var.observation_year
    "--MONTH"       = var.observation_month
  }

  timeout           = var.timeout
  number_of_workers = var.number_of_workers
  worker_type       = var.worker_type
}
