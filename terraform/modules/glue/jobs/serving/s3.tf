resource "aws_s3_object" "glue_job_load_fred_data" {
  bucket = "${var.project}-${var.glue_scripts_bucket}"
  key    = "load_fred_data.py"
  source = "${path.root}/modules/glue/scripts/serving_jobs/load_fred_data.py"
  etag = filemd5("${path.root}/modules/glue/scripts/serving_jobs/load_fred_data.py")
}
