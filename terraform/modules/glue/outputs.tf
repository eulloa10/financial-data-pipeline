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

output "security_group_id" {
  description = "ID of the security group for Glue jobs"
  value       = var.security_group_id
}
