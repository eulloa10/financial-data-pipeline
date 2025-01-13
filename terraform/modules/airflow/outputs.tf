output "security_group_id" {
  description = "ID of the Airflow security group"
  value       = aws_security_group.airflow.id
}

output "instance_id" {
  description = "ID of the Airflow EC2 instance"
  value       = aws_instance.airflow.id
}

output "public_ip" {
  description = "Public IP of the Airflow EC2 instance"
  value       = aws_instance.airflow.public_ip
}
