#!/bin/bash

# Get the module directory
MODULE_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )/.." && pwd )"

# Sync DAGs to S3
aws s3 sync ${MODULE_DIR}/dags/ s3://${1}/dags/

echo "DAGs synced to S3 bucket: ${1}"
