# Get current AWS account ID
data "aws_caller_identity" "current" {}

# Start instance Wednesday (1 hour before DAG run)
resource "aws_cloudwatch_event_rule" "start_instance" {
  name                = "${var.project}-start-instance"
  description         = "Start EC2 instance before Wednesday DAG runs (4 PM PST)"
  schedule_expression = "cron(0 0 ? * THU *)"  # Thursday 12:00 AM UTC (Wednesday 4:00 PM PST)

  tags = {
    Name        = "${var.project}-start-instance"
    Environment = var.environment
  }
}

resource "aws_cloudwatch_event_target" "start_instance" {
  rule      = aws_cloudwatch_event_rule.start_instance.name
  target_id = "StartEC2Instance"
  arn       = "arn:aws:ssm:${var.region}:${data.aws_caller_identity.current.account_id}:automation-definition/AWS-StartEC2Instance"
  role_arn  = aws_iam_role.eventbridge_role.arn

  input = jsonencode({
    InstanceId = [aws_instance.airflow.id]
  })
}

# Stop instance Thursday morning
resource "aws_cloudwatch_event_rule" "stop_instance" {
  name                = "${var.project}-stop-instance"
  description         = "Stop EC2 instance after DAGs complete"
  schedule_expression = "cron(0 6 ? * THU *)"  # Thursday 6:00 AM UTC (Wednesday 10:00 PM PST)

  tags = {
    Name        = "${var.project}-stop-instance"
    Environment = var.environment
  }
}

resource "aws_cloudwatch_event_target" "stop_instance" {
  rule      = aws_cloudwatch_event_rule.stop_instance.name
  target_id = "StopEC2Instance"
  arn       = "arn:aws:ssm:${var.region}:${data.aws_caller_identity.current.account_id}:automation-definition/AWS-StopEC2Instance"
  role_arn  = aws_iam_role.eventbridge_role.arn

  input = jsonencode({
    InstanceId = [aws_instance.airflow.id]
  })
}

# IAM role for EventBridge
resource "aws_iam_role" "eventbridge_role" {
  name = "${var.project}-eventbridge-role"

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

# IAM policy for EventBridge to control EC2
resource "aws_iam_role_policy" "eventbridge_policy" {
  name = "${var.project}-eventbridge-policy"
  role = aws_iam_role.eventbridge_role.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "ec2:StartInstances",
          "ec2:StopInstances"
        ]
        Resource = aws_instance.airflow.arn
      }
    ]
  })
}
