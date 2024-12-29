resource "aws_s3_bucket" "data_lake" {
  bucket = "${var.project}-${var.data_lake_name}"
}
resource "aws_s3_bucket" "scripts" {
  bucket = "${var.project}-${var.glue_scripts_bucket}"
}

resource "aws_s3_bucket_public_access_block" "scripts" {
  bucket = aws_s3_bucket.scripts.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_s3_object" "glue_job_extract_fred_api" {
  bucket = aws_s3_bucket.scripts.id
  key    = "extract_fred_data.py"
  source = "${path.root}/assets/extract_jobs/extract_fred_data.py"
  etag = filemd5("${path.root}/assets/extract_jobs/extract_fred_data.py")
}
