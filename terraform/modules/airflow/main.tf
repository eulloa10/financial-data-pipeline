# modules/airflow/main.tf
resource "aws_security_group" "airflow_sg" {
  name        = "${var.name_prefix}-airflow-sg"
  description = "Security group for Airflow EC2 instance"
  vpc_id      = var.vpc_id

  ingress {
    description      = "Allow HTTP traffic to Airflow web UI"
    from_port        = 8080
    to_port          = 8080
    protocol         = "tcp"
    cidr_blocks      = var.airflow_ingress_cidr_blocks
    ipv6_cidr_blocks = []
  }

  ingress {
    description      = "Allow SSH access"
    from_port        = 22
    to_port          = 22
    protocol         = "tcp"
    cidr_blocks      = var.ssh_ingress_cidr_blocks
    ipv6_cidr_blocks = []
  }

  egress {
    description = "Allow all outbound traffic"
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = merge(
    var.tags,
    {
      Name = "${var.name_prefix}-airflow-sg"
    }
  )
}

resource "aws_iam_role" "airflow_ec2_role" {
  name = "${var.name_prefix}-airflow-ec2-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action    = "sts:AssumeRole"
      Effect    = "Allow"
      Principal = {
        Service = "ec2.amazonaws.com"
      }
    }]
  })

  tags = var.tags
}

resource "aws_iam_policy" "airflow_policy" {
  name        = "${var.name_prefix}-airflow-policy"
  description = "IAM policy for Airflow to access S3 and Glue"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect   = "Allow"
        Action   = [
          "s3:GetObject",
          "s3:ListBucket"
        ]
        Resource = [
          aws_s3_bucket.airflow_dags.arn,
          "${aws_s3_bucket.airflow_dags.arn}/*"
        ]
      },
      {
        Effect   = "Allow"
        Action   = [
          "glue:StartJobRun",
          "glue:GetJobRun",
          "glue:GetJob"
        ]
        Resource = "*"
      },
      {
        Effect = "Allow"
        Action = [
          "ssm:SendCommand",
          "ssm:StartSession",
          "ssm:GetCommandInvocation"
        ]
        Resource = "*"
      },
      {
        Effect = "Allow"
        Action = [
          "ec2:StartInstances",
          "ec2:StopInstances"
        ]
        Resource = aws_instance.airflow_ec2.arn
      },
      {
        Effect = "Allow"
        Action = [
          "ssm:DescribeAutomationExecutions",
          "ssm:GetAutomationExecution"
        ]
        Resource = "*"
      }
    ]
  })

  tags = var.tags
}

resource "aws_iam_role_policy_attachment" "attach_airflow_policy" {
  role       = aws_iam_role.airflow_ec2_role.name
  policy_arn = aws_iam_policy.airflow_policy.arn
}

resource "aws_iam_instance_profile" "airflow_instance_profile" {
  name = "${var.name_prefix}-airflow-ec2-profile"
  role = aws_iam_role.airflow_ec2_role.name
}

resource "aws_instance" "airflow_ec2" {
  ami                         = var.ami
  instance_type               = var.instance_type
  subnet_id                   = var.subnet_id
  vpc_security_group_ids      = [aws_security_group.airflow_sg.id]
  associate_public_ip_address = true
  key_name                    = var.key_name
  iam_instance_profile        = aws_iam_instance_profile.airflow_instance_profile.name

  root_block_device {
    volume_size = 16
    volume_type = "gp3"
    encrypted   = true
  }
  credit_specification {
    cpu_credits = "standard"
  }

  user_data = templatefile("${path.module}/templates/setup.sh.tpl", {
    dag_s3_bucket          = aws_s3_bucket.airflow_dags.bucket
    airflow_admin_username = var.airflow_admin_username
    airflow_admin_password = var.airflow_admin_password
    aws_region             = var.region
    docker_compose_content = templatefile("${path.module}/templates/docker-compose.yml.tpl", {
      aws_region             = var.region
    })
  })

  tags = merge(
    var.tags,
    {
      Name = "${var.name_prefix}-airflow-ec2"
    }
  )
}
