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

# Create Airflow directory structure
mkdir -p /home/ec2-user/airflow/{dags,logs,plugins}
cd /home/ec2-user/airflow

# Generate Fernet key and other secrets
FERNET_KEY=$(python3 -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())")
WEBSERVER_SECRET_KEY=$(python3 -c "import secrets; print(secrets.token_hex(16))")
AIRFLOW_DB_PASSWORD=$(python3 -c "import secrets; print(secrets.token_urlsafe(16))")

# Create environment file
cat > .env << EOF
FERNET_KEY=$FERNET_KEY
WEBSERVER_SECRET_KEY=$WEBSERVER_SECRET_KEY
AIRFLOW_DB_PASSWORD=$AIRFLOW_DB_PASSWORD
EOF

# Copy docker-compose template
cat > docker-compose.yml << 'EOF'
${docker_compose_content}
EOF

# Set correct permissions
chown -R ec2-user:ec2-user /home/ec2-user/airflow

# Start Airflow
docker-compose up -d

# Install AWS CLI
curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
unzip awscliv2.zip
./aws/install

# Set up CloudWatch agent
yum install -y amazon-cloudwatch-agent
/opt/aws/amazon-cloudwatch-agent/bin/amazon-cloudwatch-agent-ctl -a fetch-config -m ec2 -s -c ssm:${cloudwatch_config_parameter}

# Set up backup script
cat > /home/ec2-user/backup.sh << 'EOF'
#!/bin/bash
BACKUP_DIR="/home/ec2-user/airflow/backups"
mkdir -p $BACKUP_DIR
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
docker-compose exec -T postgres pg_dump -U airflow airflow > $BACKUP_DIR/airflow_$TIMESTAMP.sql
aws s3 cp $BACKUP_DIR/airflow_$TIMESTAMP.sql s3://${backup_bucket}/airflow/
find $BACKUP_DIR -type f -mtime +7 -delete
EOF

chmod +x /home/ec2-user/backup.sh

# Add backup cron job
echo "0 0 * * * /home/ec2-user/backup.sh" | crontab -
