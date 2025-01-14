resource "aws_iam_role_policy" "airflow_s3" {
  name = "${var.project}-airflow-s3-policy"
  role = aws_iam_role.airflow.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "s3:GetObject",
          "s3:ListBucket"
        ]
        Resource = [
          aws_s3_bucket.airflow_dags.arn,
          "${aws_s3_bucket.airflow_dags.arn}/*"
        ]
      }
    ]
  })
}
