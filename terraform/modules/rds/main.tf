resource "aws_db_subnet_group" "main" {
  name       = "${var.project}-db-subnet-group"
  subnet_ids = var.private_subnet_ids

  tags = {
    Name        = "${var.project}-db-subnet-group"
    Environment = var.environment
  }
}

resource "aws_security_group" "rds" {
  name        = "${var.project}-rds-sg"
  description = "Security group for RDS PostgreSQL"
  vpc_id      = var.vpc_id

  ingress {
    from_port       = 5432
    to_port         = 5432
    protocol        = "tcp"
    security_groups = [var.airflow_security_group_id]
  }

  tags = {
    Name        = "${var.project}-rds-sg"
    Environment = var.environment
  }
}

resource "aws_db_instance" "fred" {
  identifier        = "${var.project}-${var.environment}-db"
  engine            = "postgres"
  engine_version    = "14.7"
  instance_class    = var.instance_class
  allocated_storage = 20

  db_name  = var.db_name
  username = var.db_username
  password = var.db_password

  db_subnet_group_name   = aws_db_subnet_group.main.name
  vpc_security_group_ids = [aws_security_group.rds.id]
  publicly_accessible    = false

  backup_retention_period = 7
  backup_window          = "03:00-04:00"
  maintenance_window     = "Mon:04:00-Mon:05:00"

  skip_final_snapshot = var.environment == "dev"

  tags = {
    Name        = "${var.project}-${var.environment}-db"
    Environment = var.environment
  }
}
