data "aws_ami" "amazon_linux_2" {
  most_recent = true
  owners      = ["amazon"]

  filter {
    name   = "name"
    values = ["amzn2-ami-hvm-*-x86_64-gp2"]
  }

  filter {
    name   = "virtualization-type"
    values = ["hvm"]
  }
}

resource "aws_security_group" "airflow" {
  name        = "${var.project}-airflow-sg"
  description = "Security group for Airflow EC2 instance"
  vpc_id      = var.vpc_id

  ingress {
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = var.allowed_ips
  }

  ingress {
    from_port   = 8080
    to_port     = 8080
    protocol    = "tcp"
    cidr_blocks = var.allowed_ips
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name        = "${var.project}-airflow-sg"
    Environment = var.environment
  }
}

resource "aws_iam_role" "airflow" {
  name = "${var.project}-airflow-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "ec2.amazonaws.com"
        }
      }
    ]
  })
}

resource "aws_iam_instance_profile" "airflow" {
  name = "${var.project}-airflow-profile"
  role = aws_iam_role.airflow.name
}

resource "aws_instance" "airflow" {
  ami           = data.aws_ami.amazon_linux_2.id
  instance_type = var.instance_type

  subnet_id                   = var.subnet_id
  vpc_security_group_ids      = [aws_security_group.airflow.id]
  associate_public_ip_address = true
  iam_instance_profile        = aws_iam_instance_profile.airflow.name
  key_name                    = var.key_name

  credit_specification {
    cpu_credits = "standard"
  }

  root_block_device {
    volume_size = 30
    volume_type = "gp3"
  }

  user_data = templatefile("${path.module}/templates/setup.sh.tpl", {
    project     = var.project
    environment = var.environment
    region      = var.region
    dags_bucket = aws_s3_bucket.airflow_dags.id
    docker_compose_content = templatefile("${path.module}/templates/docker-compose.yml.tpl", {
      airflow_db_password    = var.airflow_db_password
      fernet_key            = var.fernet_key
      webserver_secret_key  = var.webserver_secret_key
      dags_bucket          = aws_s3_bucket.airflow_dags.id
    })
    airflow_admin_username   = var.airflow_admin_username
    airflow_admin_firstname  = var.airflow_admin_firstname
    airflow_admin_lastname   = var.airflow_admin_lastname
    airflow_admin_email      = var.airflow_admin_email
    airflow_admin_password   = var.airflow_admin_password
  })

  tags = {
    Name        = "${var.project}-airflow"
    Environment = var.environment
  }
}

resource "aws_s3_bucket" "airflow_dags" {
  bucket = "${var.project}-airflow-dags"
}

resource "aws_s3_bucket_public_access_block" "airflow_dags" {
  bucket = aws_s3_bucket.airflow_dags.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}
