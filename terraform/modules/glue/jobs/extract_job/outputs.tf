output "glue_api_monthly_extract_job" {
  description = "Name of the monthly extract Glue job"
  value = aws_glue_job.fred_ingestion_etl_job.name
}

# output "glue_api_monthly_extract_job" {
#   description = "Name of the monthly extract Glue job"
#   value = aws_glue_job.fred_ingestion_monthly_etl_job.name
# }

# output "glue_api_range_extract_job" {
#   description = "Name of the range extract Glue job"
#   value = aws_glue_job.fred_ingestion_range_etl_job.name
# }

output "scripts_bucket_name" {
  description = "Name of the scripts bucket"
  value       = "${var.project}-${var.glue_scripts_bucket}"
}

output "script_location" {
  value = "s3://${var.project}-${var.glue_scripts_bucket}/${aws_s3_object.glue_job_extract_fred_api.key}"
}
