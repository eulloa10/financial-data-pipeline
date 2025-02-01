resource "aws_glue_job" "fred_aggregate_etl_job" {
  name     = "${var.project}-aggregate-job"
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
    "--API_KEY"         = var.fred_api_key
  }

  execution_property {
    max_concurrent_runs = 1
  }

  timeout = var.timeout
  number_of_workers = var.number_of_workers
  worker_type = var.worker_type
}
