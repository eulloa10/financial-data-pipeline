resource "aws_glue_job" "fred_ingestion_etl_job" {
  name     = "${var.project}-fred_extract_job"
  role_arn = aws_iam_role.glue_role.arn
  glue_version = var.glue_version

  command {
    name="glueetl"
    script_location = "s3://${aws_s3_bucket.scripts.id}/${aws_s3_object.glue_job_extract_fred_api.id}"
    python_version = var.python_version
  }

  default_arguments = {
    "--raw_data_bucket"   = "${var.project}-${var.data_lake_name}"
    "--target_path"     = "raw_data"
    "--start_date"      = var.observation_start_date
    "--end_date"        = var.observation_end_date
    "--API_KEY"         = var.fred_api_key
  }

  timeout = var.timeout
  number_of_workers = var.number_of_workers
  worker_type = var.worker_type
}

# resource "aws_glue_job" "fred_ingestion_etl_full_range_job" {
#   name     = "${var.project}-fred_extract_full_range-job"  # Updated name for the larger date range job
#   role_arn = aws_iam_role.glue_role.arn
#   glue_version = var.glue_version

#   command {
#     name = "glueetl"
#     script_location = "s3://${aws_s3_bucket.scripts.id}/${aws_s3_object.glue_job_extract_fred_api.id}"
#     python_version = var.python_version
#   }

#   default_arguments = {
#     "--raw_data_bucket" = "${var.project}-${var.data_lake_name}"
#     "--target_path"     = "raw_data"
#     "--obs_start_date"  = var.observation_start_date
#     "--obs_end_date"    = var.observation_end_date
#     "--API_KEY"         = var.fred_api_key
#   }

#   timeout = var.long_timeout
#   number_of_workers = var.number_of_workers
#   worker_type = var.worker_type
# }
