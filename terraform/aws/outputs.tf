output "project" {
  value = var.project
}

output "region" {
  value = var.region
}

output "data_lake_name" {
  value = var.data_lake_name
}

output "glue_scripts_bucket" {
  value = var.glue_scripts_bucket
}

output "aws_user" {
  value = var.aws_user
}

output "terraform_bucket" {
  value = var.terraform_bucket
}

# Module: Extract
# output "glue_rds_extract_job" {
#   value = module.extract_job.glue_rds_extract_job
# }

# output "glue_api_users_extract_job" {
#   value = module.extract_job.glue_api_users_extract_job
# }

# output "glue_sessions_users_extract_job" {
#   value = module.extract_job.glue_sessions_users_extract_job
# }

# output "glue_role_arn" {
#   value = module.extract_job.glue_role_arn
# }
