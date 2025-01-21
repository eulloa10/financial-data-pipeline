resource "aws_s3_object" "glue_job_extract_fred_api" {
  bucket = "${var.project}-${var.glue_scripts_bucket}"
  key    = "extract_fred_data_v2.py"
  source = "${path.root}/modules/glue/scripts/extract_jobs/extract_fred_data.py"
  etag = filemd5("${path.root}/modules/glue/scripts/extract_jobs/extract_fred_data.py")
}
