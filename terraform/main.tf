# # S3 Bucket for Glue Job Scripts
resource "aws_s3_bucket" "fred_glue_scripts_bucket" {
  bucket = "fred-glue-scripts"
}

# IAM Role for Glue Job Execution
resource "aws_iam_role" "fred_glue_role" {
  name = "fred_glue-job-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "glue.amazonaws.com"
        }
      }
    ]
  })
}

# IAM Policy Attachment for Glue Job Role to Access S3
resource "aws_iam_role_policy_attachment" "glue_s3_access" {
  policy_arn = "arn:aws:iam::aws:policy/AmazonS3FullAccess"
  role       = aws_iam_role.glue_role.name
}
