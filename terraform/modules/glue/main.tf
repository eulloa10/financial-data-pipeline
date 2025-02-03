resource "aws_s3_bucket" "data_lake" {
  bucket = "${var.project}-${var.data_lake_name}"
  lifecycle {
    prevent_destroy = true
  }
}

resource "aws_s3_bucket" "scripts" {
  bucket = "${var.project}-${var.glue_scripts_bucket}"

  lifecycle {
    prevent_destroy = true
  }
}

resource "aws_s3_bucket_public_access_block" "data_lake" {
  bucket = aws_s3_bucket.data_lake.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_s3_bucket_public_access_block" "scripts" {
  bucket = aws_s3_bucket.scripts.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_iam_role" "glue_role" {
  name               = "${var.project}-glue-role"
  assume_role_policy = data.aws_iam_policy_document.glue_base_policy.json

  lifecycle {
    prevent_destroy = true
  }
}

resource "aws_iam_role_policy" "glue_access" {
  name   = "${var.project}-glue-access-policy"
  role   = aws_iam_role.glue_role.id
  policy = data.aws_iam_policy_document.glue_access_policy.json
}

resource "aws_iam_role_policy" "secrets_access" {
  name   = "${var.project}-secrets-access-policy"
  role   = aws_iam_role.glue_role.id
  policy = data.aws_iam_policy_document.secrets_access_policy.json
}

module "extract_job" {
  source = "./jobs/extract_job/"

  project                 = var.project
  region                  = var.region
  data_lake_name          = var.data_lake_name
  glue_scripts_bucket     = var.glue_scripts_bucket
  python_version          = var.python_version
  timeout                 = var.timeout
  fred_api_key            = var.fred_api_key
  glue_assume_role_policy = data.aws_iam_policy_document.glue_base_policy.json
  glue_access_policy      = data.aws_iam_policy_document.glue_access_policy.json
  scripts_bucket_id       = aws_s3_bucket.scripts.id
  glue_role_arn           = aws_iam_role.glue_role.arn
}

module "transform_job" {
  source = "./jobs/transform_job"

  project                 = var.project
  region                  = var.region
  data_lake_name          = var.data_lake_name
  glue_scripts_bucket     = var.glue_scripts_bucket
  python_version          = var.python_version
  timeout                 = var.timeout
  fred_api_key            = var.fred_api_key
  glue_assume_role_policy = data.aws_iam_policy_document.glue_base_policy.json
  glue_access_policy      = data.aws_iam_policy_document.glue_access_policy.json
  scripts_bucket_id       = aws_s3_bucket.scripts.id
  glue_role_arn          = aws_iam_role.glue_role.arn
}

module "aggregate_job" {
  source = "./jobs/aggregate_job"

  project                 = var.project
  region                  = var.region
  data_lake_name          = var.data_lake_name
  glue_scripts_bucket     = var.glue_scripts_bucket
  python_version          = var.python_version
  timeout                 = var.timeout
  fred_api_key            = var.fred_api_key
  glue_assume_role_policy = data.aws_iam_policy_document.glue_base_policy.json
  glue_access_policy      = data.aws_iam_policy_document.glue_access_policy.json
  scripts_bucket_id       = aws_s3_bucket.scripts.id
  glue_role_arn           = aws_iam_role.glue_role.arn
}

module "serving" {
  source = "./jobs/serving"

  project                 = var.project
  data_lake_name          = var.data_lake_name
  glue_scripts_bucket     = var.glue_scripts_bucket
  python_version          = var.python_version
  glue_role_arn           = aws_iam_role.glue_role.arn
  glue_assume_role_policy = data.aws_iam_policy_document.glue_base_policy.json
  glue_access_policy      = data.aws_iam_policy_document.glue_access_policy.json
  db_host                 = var.db_host
  db_name                 = var.db_name
  db_username             = var.db_username
  db_password             = var.db_password
  start_year              = var.start_year
  vpc_id                 = var.vpc_id
  private_subnet_id      = var.private_subnet_id
  private_subnet_az      = var.private_subnet_az
  glue_security_group_id = var.glue_security_group_id
}
