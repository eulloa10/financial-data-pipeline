#!/bin/bash

# Update system packages
yum update -y
yum install -y docker git python3-pip

# Start and enable Docker
systemctl start docker
systemctl enable docker
usermod -aG docker ec2-user

# Install Docker Compose
curl -L "https://github.com/docker/compose/releases/download/v2.20.0/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
chmod +x /usr/local/bin/docker-compose

# Install AWS CLI
curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
unzip awscliv2.zip
./aws/install

# Create Airflow directory structure
mkdir -p /home/ec2-user/airflow/{dags,logs,plugins}
cd /home/ec2-user/airflow

# Create S3 sync script for DAGs
cat > /home/ec2-user/sync_dags.sh << 'EOF'
#!/bin/bash
aws s3 sync s3://${dags_bucket}/dags /home/ec2-user/airflow/dags
EOF

chmod +x /home/ec2-user/sync_dags.sh

# Add S3 sync to crontab (sync every minute)
(crontab -l 2>/dev/null; echo "* * * * * /home/ec2-user/sync_dags.sh") | crontab -

# Initial sync of DAGs
/home/ec2-user/sync_dags.sh

# Create docker-compose.yml
cat > docker-compose.yml << 'EOF'
${docker_compose_content}
EOF

# Set correct permissions
chown -R ec2-user:ec2-user /home/ec2-user/airflow

# Create a script to start Airflow services
cat > /home/ec2-user/start-airflow.sh << 'EOF'
#!/bin/bash
cd /home/ec2-user/airflow
docker-compose up -d
EOF

chmod +x /home/ec2-user/start-airflow.sh

# Start Airflow
/home/ec2-user/start-airflow.sh

# Add CloudWatch agent
yum install -y amazon-cloudwatch-agent

# Create a backup script
cat > /home/ec2-user/backup.sh << 'EOF'
#!/bin/bash
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/home/ec2-user/airflow/backups"

# Create backup directory if it doesn't exist
mkdir -p $BACKUP_DIR

# Backup DAGs to S3
aws s3 sync /home/ec2-user/airflow/dags s3://${dags_bucket}/backups/dags_$TIMESTAMP/

# Backup Airflow database
docker-compose exec -T postgres pg_dump -U airflow airflow > $BACKUP_DIR/airflow_db_$TIMESTAMP.sql

# Upload database backup to S3
aws s3 cp $BACKUP_DIR/airflow_db_$TIMESTAMP.sql s3://${dags_bucket}/backups/

# Clean up local backups (keep last 7 days)
find $BACKUP_DIR -type f -mtime +7 -delete
EOF

chmod +x /home/ec2-user/backup.sh

# Create a health check script
cat > /home/ec2-user/health-check.sh << 'EOF'
#!/bin/bash
# Check if Docker is running
if ! systemctl is-active --quiet docker; then
    systemctl start docker
fi

# Check if Airflow containers are running
cd /home/ec2-user/airflow
if ! docker-compose ps | grep -q "Up"; then
    docker-compose up -d
fi

# Force a DAG sync from S3
/home/ec2-user/sync_dags.sh
EOF

chmod +x /home/ec2-user/health-check.sh

# Set up combined crontab for all scheduled tasks
(crontab -l 2>/dev/null; echo "0 0 * * * /home/ec2-user/backup.sh") | crontab -
(crontab -l 2>/dev/null; echo "*/5 * * * * /home/ec2-user/health-check.sh") | crontab -

# Tag the instance
aws ec2 create-tags --region ${region} \
  --resources $(curl -s http://169.254.169.254/latest/meta-data/instance-id) \
  --tags Key=Project,Value=${project} Key=Environment,Value=${environment}

# Signal that setup is complete
touch /home/ec2-user/setup_complete
