resource "aws_s3_bucket" "data_lake" {
  bucket = "${var.project}-${var.data_lake_name}"
}
resource "aws_s3_bucket" "scripts" {
  bucket = "${var.project}-${var.glue_scripts_bucket}"
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

# Enable versioning for both buckets
# resource "aws_s3_bucket_versioning" "data_lake" {
#   bucket = aws_s3_bucket.data_lake.id
#   versioning_configuration {
#     status = "Enabled"
#   }
# }

# resource "aws_s3_bucket_versioning" "scripts" {
#   bucket = aws_s3_bucket.scripts.id
#   versioning_configuration {
#     status = "Enabled"
#   }
# }

# IAM Role for Glue
resource "aws_iam_role" "glue_role" {
  name               = "${var.project}-glue-role"
  assume_role_policy = data.aws_iam_policy_document.glue_base_policy.json
}

resource "aws_iam_role_policy" "glue_access" {
  name   = "${var.project}-glue-access-policy"
  role   = aws_iam_role.glue_role.id
  policy = data.aws_iam_policy_document.glue_access_policy.json
}

# Optional: Attach secrets access policy if needed
resource "aws_iam_role_policy" "secrets_access" {
  name   = "${var.project}-secrets-access-policy"
  role   = aws_iam_role.glue_role.id
  policy = data.aws_iam_policy_document.secrets_access_policy.json
}

module "extract_job" {
  source = "./jobs/extract_job/"

  project             = var.project
  region              = var.region
  data_lake_name      = var.data_lake_name
  glue_scripts_bucket = var.glue_scripts_bucket
  python_version      = var.python_version
  timeout             = var.timeout
  fred_api_key        = var.fred_api_key
}

module "transform_job" {
  source = "./jobs/transform_job"

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
  source = "./jobs/aggregate_job"

  project             = var.project
  region              = var.region
  data_lake_name      = var.data_lake_name
  glue_scripts_bucket = module.extract_job.scripts_bucket_id
  glue_role_arn       = module.extract_job.glue_role_arn
  python_version      = var.python_version
  timeout             = var.timeout
  fred_api_key        = var.fred_api_key
}
