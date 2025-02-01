output "airflow_public_ip" {
  description = "Public IP address of the Airflow EC2 instance"
  value       = aws_instance.airflow_ec2.public_ip
}

output "airflow_security_group_id" {
  description = "Security Group ID for Airflow EC2 instance"
  value       = aws_security_group.airflow_sg.id
}

output "airflow_instance_id" {
  description = "EC2 Instance ID for Airflow"
  value       = aws_instance.airflow_ec2.id
}

output "instance_id" {
  description = "EC2 Instance ID for Airflow"
  value       = aws_instance.airflow_ec2.id
}

output "airflow_url" {
  description = "URL to access the Airflow web UI"
  value       = "http://${aws_instance.airflow_ec2.public_ip}:8080"
}

output "dags_bucket_name" {
  value = aws_s3_bucket.airflow_dags.id
}

output "dags_bucket_arn" {
  value = aws_s3_bucket.airflow_dags.arn
}
