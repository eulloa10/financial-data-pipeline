data "aws_availability_zones" "available" {
  state = "available"
}

resource "aws_db_subnet_group" "main" {
  name       = "${var.project}-db-subnet-group"
  subnet_ids = var.public_subnet_ids

  tags = {
    Name        = "${var.project}-db-subnet-group"
    Environment = var.environment
  }
}

resource "aws_security_group" "rds" {
  name        = "${var.project}-rds-sg"
  description = "Security group for RDS PostgreSQL"
  vpc_id      = var.vpc_id

  # Allow access from Glue
  ingress {
    from_port       = 5432
    to_port         = 5432
    protocol        = "tcp"
    security_groups = [var.glue_security_group_id]
    description     = "Allow access from Glue"
  }

  # Allow access from Looker Studio
  ingress {
    from_port   = 5432
    to_port     = 5432
    protocol    = "tcp"
    cidr_blocks = var.allowed_rds_ips
    description = "Allow Looker Studio access"
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
    description = "Allow all outbound traffic"
  }

  tags = {
    Name        = "${var.project}-rds-sg"
    Environment = var.environment
  }
}

resource "aws_db_instance" "fred" {
  identifier        = "${var.project}-${var.environment}-db"
  engine            = "postgres"
  engine_version    = var.engine_version
  instance_class    = var.instance_class
  allocated_storage = 20
  storage_type      = "gp2"
  availability_zone = data.aws_availability_zones.available.names[0]
  multi_az          = false

  db_name  = var.db_name
  username = var.db_username
  password = var.db_password

  db_subnet_group_name   = aws_db_subnet_group.main.name
  vpc_security_group_ids = [aws_security_group.rds.id]
  publicly_accessible    = true  # Changed to true to allow Looker Studio access

  backup_retention_period = 7
  backup_window          = "06:00-07:00" #10:00 PM - 11:00 PM PST
  maintenance_window     = "Sun:05:00-Sun:06:00" # Sat 9:00 PM - 10:00 PM PST
  skip_final_snapshot = var.environment == "dev"
  delete_automated_backups = true
  deletion_protection     = true  # For dev environment

  lifecycle {
    prevent_destroy = true
  }
  tags = {
    Name        = "${var.project}-${var.environment}-db"
    Environment = var.environment
  }
}
