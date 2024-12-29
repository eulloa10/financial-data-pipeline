data "aws_caller_identity" "current" {}

data "aws_iam_policy_document" "terraform_policy" {
  statement {
    sid = "S3FullAccess"
    actions = [
      "s3:CreateBucket",
      "s3:DeleteBucket",
      "s3:PutObject",
      "s3:GetObject",
      "s3:ListBucket",
      "s3:PutBucketPolicy",
      "s3:GetBucketPolicy",
    ]
    resources = [
      "arn:aws:s3:::${var.glue_scripts_bucket}",
      "arn:aws:s3:::${var.glue_scripts_bucket}/*",
      "arn:aws:s3:::${var.fred_data_bucket}",
      "arn:aws:s3:::${var.fred_data_bucket}/*",
    ]
  }

  statement {
    sid = "GlueFullAccess"
    actions = [
      "glue:CreateJob",
      "glue:DeleteJob",
      "glue:GetJob",
      "glue:UpdateJob",
      "glue:StartJobRun",
      "glue:GetJobRun",
    ]
    resources = [
      "arn:aws:glue:*:${data.aws_caller_identity.current.account_id}:job/extract_fred_data_job",
    ]
  }

  statement {
    sid = "IAMPassRole"
    actions = [
      "iam:PassRole"
    ]
    resources = [
      aws_iam_role.glue_job_role.arn
    ]
    condition {
      test     = "StringEquals"
      variable = "iam:PassedToService"
      values   = ["glue.amazonaws.com"]
    }
  }
}
