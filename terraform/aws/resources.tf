resource "aws_s3_bucket" "fred_glue_scripts_bucket" {
  bucket = var.glue_scripts_bucket
}

resource "aws_s3_bucket" "fred_data_bucket" {
  bucket = var.fred_data_bucket
}

resource "aws_s3_object" "extract_script" {
  bucket = var.glue_scripts_bucket
  key    = "extract/extract_fred_data.py"
  source = "./assets/extract_jobs/extract_fred_data.py"
  etag = filemd5("./assets/extract_jobs/extract_fred_data.py")
}

# resource "aws_glue_job" "extract_fred_data_job" {
#   name     = "extract_fred_data_job"
#   role_arn = aws_iam_role.glue_job_role.arn
#   glue_version = var.glue_version
#   number_of_workers = var.number_of_workers
#   worker_type = var.worker_type

#   command {
#     script_location = "s3://${var.glue_scripts_bucket}/extract/extract_fred_data.py"
#   }
# }

# resource "aws_s3_object" "transform_glue_scripts" {
#   for_each = var.transform_glue_scripts

#   bucket = var.glue_scripts_bucket
#   key    = "${each.value.type}/${each.value.filename}" # Construct the S3 key
#   source = "./assets/${each.value.type}/${each.value.filename}" # Construct the local path
#   etag = filemd5("./assets/${each.value.type}/${each.value.filename}")
# }
