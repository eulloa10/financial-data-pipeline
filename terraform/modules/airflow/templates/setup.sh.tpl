#!/bin/bash
set -e
set -x

# Update and install necessary packages
sudo yum update -y
sudo amazon-linux-extras install docker -y
sudo systemctl start docker
sudo systemctl enable docker
sudo usermod -aG docker ec2-user

# Install Docker Compose
sudo yum install -y curl
sudo curl -L "https://github.com/docker/compose/releases/download/v2.32.3/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose
sudo ln -s /usr/local/bin/docker-compose /usr/bin/docker-compose

# Install AWS CLI v2
sudo yum install -y unzip
curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
unzip awscliv2.zip
sudo ./aws/install
rm -rf awscliv2.zip aws/

# Install and start SSM Agent
sudo yum install -y amazon-ssm-agent
sudo systemctl enable amazon-ssm-agent
sudo systemctl start amazon-ssm-agent

# Create directories for Airflow
mkdir -p /home/ec2-user/airflow/{dags,logs,plugins,config}
sudo chown -R 50000:0 /home/ec2-user/airflow/{dags,logs,plugins,config}
sudo chown -R ec2-user:ec2-user /home/ec2-user/airflow
sudo chmod -R 777 /home/ec2-user/airflow/logs

# Create docker-compose.yml
cat <<EOF > /home/ec2-user/airflow/docker-compose.yml
${docker_compose_content}
EOF

# Initialize Airflow database and create admin user
cd /home/ec2-user/airflow
sudo docker-compose up -d postgres

echo "Waiting for PostgreSQL to be ready..."
until sudo docker exec $(sudo docker-compose ps -q postgres) pg_isready -U airflow; do
  echo "PostgreSQL not ready, waiting..."
  sleep 5
done

sudo docker-compose run --rm webserver airflow db upgrade
sudo docker-compose run --rm webserver airflow users create \
    --username ${airflow_admin_username} \
    --password ${airflow_admin_password} \
    --firstname Admin \
    --lastname User \
    --role Admin \
    --email admin@example.com

# Start Airflow services
sudo docker-compose up -d

# Create sync script
cat <<'SYNC_SCRIPT' > /home/ec2-user/airflow/sync_dags.sh
#!/bin/bash
while true; do
  aws s3 sync s3://${dag_s3_bucket} /home/ec2-user/airflow/dags
  sleep 300
done
SYNC_SCRIPT

chmod +x /home/ec2-user/airflow/sync_dags.sh
nohup bash /home/ec2-user/airflow/sync_dags.sh >> /home/ec2-user/airflow/sync_dags.log 2>&1 &

echo "Airflow setup complete."
