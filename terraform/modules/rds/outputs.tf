output "instance_id" {
  description = "ID of the RDS instance"
  value       = aws_db_instance.fred.id
}


output "endpoint" {
  description = "Endpoint of the RDS instance"
  value       = aws_db_instance.fred.endpoint
}
