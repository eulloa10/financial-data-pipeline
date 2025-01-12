module "extract_job" {
  source = "./modules/extract_job"

  project             = var.project
  region              = var.region
  data_lake_name      = var.data_lake_name
  glue_scripts_bucket = var.glue_scripts_bucket
  python_version      = var.python_version
  timeout             = var.timeout
  fred_api_key        = var.fred_api_key
}

module "transform_job" {
  source = "./modules/transform_job"

  project             = var.project
  region              = var.region
  data_lake_name      = var.data_lake_name
  glue_scripts_bucket = module.extract_job.scripts_bucket_id
  glue_role_arn       = module.extract_job.glue_role_arn
  python_version      = var.python_version
  timeout             = var.timeout
  fred_api_key        = var.fred_api_key
}

module "aggregate_job" {
  source = "./modules/aggregate_job"

  project             = var.project
  region              = var.region
  data_lake_name      = var.data_lake_name
  glue_scripts_bucket = module.extract_job.scripts_bucket_id
  glue_role_arn       = module.extract_job.glue_role_arn
  python_version      = var.python_version
  timeout             = var.timeout
  fred_api_key        = var.fred_api_key
}
