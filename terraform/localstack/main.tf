resource "aws_s3_bucket" "fred_glue_scripts_bucket" {
  bucket = var.glue_scripts_bucket
}

resource "aws_s3_bucket" "fred_glue_scripts_bucket" {
  bucket = var.fred_data_bucket
}

# resource "aws_iam_role" "glue_role" {
#   name               = "glue-role"
#   assume_role_policy = data.aws_iam_policy_document.glue_assume_role_policy.json
# }

# data "aws_iam_policy_document" "glue_assume_role_policy" {
#   statement {
#     actions = ["sts:AssumeRole"]
#     principals {
#       type        = "Service"
#       identifiers = ["glue.amazonaws.com"]
#     }
#   }
# }

# data "aws_iam_policy_document" "s3_bucket_policy" {
#   statement {
#     sid = "AllowS3BucketAccess"
#     actions = [
#       "s3:PutObject",
#       "s3:ListBucket",
#       "s3:GetObject",
#       "s3:GetBucketLocation",
#       "s3:DeleteObject"
#     ]
#     resources = [
#       "arn:aws:s3:local:fred-glue-scripts",
#       "arn:aws:s3:local:fred-glue-scripts/*",
#     ]
#   }
# }

# resource "aws_iam_role_policy_attachment" "glue_s3_access" {
#   role       = aws_iam_role.glue_role.name
#   policy_arn = data.aws_iam_policy_document.s3_bucket_policy.json
# }

# resource "aws_iam_role_policy_attachment" "glue_service_role_policy" {
#   role       = aws_iam_role.glue_role.name
#   policy_arn = "arn:aws:iam::aws:policy/service-role/AWSGlueServiceRole"
# }
