resource "aws_s3_object" "glue_job_aggregate_fred_data" {
  bucket = var.glue_scripts_bucket
  key    = "aggregate_fred_data.py"
  source = "${path.root}/../../../scripts/aggregate_jobs/aggregate_fred_data.py"
  etag = filemd5("${path.root}/../../../scripts/aggregate_jobs/aggregate_fred_data.py")
}

resource "aws_s3_object" "glue_job_aggregate_month_fred_data" {
  bucket = var.glue_scripts_bucket
  key    = "aggregate_month_fred_data.py"
  source = "${path.root}/../../../scripts/aggregate_jobs/aggregate_month_fred_data.py"
  etag = filemd5("${path.root}/../../../scripts/aggregate_jobs/aggregate_month_fred_data.py")
}
