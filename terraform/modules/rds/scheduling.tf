data "aws_caller_identity" "current" {}

# Start RDS instance at 6 AM PST (1 PM UTC)
resource "aws_cloudwatch_event_rule" "start_rds" {
  name                = "${var.project}-start-rds"
  description         = "Start RDS instance at 6 AM PST"
  schedule_expression = "cron(0 13 * * ? *)"  # 1 PM UTC = 6 AM PST

  tags = {
    Name        = "${var.project}-start-rds"
    Environment = var.environment
  }
}

resource "aws_cloudwatch_event_target" "start_rds" {
  rule      = aws_cloudwatch_event_rule.start_rds.name
  target_id = "StartRDSInstance"
  arn       = "arn:aws:ssm:${var.region}:${data.aws_caller_identity.current.account_id}:automation-definition/AWS-StartRDSInstance"
  role_arn  = aws_iam_role.eventbridge_role.arn

  input = jsonencode({
    InstanceId = aws_db_instance.fred.id
  })
}

# Stop RDS instance at 12 AM PST (8 AM UTC)
resource "aws_cloudwatch_event_rule" "stop_rds" {
  name                = "${var.project}-stop-rds"
  description         = "Stop RDS instance at 12 AM PST"
  schedule_expression = "cron(0 8 * * ? *)"  # 8 AM UTC = 12 AM PST

  tags = {
    Name        = "${var.project}-stop-rds"
    Environment = var.environment
  }
}

resource "aws_cloudwatch_event_target" "stop_rds" {
  rule      = aws_cloudwatch_event_rule.stop_rds.name
  target_id = "StopRDSInstance"
  arn       = "arn:aws:ssm:${var.region}:${data.aws_caller_identity.current.account_id}:automation-definition/AWS-StopRDSInstance:$LATEST"
  role_arn  = aws_iam_role.eventbridge_role.arn

  input = jsonencode({
    InstanceId = aws_db_instance.fred.id
  })
}

resource "aws_iam_role" "eventbridge_role" {
  name = "${var.project}-rds-eventbridge-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "events.amazonaws.com"
        }
      }
    ]
  })
}

resource "aws_iam_role_policy" "eventbridge_policy" {
  name = "${var.project}-rds-eventbridge-policy"
  role = aws_iam_role.eventbridge_role.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "rds:StartDBInstance",
          "rds:StopDBInstance",
          "rds:DescribeDBInstances"
        ]
        Resource = aws_db_instance.fred.arn
      }
    ]
  })
}
