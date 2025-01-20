resource "aws_glue_connection" "rds_connection" {
  name = "${var.project}-rds-connection"

  connection_type = "JDBC"

  connection_properties = {
    JDBC_CONNECTION_URL = "jdbc:postgresql://${var.db_host}:5432/${var.db_name}"
    USERNAME           = var.db_username
    PASSWORD           = var.db_password
  }

  physical_connection_requirements {
    availability_zone = var.private_subnet_az
    subnet_id        = var.private_subnet_id
    security_group_id_list = [var.glue_security_group_id]
  }
}

resource "aws_glue_job" "load_indicators_to_rds" {
  name     = "${var.project}-load-indicators-to-rds"
  role_arn = var.glue_role_arn
  glue_version = var.glue_version

  command {
    name="glueetl"
    script_location = "s3://${var.project}-${var.glue_scripts_bucket}/${aws_s3_object.glue_job_load_fred_data.id}"
    python_version = var.python_version
  }

  default_arguments = {
      "--SRC_BUCKET"      = "${var.project}-${var.data_lake_name}"
      "--SRC_PREFIX"      = "aggregated_data"
      "--START_YEAR"      = var.start_year
      "--END_YEAR"        = var.end_year    # Optional
      "--INDICATOR"       = var.indicator   # Optional
      "--DB_HOST"         = var.db_host
      "--DB_NAME"         = var.db_name
      "--DB_USER"         = var.db_username
      "--DB_PASSWORD"     = var.db_password
      "--DB_PORT"         = "5432"
      "--TABLE_NAME"      = "economic_indicators"
  }

    execution_property {
    max_concurrent_runs = 1
  }

  worker_type  = var.worker_type
  number_of_workers = var.number_of_workers
  timeout      = var.timeout

  connections = [aws_glue_connection.rds_connection.name]
}
