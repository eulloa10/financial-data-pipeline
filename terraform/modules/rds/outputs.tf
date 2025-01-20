output "instance_id" {
  description = "ID of the RDS instance"
  value       = aws_db_instance.fred.id
}

output "db_endpoint" {
  description = "Endpoint of the RDS instance"
  value       = split(":", aws_db_instance.fred.endpoint)[0] # Remove the port number
}

output "security_group_id" {
  value = aws_security_group.rds.id
}

output "rds_hostname" {
  description = "Hostname of the RDS instance"
  value       = aws_db_instance.fred.address
}

output "rds_port" {
  description = "Port of the RDS instance"
  value       = aws_db_instance.fred.port
}

output "rds_username" {
  description = "Username for the RDS instance"
  value       = aws_db_instance.fred.username
}
