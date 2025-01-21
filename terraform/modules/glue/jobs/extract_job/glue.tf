resource "aws_glue_job" "fred_ingestion_etl_job" {
  name         = "${var.project}-fred-extract-job"
  role_arn     = var.glue_role_arn
  glue_version = var.glue_version

  command {
    name            = "glueetl"
    script_location = "s3://${var.project}-${var.glue_scripts_bucket}/${aws_s3_object.glue_job_extract_fred_api.key}"
    python_version  = var.python_version
  }

  default_arguments = {
    "--RAW_DATA_BUCKET" = "${var.project}-${var.data_lake_name}"
    "--TARGET_PATH"     = "raw_data"
    "--START_DATE"      = var.observation_start_date
    "--END_DATE"        = var.observation_end_date
    "--API_KEY"         = var.fred_api_key
    "--INDICATOR"       = var.indicator != "" ? var.indicator: " " # Optional - will process all indicators if not provided
  }

  execution_property {
    max_concurrent_runs = 1
  }

  timeout           = var.timeout
  number_of_workers = var.number_of_workers
  worker_type       = var.worker_type
}
