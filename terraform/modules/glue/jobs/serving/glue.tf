resource "aws_glue_job" "fred_load_to_rds_job" {
  name         = "${var.project}-fred-load-to-rds-job"
  role_arn     = var.glue_role_arn
  glue_version = var.glue_version

  command {
    name            = "glueetl"
    script_location = "s3://${var.glue_scripts_bucket}/${aws_s3_object.glue_job_load_fred_to_rds.id}"
    python_version  = var.python_version
  }

  default_arguments = {
    "--SRC_BUCKET"      = "${var.project}-${var.data_lake_name}"
    "--SRC_PREFIX"      = "aggregated_data"
    "--YEAR"           = var.year
    "--DB_SECRET_NAME" = var.db_secret_name
    "--DB_NAME"        = var.db_name
    "--TABLE_NAME"     = var.table_name
    "--additional-python-modules" = "psycopg2-binary"
  }

  connections = [var.glue_connection_name]  # Connection to access RDS
  timeout     = var.timeout
  max_retries = 0

  execution_property {
    max_concurrent_runs = 1
  }
}
