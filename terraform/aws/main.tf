# resource "aws_s3_bucket" "fred_glue_scripts_bucket" {
#   bucket = var.glue_scripts_bucket
# }

# resource "aws_s3_bucket" "fred_data_bucket" {
#   bucket = var.fred_data_bucket
# }

# module "extract_fred_data_DGS10" {
#   source = "./modules/extract_job"
#   # ... other configurations
#   job_name = "extract_dgs10_data"
#   script_key = "extract_fred.py"
#   default_arguments = {
#     "--fred_api_key"  = var.fred_api_key
#     "--fred_series_id" = "DGS10"
#     "--s3_bucket"     = aws_s3_bucket.fred_data_bucket.bucket
#     "--indicator_name" = "DGS10"
#   }
# }

# module "extract_fred_data_EFFR" {
#     source = "./modules/extract_job"
#     # ... other configurations
#     job_name = "extract_EFFR_data"
#     script_key = "extract_fred.py"
#     default_arguments = {
#         "--fred_api_key" = var.fred_api_key
#         "--fred_series_id" = "EFFR"
#         "--s3_bucket" = aws_s3_bucket.fred_data_bucket.bucket
#         "--indicator_name" = "EFFR"
#     }
# }

# module "extract_fred_data_CSUSHPINSA" {
#     source = "./modules/extract_job"
#     # ... other configurations
#     job_name = "extract_CSUSHPINSA_data"
#     script_key = "extract_fred.py"
#     default_arguments = {
#         "--fred_api_key" = var.fred_api_key
#         "--fred_series_id" = "CSUSHPINSA"
#         "--s3_bucket" = aws_s3_bucket.fred_data_bucket.bucket
#         "--indicator_name" = "CSUSHPINSA"
#     }
# }

# module "extract_fred_data_UNRATE" {
#     source = "./modules/extract_job"
#     # ... other configurations
#     job_name = "extract_UNRATE_data"
#     script_key = "extract_fred.py"
#     default_arguments = {
#         "--fred_api_key" = var.fred_api_key
#         "--fred_series_id" = "UNRATE"
#         "--s3_bucket" = aws_s3_bucket.fred_data_bucket.bucket
#         "--indicator_name" = "UNRATE"
#     }
# }

# module "extract_fred_data_CPIAUCSL" {
#     source = "./modules/extract_job"
#     # ... other configurations
#     job_name = "extract_CPIAUCSL_data"
#     script_key = "extract_fred.py"
#     default_arguments = {
#         "--fred_api_key" = var.fred_api_key
#         "--fred_series_id" = "CPIAUCSL"
#         "--s3_bucket" = aws_s3_bucket.fred_data_bucket.bucket
#         "--indicator_name" = "CPIAUCSL"
#     }
# }

# module "extract_fred_data_PCE" {
#     source = "./modules/extract_job"
#     # ... other configurations
#     job_name = "extract_PCE_data"
#     script_key = "extract_fred.py"
#     default_arguments = {
#         "--fred_api_key" = var.fred_api_key
#         "--fred_series_id" = "PCE"
#         "--s3_bucket" = aws_s3_bucket.fred_data_bucket.bucket
#         "--indicator_name" = "PCE"
#     }
# }

# module "extract_fred_data_JTSJOL" {
#     source = "./modules/extract_job"
#     # ... other configurations
#     job_name = "extract_JTSJOL_data"
#     script_key = "extract_fred.py"
#     default_arguments = {
#         "--fred_api_key" = var.fred_api_key
#         "--fred_series_id" = "JTSJOL"
#         "--s3_bucket" = aws_s3_bucket.fred_data_bucket.bucket
#         "--indicator_name" = "JTSJOL"
#     }
# }

# module "extract_fred_data_JTSHIR" {
#     source = "./modules/extract_job"
#     # ... other configurations
#     job_name = "extract_JTSHIR_data"
#     script_key = "extract_fred.py"
#     default_arguments = {
#         "--fred_api_key" = var.fred_api_key
#         "--fred_series_id" = "JTSHIR"
#         "--s3_bucket" = aws_s3_bucket.fred_data_bucket.bucket
#         "--indicator_name" = "JTSHIR"
#     }
# }

# module "extract_fred_data_JTSTSR" {
#     source = "./modules/extract_job"
#     # ... other configurations
#     job_name = "extract_JTSTSR_data"
#     script_key = "extract_fred.py"
#     default_arguments = {
#         "--fred_api_key" = var.fred_api_key
#         "--fred_series_id" = "JTSTSR"
#         "--s3_bucket" = aws_s3_bucket.fred_data_bucket.bucket
#         "--indicator_name" = "JTSTSR"
#     }
# }

# module "extract_fred_data_PSAVERT" {
#     source = "./modules/extract_job"
#     # ... other configurations
#     job_name = "extract_PSAVERT_data"
#     script_key = "extract_fred.py"
#     default_arguments = {
#         "--fred_api_key" = var.fred_api_key
#         "--fred_series_id" = "PSAVERT"
#         "--s3_bucket" = aws_s3_bucket.fred_data_bucket.bucket
#         "--indicator_name" = "PSAVERT"
#     }
# }

# module "extract_fred_data_CSCICP03USM665S" {
#     source = "./modules/extract_job"
#     # ... other configurations
#     job_name = "extract_CSCICP03USM665S_data"
#     script_key = "extract_fred.py"
#     default_arguments = {
#         "--fred_api_key" = var.fred_api_key
#         "--fred_series_id" = "CSCICP03USM665S"
#         "--s3_bucket" = aws_s3_bucket.fred_data_bucket.bucket
#         "--indicator_name" = "CSCICP03USM665S"
#     }
# }

# resource "aws_glue_job" "example" {
#   name     = "extract_data"
#   role_arn = aws_iam_role.example.arn

#   command {
#     script_location = "s3://${aws_s3_bucket.example.bucket}/example.py"
#   }
# }
