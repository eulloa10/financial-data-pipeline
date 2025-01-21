resource "aws_s3_object" "glue_job_aggregate_fred_data" {
  bucket = "${var.project}-${var.glue_scripts_bucket}"
  key    = "aggregate_fred_data.py"
  source = "${path.root}/modules/glue/scripts/aggregate_jobs/aggregate_fred_data.py"
  etag = filemd5("${path.root}/modules/glue/scripts/aggregate_jobs/aggregate_fred_data.py")
}
