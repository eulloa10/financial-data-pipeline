# modules/rds/variables.tf

variable "project" {
  description = "Project name"
  type        = string
}

variable "environment" {
  description = "Environment name"
  type        = string
}

variable "region" {
  description = "AWS region"
  type        = string
}

variable "vpc_id" {
  description = "VPC ID where RDS will be deployed"
  type        = string
}

variable "private_subnet_ids" {
  description = "List of private subnet IDs for RDS"
  type        = list(string)
}

variable "glue_security_group_id" {
  description = "Security group ID of Glue jobs"
  type        = string
}

variable "airflow_security_group_id" {
  description = "Security group ID of Airflow EC2 instance"
  type        = string
}

variable "instance_class" {
  description = "RDS instance class"
  type        = string
  default     = "db.t3.micro"
}

variable "allocated_storage" {
  description = "Allocated storage in GB"
  type        = number
  default     = 20
}

variable "max_allocated_storage" {
  description = "Maximum allocated storage in GB for autoscaling"
  type        = number
  default     = 100
}

variable "db_name" {
  description = "Name of the database to create"
  type        = string
}

variable "db_username" {
  description = "Username for the database"
  type        = string
  sensitive   = true
}

variable "db_password" {
  description = "Password for the database"
  type        = string
  sensitive   = true
}

variable "backup_retention_period" {
  description = "Number of days to retain backups"
  type        = number
  default     = 7
}

variable "backup_window" {
  description = "Preferred backup window"
  type        = string
  default     = "03:00-04:00"  # UTC
}

variable "maintenance_window" {
  description = "Preferred maintenance window"
  type        = string
  default     = "Mon:04:00-Mon:05:00"  # UTC
}

variable "multi_az" {
  description = "Whether to deploy RDS in multiple availability zones"
  type        = bool
  default     = false
}

variable "deletion_protection" {
  description = "Whether to enable deletion protection"
  type        = bool
  default     = true
}

variable "skip_final_snapshot" {
  description = "Whether to skip final snapshot when destroying database"
  type        = bool
  default     = false
}

variable "engine_version" {
  description = "PostgreSQL engine version"
  type        = string
  default     = "14.15"
}

variable "parameter_group_family" {
  description = "Family of the DB parameter group"
  type        = string
  default     = "postgres14"
}

variable "monitoring_interval" {
  description = "Monitoring interval in seconds (0 to disable enhanced monitoring)"
  type        = number
  default     = 60
}

variable "performance_insights_enabled" {
  description = "Whether to enable Performance Insights"
  type        = bool
  default     = true
}

variable "performance_insights_retention_period" {
  description = "Performance Insights retention period in days"
  type        = number
  default     = 7
}

variable "enabled_cloudwatch_logs_exports" {
  description = "List of log types to enable for exporting to CloudWatch logs"
  type        = list(string)
  default     = ["postgresql", "upgrade"]
}

variable "auto_minor_version_upgrade" {
  description = "Whether to automatically upgrade minor versions"
  type        = bool
  default     = true
}


variable "allow_major_version_upgrade" {
  description = "Whether to allow major version upgrades"
  type        = bool
  default     = false
}


variable "apply_immediately" {
  description = "Whether to apply changes immediately or during maintenance window"
  type        = bool
  default     = false
}


variable "storage_encrypted" {
  description = "Whether to encrypt the storage"
  type        = bool
  default     = true
}


variable "copy_tags_to_snapshot" {
  description = "Whether to copy tags to snapshots"
  type        = bool
  default     = true
}


variable "tags" {
  description = "Additional tags for RDS resources"
  type        = map(string)
  default     = {}
}


variable "additional_security_group_ids" {
  description = "List of additional security group IDs to attach to RDS"
  type        = list(string)
  default     = []
}


variable "parameter_group_parameters" {
  description = "Map of parameters to add to the DB parameter group"
  type        = map(string)
  default     = {}
}


variable "subnet_group_name_prefix" {
  description = "Prefix for the DB subnet group name"
  type        = string
  default     = null
}


variable "port" {
  description = "The port on which the DB accepts connections"
  type        = number
  default     = 5432
}

variable "alert_email" {
  description = "Email address to receive RDS alerts"
  type        = string
}
