resource "aws_s3_object" "glue_job_extract_fred_api" {
  bucket = aws_s3_bucket.scripts.id
  key    = "extract_fred_data.py"
  source = "${path.root}/../../../scripts/extract_jobs/extract_fred_data.py"
  etag = filemd5("${path.root}/../../../scripts/extract_jobs/extract_fred_data.py")
}

resource "aws_s3_object" "glue_job_extract_range_fred_api" {
  bucket = aws_s3_bucket.scripts.id
  key    = "extract_range_fred_data.py"
  source = "${path.root}/../../../scripts/extract_range_fred_data.py"
  etag = filemd5("${path.root}/../../../scripts/extract_range_fred_data.py")
}
