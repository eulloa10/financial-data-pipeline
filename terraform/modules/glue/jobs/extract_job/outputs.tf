output "data_lake_bucket_id" {
  value = aws_s3_bucket.data_lake.id
}

output "scripts_bucket_id" {
  value = aws_s3_bucket.scripts.id
}

output "glue_role_arn" {
  value = aws_iam_role.glue_role.arn
}

output "glue_api_monthly_extract_job" {
  value = aws_glue_job.fred_ingestion_monthly_etl_job.name
}

output "glue_api_range_extract_job" {
  value = aws_glue_job.fred_ingestion_range_etl_job.name
}
