resource "aws_glue_job" "fred_transform_etl_job" {
  name         = "${var.project}-transform-job"
  role_arn     = var.glue_role_arn
  glue_version = var.glue_version

  command {
    name            = "glueetl"
    script_location = "s3://${var.project}-${var.glue_scripts_bucket}/${aws_s3_object.glue_job_transform_fred_data.id}"
    python_version  = var.python_version
  }

  default_arguments = {
    "--SRC_BUCKET"      = "${var.project}-${var.data_lake_name}"
    "--SRC_PREFIX"      = "raw_data"
    "--DEST_BUCKET"     = "${var.project}-${var.data_lake_name}"
    "--DEST_PREFIX"     = "processed_data"
  }

  execution_property {
    max_concurrent_runs = 5
  }

  timeout           = var.timeout
  number_of_workers = var.number_of_workers
  worker_type       = var.worker_type
}
