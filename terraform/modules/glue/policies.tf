data "aws_caller_identity" "current" {}
data "aws_region" "current" {}

data "aws_iam_policy_document" "glue_base_policy" {
  statement {
    sid    = "AllowGlueToAssumeRole"
    effect = "Allow"

    principals {
      identifiers = ["glue.amazonaws.com"]
      type        = "Service"
    }

    actions = ["sts:AssumeRole"]
  }
}

data "aws_iam_policy_document" "glue_access_policy" {
  # S3 Access
  statement {
    sid    = "AllowS3Access"
    effect = "Allow"
    actions = [
      "s3:GetObject",
      "s3:PutObject",
      "s3:DeleteObject",
      "s3:ListBucket"
    ]
    resources = [
      aws_s3_bucket.data_lake.arn,
      "${aws_s3_bucket.data_lake.arn}/*",
      aws_s3_bucket.scripts.arn,
      "${aws_s3_bucket.scripts.arn}/*"
    ]
  }

  # Glue Service Access
  statement {
    sid    = "AllowGlueServiceAccess"
    effect = "Allow"
    actions = [
      "glue:*Database*",
      "glue:*Table*",
      "glue:*Partition*",
      "glue:*Crawler*",
      "glue:*Classification*",
      "glue:*Connection*",
      "glue:*Job*"
    ]
    resources = [
      "arn:aws:glue:${data.aws_region.current.name}:${data.aws_caller_identity.current.account_id}:catalog",
      "arn:aws:glue:${data.aws_region.current.name}:${data.aws_caller_identity.current.account_id}:database/*",
      "arn:aws:glue:${data.aws_region.current.name}:${data.aws_caller_identity.current.account_id}:table/*",
      "arn:aws:glue:${data.aws_region.current.name}:${data.aws_caller_identity.current.account_id}:connection/*"
    ]
  }

  # CloudWatch Logs Access
  statement {
    sid    = "AllowCloudWatchLogsAccess"
    effect = "Allow"
    actions = [
      "logs:CreateLogGroup",
      "logs:CreateLogStream",
      "logs:PutLogEvents",
      "logs:GetLogEvents",
      "logs:GetLogGroupFields"
    ]
    resources = [
      "arn:aws:logs:${data.aws_region.current.name}:${data.aws_caller_identity.current.account_id}:log-group:/aws-glue/*"
    ]
  }

  # CloudWatch Metrics Access
  statement {
    sid    = "AllowCloudWatchMetricsAccess"
    effect = "Allow"
    actions = [
      "cloudwatch:PutMetricData"
    ]
    resources = ["*"]
    condition {
      test     = "StringEquals"
      variable = "cloudwatch:namespace"
      values   = ["AWS/Glue"]
    }
  }

  # EC2 Network Interface Access (for VPC connectivity)
  statement {
    sid    = "AllowEC2NetworkAccess"
    effect = "Allow"
    actions = [
      "ec2:CreateNetworkInterface",
      "ec2:DeleteNetworkInterface",
      "ec2:DescribeNetworkInterfaces",
      "ec2:DescribeSecurityGroups",
      "ec2:DescribeSubnets",
      "ec2:DescribeVpcEndpoints",
      "ec2:DescribeVpcs"
    ]
    resources = ["*"]
  }

  # RDS Access (if needed for your load job)
  statement {
    sid    = "AllowRDSAccess"
    effect = "Allow"
    actions = [
      "rds-db:connect",
      "rds:DescribeDBInstances",
      "rds:DescribeDBClusters",
      "rds:DescribeDBEngineVersions",
      "rds:ModifyDBInstance",
      "rds:CreateDBInstance",
      "rds:DeleteDBInstance",
      "rds:RebootDBInstance",
      "rds:StartDBInstance",
      "rds:StopDBInstance",
      "rds:ListTagsForResource",
      "rds:AddTagsToResource"
    ]
    resources = [
      "arn:aws:rds:${data.aws_region.current.name}:${data.aws_caller_identity.current.account_id}:db:${var.project}-*"
    ]
  }

  statement {
    sid    = "AllowRDSSecretAccess"
    effect = "Allow"
    actions = [
      "secretsmanager:GetSecretValue",
      "secretsmanager:DescribeSecret"
    ]

    resources = [
      "arn:aws:secretsmanager:${data.aws_region.current.name}:${data.aws_caller_identity.current.account_id}:secret:${var.project}/rds-*"
    ]
  }


  # CloudTrail Access (limited to describe actions)
  statement {
    sid    = "AllowCloudTrailAccess"
    effect = "Allow"
    actions = [
      "cloudtrail:DescribeTrails",
      "cloudtrail:GetTrailStatus"
    ]
    resources = [
      "arn:aws:cloudtrail:${data.aws_region.current.name}:${data.aws_caller_identity.current.account_id}:trail/*"
    ]
  }
}

# Optional: Additional policy for Secrets Manager if you're storing sensitive values
data "aws_iam_policy_document" "secrets_access_policy" {
  statement {
    sid    = "AllowSecretsAccess"
    effect = "Allow"
    actions = [
      "secretsmanager:GetSecretValue"
    ]
    resources = [
      "arn:aws:secretsmanager:${data.aws_region.current.name}:${data.aws_caller_identity.current.account_id}:secret:${var.project}-*"
    ]
  }
}

# data "aws_iam_policy_document" "glue_base_policy" {
#   statement {
#     sid    = "AllowGlueToAssumeRole"
#     effect = "Allow"

#     principals {
#       identifiers = ["glue.amazonaws.com"]
#       type        = "Service"
#     }

#     actions = ["sts:AssumeRole"]
#   }
# }

# data "aws_iam_policy_document" "glue_access_policy" {
#   statement {
#     sid    = "AllowGlueAccess"
#     effect = "Allow"
#     actions = [
#       "s3:*",
#       "glue:*",
#       "iam:*",
#       "logs:*",
#       "cloudwatch:*",
#       "sqs:*",
#       "ec2:*",
#       "rds:*",
#       "cloudtrail:*"
#     ]
#     resources = [
#       "*",
#     ]
#   }
# }
