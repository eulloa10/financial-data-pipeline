resource "aws_s3_object" "glue_job_transform_fred_api" {
  bucket = aws_s3_bucket.scripts.id
  key    = "transform_fred_data.py"
  source = "${path.root}/assets/transform_jobs/transform_fred_data.py"
  etag = filemd5("${path.root}/assets/transform_jobs/transform_fred_data.py")
}
