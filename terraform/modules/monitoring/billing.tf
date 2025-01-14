# SNS Topic for billing alerts
resource "aws_sns_topic" "billing_alert" {
  name = "${var.project}-billing-alert"
}

# SNS Topic subscription (for email notifications)
resource "aws_sns_topic_subscription" "billing_alert_email" {
  topic_arn = aws_sns_topic.billing_alert.arn
  protocol  = "email"
  endpoint  = var.alert_email
}

# CloudWatch billing alarm
resource "aws_cloudwatch_metric_alarm" "billing_alarm" {
  alarm_name          = "${var.project}-billing-alarm"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = "1"
  metric_name         = "EstimatedCharges"
  namespace          = "AWS/Billing"
  period             = "21600"  # 6 hours
  statistic          = "Maximum"
  threshold          = "10"      # $10 USD
  alarm_description  = "Billing alarm when charges exceed $10"
  alarm_actions      = [aws_sns_topic.billing_alert.arn]

  dimensions = {
    Currency = "USD"
  }
}

# AWS Budget
resource "aws_budgets_budget" "cost" {
  name              = "${var.project}-monthly-budget"
  budget_type       = "COST"
  limit_amount      = "10"
  limit_unit        = "USD"
  time_unit         = "MONTHLY"
  time_period_start = formatdate("YYYY-MM-01_12:00", timestamp())

  notification {
    comparison_operator        = "GREATER_THAN"
    threshold                 = 80
    threshold_type            = "PERCENTAGE"
    notification_type         = "ACTUAL"
    subscriber_email_addresses = [var.alert_email]
  }
}
