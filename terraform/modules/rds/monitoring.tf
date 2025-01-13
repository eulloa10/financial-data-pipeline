# SNS Topic for RDS notifications
resource "aws_sns_topic" "rds_events" {
  name = "${var.project}-rds-events"
}

# SNS Topic subscription for email notifications
resource "aws_sns_topic_subscription" "rds_events_email" {
  topic_arn = aws_sns_topic.rds_events.arn
  protocol  = "email"
  endpoint  = var.alert_email
}

# CloudWatch Event Rule for RDS state changes
resource "aws_cloudwatch_event_rule" "rds_state_change" {
  name        = "${var.project}-rds-state-change"
  description = "Capture RDS state changes"

  event_pattern = jsonencode({
    source      = ["aws.rds"]
    detail-type = ["RDS DB Instance Event"]
    detail = {
      SourceIdentifier = [aws_db_instance.fred.id]
      EventCategories = [
        "availability",
        "failure"
      ]
    }
  })

  tags = {
    Name        = "${var.project}-rds-state-change"
    Environment = var.environment
  }
}

# CloudWatch Event Target for RDS state changes
resource "aws_cloudwatch_event_target" "rds_state_change" {
  rule      = aws_cloudwatch_event_rule.rds_state_change.name
  target_id = "SendToSNS"
  arn       = aws_sns_topic.rds_events.arn

  input_transformer {
    input_paths = {
      instance = "$.detail.SourceIdentifier"
      status   = "$.detail.Message"
      time     = "$.time"
    }
    input_template = "\"RDS Instance <instance> status update at <time>: <status>\""
  }
}

# CloudWatch Alarms for monitoring RDS status
resource "aws_cloudwatch_metric_alarm" "rds_status_check" {
  alarm_name          = "${var.project}-rds-status"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = "1"
  metric_name         = "StatusCheckFailed"
  namespace          = "AWS/RDS"
  period             = "60"
  statistic          = "Maximum"
  threshold          = "0"
  alarm_description  = "This metric monitors RDS instance status"
  alarm_actions      = [aws_sns_topic.rds_events.arn]

  dimensions = {
    DBInstanceIdentifier = aws_db_instance.fred.id
  }
}

# CloudWatch Alarm for startup time
resource "aws_cloudwatch_metric_alarm" "rds_startup_time" {
  alarm_name          = "${var.project}-rds-startup-time"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = "1"
  metric_name         = "EngineUptime"
  namespace          = "AWS/RDS"
  period             = "300"  # 5 minutes
  statistic          = "Minimum"
  threshold          = "600"  # 10 minutes
  alarm_description  = "Alert if RDS takes too long to start"
  alarm_actions      = [aws_sns_topic.rds_events.arn]

  dimensions = {
    DBInstanceIdentifier = aws_db_instance.fred.id
  }
}

# CloudWatch Dashboard for RDS monitoring
resource "aws_cloudwatch_dashboard" "rds" {
  dashboard_name = "${var.project}-rds-monitoring"

  dashboard_body = jsonencode({
    widgets = [
      {
        type   = "metric"
        x      = 0
        y      = 0
        width  = 12
        height = 6
        properties = {
          metrics = [
            ["AWS/RDS", "CPUUtilization", "DBInstanceIdentifier", aws_db_instance.fred.id],
            [".", "DatabaseConnections", ".", "."],
            [".", "FreeStorageSpace", ".", "."]
          ]
          period = 300
          stat   = "Average"
          region = var.region
          title  = "RDS Metrics"
        }
      },
      {
        type   = "metric"
        x      = 12
        y      = 0
        width  = 12
        height = 6
        properties = {
          metrics = [
            ["AWS/RDS", "EngineUptime", "DBInstanceIdentifier", aws_db_instance.fred.id]
          ]
          period = 300
          stat   = "Minimum"
          region = var.region
          title  = "RDS Uptime"
        }
      }
    ]
  })
}
