resource "aws_security_group" "glue" {
  name        = "${var.project}-${var.environment}-glue-sg"
  description = "Security group for Glue jobs"
  vpc_id      = module.networking.vpc_id
  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
    description = "Allow all outbound traffic"
  }

  tags = {
    Name        = "${var.project}-${var.environment}-glue-sg"
    Environment = var.environment
  }
}

module "networking" {
  source = "./modules/networking"

  project     = var.project
  environment = var.environment
  vpc_cidr    = var.vpc_cidr
  region      = var.region
}

module "airflow" {
  source = "./modules/airflow"

  project                = var.project
  environment            = var.environment
  vpc_id                 = module.networking.vpc_id
  subnet_id              = module.networking.public_subnet_ids[0]
  allowed_ips            = var.allowed_ips
  key_name               = var.key_name
  instance_type          = var.airflow_instance_type
  region                 = var.region
  airflow_db_password    = var.airflow_db_password
  webserver_secret_key   = var.airflow_webserver_secret_key
  fernet_key             = var.airflow_fernet_key

  depends_on = [module.networking]
}

module "rds" {
  source = "./modules/rds"

  project                   = var.project
  environment               = var.environment
  region                    = var.region
  vpc_id                    = module.networking.vpc_id
  private_subnet_ids        = module.networking.private_subnet_ids
  db_name                   = var.db_name
  db_username               = var.db_username
  db_password               = var.db_password
  instance_class            = var.db_instance_class
  airflow_security_group_id = module.airflow.security_group_id
  glue_security_group_id    = aws_security_group.glue.id
  alert_email               = var.alert_email

  depends_on = [module.networking]
}

module "glue" {
  source = "./modules/glue"

  project             = var.project
  environment         = var.environment
  region              = var.region
  vpc_id              = module.networking.vpc_id
  data_lake_name      = var.data_lake_name
  glue_scripts_bucket = var.glue_scripts_bucket
  python_version      = var.python_version
  timeout             = var.timeout
  fred_api_key        = var.fred_api_key
  security_group_id   = aws_security_group.glue.id
}

module "monitoring" {
  source = "./modules/monitoring"

  project              = var.project
  environment          = var.environment
  region               = var.region
  airflow_instance_id  = module.airflow.instance_id
  rds_instance_id      = module.rds.instance_id
  alert_email          = var.alert_email

  depends_on = [module.airflow, module.rds]
}
