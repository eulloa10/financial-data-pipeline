resource "aws_s3_bucket" "fred_glue_scripts_bucket" {
  bucket = var.glue_scripts_bucket
}

resource "aws_s3_bucket" "fred_data_bucket" {
  bucket = var.fred_data_bucket
}

# resource "aws_glue_job" "example" {
#   name     = "extract_data"
#   role_arn = aws_iam_role.example.arn

#   command {
#     script_location = "s3://${aws_s3_bucket.example.bucket}/example.py"
#   }
# }
