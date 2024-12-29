resource "aws_iam_user" "terraform_user" {
  name = "terraform_user"
}

resource "aws_iam_policy" "terraform_policy" {
  name        = "TerraformGlueS3Policy"
  description = "Policy for Terraform to create Glue and S3 resources"
  policy      = data.aws_iam_policy_document.terraform_policy.json
}

resource "aws_iam_user_policy_attachment" "terraform_user_policy" {
  user       = aws_iam_user.terraform_user.name
  policy_arn = aws_iam_policy.terraform_policy.arn
}

resource "aws_iam_role" "glue_job_role" {
  name = "glue_job_role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17",
    Statement = [
      {
        Effect = "Allow",
        Principal = {
          Service = "glue.amazonaws.com"
        },
        Action = "sts:AssumeRole"
      }
    ]
  })
}
