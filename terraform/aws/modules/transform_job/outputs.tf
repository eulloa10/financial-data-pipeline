output "data_lake_bucket_id" {
  value = aws_s3_bucket.data_lake.id
}

output "scripts_bucket_id" {
  value = aws_s3_bucket.scripts.id
}

output "glue_role_arn" {
  value = aws_iam_role.glue_role.arn
}

output "glue_fred_transform_job" {
  value = aws_glue_job.fred_transform_etl_job.name
}
