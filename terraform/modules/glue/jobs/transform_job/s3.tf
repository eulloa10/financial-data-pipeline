resource "aws_s3_object" "glue_job_transform_fred_api" {
  bucket = var.glue_scripts_bucket
  key    = "transform_fred_data.py"
  source = "${path.root}/modules/glue/scripts/transform_jobs/transform_fred_data.py"
  etag = filemd5("${path.root}/modules/glue/scripts/transform_jobs/transform_fred_data.py")
}
