output "instance_id" {
  description = "ID of the RDS instance"
  value       = aws_db_instance.fred.id
}

output "db_endpoint" {
  description = "Endpoint of the RDS instance"
  value       = aws_db_instance.fred.endpoint
}

output "security_group_id" {
  value = aws_security_group.rds.id
}
