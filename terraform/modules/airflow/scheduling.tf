# Get current AWS account ID
data "aws_caller_identity" "current" {}

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

  tags = var.tags
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
          "ssm:SendCommand",
          "ssm:StartSession",
          "ssm:GetCommandInvocation"
        ]
        Resource = "*"
      },
      {
        Effect = "Allow"
        Action = [
          "ec2:StartInstances",
          "ec2:StopInstances"
        ]
        Resource = aws_instance.airflow_ec2.arn
      },
      {
        Effect = "Allow"
        Action = [
          "ssm:DescribeAutomationExecutions",
          "ssm:GetAutomationExecution"
        ]
        Resource = "*"
      }
    ]
  })
}

# CloudWatch Event Rule to Start EC2 Instance
resource "aws_cloudwatch_event_rule" "start_instance" {
  name                = "${var.project}-start-instance"
  description         = "Start EC2 instance before Wednesday DAG run (4 PM PST)"
  schedule_expression = "cron(0 0 ? * THU *)"  # Thursday 12:00 AM UTC (Wednesday 4:00 PM PST)

  tags = var.tags
}

# CloudWatch Event Target to Start EC2 Instance
resource "aws_cloudwatch_event_target" "start_instance" {
  rule      = aws_cloudwatch_event_rule.start_instance.name
  target_id = "StartEC2Instance"
  role_arn  = aws_iam_role.eventbridge_role.arn

  arn = "arn:aws:ssm:${var.region}:${data.aws_caller_identity.current.account_id}:automation-definition/AWS-StartEC2Instance"

  input = jsonencode({
    InstanceId = [aws_instance.airflow_ec2.id]
  })
}

# CloudWatch Event Rule to Stop EC2 Instance
resource "aws_cloudwatch_event_rule" "stop_instance" {
  name                = "${var.project}-stop-instance"
  description         = "Stop EC2 instance after DAGs complete (10 PM PST)"
  schedule_expression = "cron(0 6 ? * THU *)"  # Thursday 6:00 AM UTC (Wednesday 10:00 PM PST)

  tags = var.tags
}

# CloudWatch Event Target to Stop EC2 Instance
resource "aws_cloudwatch_event_target" "stop_instance" {
  rule      = aws_cloudwatch_event_rule.stop_instance.name
  target_id = "StopEC2Instance"
  role_arn  = aws_iam_role.eventbridge_role.arn

  arn = "arn:aws:ssm:${var.region}:${data.aws_caller_identity.current.account_id}:automation-definition/AWS-StopEC2Instance"

  input = jsonencode({
    InstanceId = [aws_instance.airflow_ec2.id]
  })
}
