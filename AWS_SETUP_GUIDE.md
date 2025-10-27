# AWS Infrastructure Setup Guide

Complete guide for deploying the HealthAI RAG Application on AWS using ECS, ECR, ALB, and other AWS services.

## 🏗️ Architecture Overview

The AWS infrastructure includes:

- **Amazon ECS**: Container orchestration with Fargate
- **Amazon ECR**: Docker image registry
- **Application Load Balancer (ALB)**: Traffic distribution and SSL termination
- **Amazon RDS**: PostgreSQL database for application data
- **Amazon ElastiCache**: Redis for caching and session storage
- **Amazon CloudWatch**: Monitoring and logging
- **AWS IAM**: Identity and access management
- **AWS Certificate Manager**: SSL certificates
- **Amazon VPC**: Network isolation and security

## 📋 Prerequisites

Before starting, ensure you have:

1. **AWS Account**: With appropriate billing setup
2. **AWS CLI**: Installed and configured
3. **Docker**: For local testing and building images
4. **Domain Name**: (Optional) For custom domain setup
5. **Administrative Access**: To create IAM roles and policies

## 🚀 Step-by-Step Setup

### 1. Initial AWS Configuration

#### Configure AWS CLI

```bash
# Install AWS CLI v2 (if not already installed)
# Windows: Download from https://aws.amazon.com/cli/
# Linux/Mac: 
curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
unzip awscliv2.zip
sudo ./aws/install

# Configure AWS CLI
aws configure
# AWS Access Key ID: [Your Access Key]
# AWS Secret Access Key: [Your Secret Key]  
# Default region name: eu-north-1
# Default output format: json
```

#### Verify AWS Configuration

```bash
# Test AWS connectivity
aws sts get-caller-identity
aws ec2 describe-regions --region eu-north-1
```

### 2. VPC and Networking Setup

#### Create VPC with Public and Private Subnets

```bash
# Create VPC
VPC_ID=$(aws ec2 create-vpc \
  --cidr-block 10.0.0.0/16 \
  --tag-specifications 'ResourceType=vpc,Tags=[{Key=Name,Value=healthai-vpc}]' \
  --query 'Vpc.VpcId' --output text)

echo "Created VPC: $VPC_ID"

# Enable DNS hostnames
aws ec2 modify-vpc-attribute --vpc-id $VPC_ID --enable-dns-hostnames

# Create Internet Gateway
IGW_ID=$(aws ec2 create-internet-gateway \
  --tag-specifications 'ResourceType=internet-gateway,Tags=[{Key=Name,Value=healthai-igw}]' \
  --query 'InternetGateway.InternetGatewayId' --output text)

# Attach Internet Gateway to VPC
aws ec2 attach-internet-gateway --vpc-id $VPC_ID --internet-gateway-id $IGW_ID

# Create Public Subnets (2 AZs for high availability)
PUBLIC_SUBNET_1=$(aws ec2 create-subnet \
  --vpc-id $VPC_ID \
  --cidr-block 10.0.1.0/24 \
  --availability-zone eu-north-1a \
  --tag-specifications 'ResourceType=subnet,Tags=[{Key=Name,Value=healthai-public-1}]' \
  --query 'Subnet.SubnetId' --output text)

PUBLIC_SUBNET_2=$(aws ec2 create-subnet \
  --vpc-id $VPC_ID \
  --cidr-block 10.0.2.0/24 \
  --availability-zone eu-north-1b \
  --tag-specifications 'ResourceType=subnet,Tags=[{Key=Name,Value=healthai-public-2}]' \
  --query 'Subnet.SubnetId' --output text)

# Create Private Subnets
PRIVATE_SUBNET_1=$(aws ec2 create-subnet \
  --vpc-id $VPC_ID \
  --cidr-block 10.0.11.0/24 \
  --availability-zone eu-north-1a \
  --tag-specifications 'ResourceType=subnet,Tags=[{Key=Name,Value=healthai-private-1}]' \
  --query 'Subnet.SubnetId' --output text)

PRIVATE_SUBNET_2=$(aws ec2 create-subnet \
  --vpc-id $VPC_ID \
  --cidr-block 10.0.12.0/24 \
  --availability-zone eu-north-1b \
  --tag-specifications 'ResourceType=subnet,Tags=[{Key=Name,Value=healthai-private-2}]' \
  --query 'Subnet.SubnetId' --output text)

# Create Route Tables
PUBLIC_RT=$(aws ec2 create-route-table \
  --vpc-id $VPC_ID \
  --tag-specifications 'ResourceType=route-table,Tags=[{Key=Name,Value=healthai-public-rt}]' \
  --query 'RouteTable.RouteTableId' --output text)

# Add route to Internet Gateway
aws ec2 create-route --route-table-id $PUBLIC_RT --destination-cidr-block 0.0.0.0/0 --gateway-id $IGW_ID

# Associate public subnets with public route table
aws ec2 associate-route-table --subnet-id $PUBLIC_SUBNET_1 --route-table-id $PUBLIC_RT
aws ec2 associate-route-table --subnet-id $PUBLIC_SUBNET_2 --route-table-id $PUBLIC_RT
```

#### Create NAT Gateways for Private Subnets

```bash
# Allocate Elastic IPs for NAT Gateways
EIP_1=$(aws ec2 allocate-address --domain vpc --query 'AllocationId' --output text)
EIP_2=$(aws ec2 allocate-address --domain vpc --query 'AllocationId' --output text)

# Create NAT Gateways
NAT_GW_1=$(aws ec2 create-nat-gateway \
  --subnet-id $PUBLIC_SUBNET_1 \
  --allocation-id $EIP_1 \
  --tag-specifications 'ResourceType=nat-gateway,Tags=[{Key=Name,Value=healthai-nat-1}]' \
  --query 'NatGateway.NatGatewayId' --output text)

NAT_GW_2=$(aws ec2 create-nat-gateway \
  --subnet-id $PUBLIC_SUBNET_2 \
  --allocation-id $EIP_2 \
  --tag-specifications 'ResourceType=nat-gateway,Tags=[{Key=Name,Value=healthai-nat-2}]' \
  --query 'NatGateway.NatGatewayId' --output text)

# Create private route tables
PRIVATE_RT_1=$(aws ec2 create-route-table \
  --vpc-id $VPC_ID \
  --tag-specifications 'ResourceType=route-table,Tags=[{Key=Name,Value=healthai-private-rt-1}]' \
  --query 'RouteTable.RouteTableId' --output text)

PRIVATE_RT_2=$(aws ec2 create-route-table \
  --vpc-id $VPC_ID \
  --tag-specifications 'ResourceType=route-table,Tags=[{Key=Name,Value=healthai-private-rt-2}]' \
  --query 'RouteTable.RouteTableId' --output text)

# Wait for NAT Gateways to be available
echo "Waiting for NAT Gateways to be available..."
aws ec2 wait nat-gateway-available --nat-gateway-ids $NAT_GW_1 $NAT_GW_2

# Add routes to NAT Gateways
aws ec2 create-route --route-table-id $PRIVATE_RT_1 --destination-cidr-block 0.0.0.0/0 --nat-gateway-id $NAT_GW_1
aws ec2 create-route --route-table-id $PRIVATE_RT_2 --destination-cidr-block 0.0.0.0/0 --nat-gateway-id $NAT_GW_2

# Associate private subnets with private route tables
aws ec2 associate-route-table --subnet-id $PRIVATE_SUBNET_1 --route-table-id $PRIVATE_RT_1
aws ec2 associate-route-table --subnet-id $PRIVATE_SUBNET_2 --route-table-id $PRIVATE_RT_2
```

### 3. Security Groups

```bash
# ALB Security Group
ALB_SG=$(aws ec2 create-security-group \
  --group-name healthai-alb-sg \
  --description "Security group for HealthAI ALB" \
  --vpc-id $VPC_ID \
  --tag-specifications 'ResourceType=security-group,Tags=[{Key=Name,Value=healthai-alb-sg}]' \
  --query 'GroupId' --output text)

# Allow HTTP and HTTPS traffic
aws ec2 authorize-security-group-ingress --group-id $ALB_SG --protocol tcp --port 80 --cidr 0.0.0.0/0
aws ec2 authorize-security-group-ingress --group-id $ALB_SG --protocol tcp --port 443 --cidr 0.0.0.0/0

# ECS Security Group
ECS_SG=$(aws ec2 create-security-group \
  --group-name healthai-ecs-sg \
  --description "Security group for HealthAI ECS tasks" \
  --vpc-id $VPC_ID \
  --tag-specifications 'ResourceType=security-group,Tags=[{Key=Name,Value=healthai-ecs-sg}]' \
  --query 'GroupId' --output text)

# Allow traffic from ALB
aws ec2 authorize-security-group-ingress --group-id $ECS_SG --protocol tcp --port 8000 --source-group $ALB_SG

# RDS Security Group
RDS_SG=$(aws ec2 create-security-group \
  --group-name healthai-rds-sg \
  --description "Security group for HealthAI RDS" \
  --vpc-id $VPC_ID \
  --tag-specifications 'ResourceType=security-group,Tags=[{Key=Name,Value=healthai-rds-sg}]' \
  --query 'GroupId' --output text)

# Allow PostgreSQL traffic from ECS
aws ec2 authorize-security-group-ingress --group-id $RDS_SG --protocol tcp --port 5432 --source-group $ECS_SG

# Redis Security Group
REDIS_SG=$(aws ec2 create-security-group \
  --group-name healthai-redis-sg \
  --description "Security group for HealthAI ElastiCache" \
  --vpc-id $VPC_ID \
  --tag-specifications 'ResourceType=security-group,Tags=[{Key=Name,Value=healthai-redis-sg}]' \
  --query 'GroupId' --output text)

# Allow Redis traffic from ECS
aws ec2 authorize-security-group-ingress --group-id $REDIS_SG --protocol tcp --port 6379 --source-group $ECS_SG
```

### 4. ECR Repository Setup

```bash
# Create ECR repository
aws ecr create-repository \
  --repository-name clinchat-rag \
  --region eu-north-1 \
  --image-tag-mutability MUTABLE

# Get ECR login token and login
aws ecr get-login-password --region eu-north-1 | docker login --username AWS --password-stdin 123456789012.dkr.ecr.eu-north-1.amazonaws.com

# Build and push initial image (run from project root)
docker build -t clinchat-rag:latest -f Dockerfile.optimized .
docker tag clinchat-rag:latest 123456789012.dkr.ecr.eu-north-1.amazonaws.com/clinchat-rag:latest
docker push 123456789012.dkr.ecr.eu-north-1.amazonaws.com/clinchat-rag:latest
```

### 5. RDS Database Setup

```bash
# Create DB Subnet Group
aws rds create-db-subnet-group \
  --db-subnet-group-name healthai-db-subnet-group \
  --db-subnet-group-description "Subnet group for HealthAI RDS" \
  --subnet-ids $PRIVATE_SUBNET_1 $PRIVATE_SUBNET_2 \
  --tags Key=Name,Value=healthai-db-subnet-group

# Create RDS instance
aws rds create-db-instance \
  --db-instance-identifier healthai-postgres \
  --db-instance-class db.t3.micro \
  --engine postgres \
  --engine-version 15.4 \
  --master-username healthai_admin \
  --master-user-password 'YourSecurePassword123!' \
  --allocated-storage 20 \
  --storage-type gp2 \
  --vpc-security-group-ids $RDS_SG \
  --db-subnet-group-name healthai-db-subnet-group \
  --backup-retention-period 7 \
  --storage-encrypted \
  --tags Key=Name,Value=healthai-postgres

# Wait for RDS instance to be available
echo "Waiting for RDS instance to be available (this may take 10-15 minutes)..."
aws rds wait db-instance-available --db-instance-identifier healthai-postgres
```

### 6. ElastiCache Redis Setup

```bash
# Create ElastiCache Subnet Group
aws elasticache create-cache-subnet-group \
  --cache-subnet-group-name healthai-redis-subnet-group \
  --cache-subnet-group-description "Subnet group for HealthAI Redis" \
  --subnet-ids $PRIVATE_SUBNET_1 $PRIVATE_SUBNET_2

# Create ElastiCache Redis cluster
aws elasticache create-cache-cluster \
  --cache-cluster-id healthai-redis \
  --cache-node-type cache.t3.micro \
  --engine redis \
  --num-cache-nodes 1 \
  --cache-subnet-group-name healthai-redis-subnet-group \
  --security-group-ids $REDIS_SG \
  --tags Key=Name,Value=healthai-redis
```

### 7. Application Load Balancer Setup

```bash
# Create Application Load Balancer
ALB_ARN=$(aws elbv2 create-load-balancer \
  --name healthai-alb \
  --subnets $PUBLIC_SUBNET_1 $PUBLIC_SUBNET_2 \
  --security-groups $ALB_SG \
  --tags Key=Name,Value=healthai-alb \
  --query 'LoadBalancers[0].LoadBalancerArn' --output text)

# Create Target Group
TG_ARN=$(aws elbv2 create-target-group \
  --name healthai-tg \
  --protocol HTTP \
  --port 8000 \
  --vpc-id $VPC_ID \
  --target-type ip \
  --health-check-path /health \
  --health-check-protocol HTTP \
  --health-check-interval-seconds 30 \
  --health-check-timeout-seconds 10 \
  --healthy-threshold-count 2 \
  --unhealthy-threshold-count 3 \
  --tags Key=Name,Value=healthai-tg \
  --query 'TargetGroups[0].TargetGroupArn' --output text)

# Create ALB Listener
aws elbv2 create-listener \
  --load-balancer-arn $ALB_ARN \
  --protocol HTTP \
  --port 80 \
  --default-actions Type=forward,TargetGroupArn=$TG_ARN
```

### 8. ECS Cluster and Service Setup

#### Create ECS Cluster

```bash
# Create ECS cluster
aws ecs create-cluster \
  --cluster-name clinchat-cluster \
  --capacity-providers FARGATE \
  --default-capacity-provider-strategy capacityProvider=FARGATE,weight=1 \
  --tags key=Name,value=clinchat-cluster
```

#### Create IAM Roles

```bash
# Create Task Execution Role
aws iam create-role \
  --role-name ecsTaskExecutionRole \
  --assume-role-policy-document '{
    "Version": "2012-10-17",
    "Statement": [
      {
        "Effect": "Allow",
        "Principal": {
          "Service": "ecs-tasks.amazonaws.com"
        },
        "Action": "sts:AssumeRole"
      }
    ]
  }'

# Attach required policies
aws iam attach-role-policy \
  --role-name ecsTaskExecutionRole \
  --policy-arn arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy

# Create Task Role for application
aws iam create-role \
  --role-name ecsTaskRole \
  --assume-role-policy-document '{
    "Version": "2012-10-17",
    "Statement": [
      {
        "Effect": "Allow",
        "Principal": {
          "Service": "ecs-tasks.amazonaws.com"
        },
        "Action": "sts:AssumeRole"
      }
    ]
  }'

# Create custom policy for application access
aws iam create-policy \
  --policy-name HealthAIAppPolicy \
  --policy-document '{
    "Version": "2012-10-17",
    "Statement": [
      {
        "Effect": "Allow",
        "Action": [
          "s3:GetObject",
          "s3:PutObject",
          "secretsmanager:GetSecretValue",
          "ssm:GetParameter",
          "ssm:GetParameters",
          "ssm:GetParametersByPath"
        ],
        "Resource": "*"
      }
    ]
  }'

# Attach custom policy to task role
aws iam attach-role-policy \
  --role-name ecsTaskRole \
  --policy-arn arn:aws:iam::123456789012:policy/HealthAIAppPolicy
```

#### Create Task Definition

Create the task definition file:

```json
{
  "family": "clinchat-task",
  "networkMode": "awsvpc",
  "requiresCompatibilities": ["FARGATE"],
  "cpu": "512",
  "memory": "1024",
  "executionRoleArn": "arn:aws:iam::123456789012:role/ecsTaskExecutionRole",
  "taskRoleArn": "arn:aws:iam::123456789012:role/ecsTaskRole",
  "containerDefinitions": [
    {
      "name": "healthai-app",
      "image": "123456789012.dkr.ecr.eu-north-1.amazonaws.com/clinchat-rag:latest",
      "portMappings": [
        {
          "containerPort": 8000,
          "protocol": "tcp"
        }
      ],
      "essential": true,
      "logConfiguration": {
        "logDriver": "awslogs",
        "options": {
          "awslogs-group": "/ecs/clinchat-task",
          "awslogs-region": "eu-north-1",
          "awslogs-stream-prefix": "ecs"
        }
      },
      "environment": [
        {
          "name": "PORT",
          "value": "8000"
        },
        {
          "name": "PYTHONPATH",
          "value": "/app"
        }
      ],
      "secrets": [
        {
          "name": "GROQ_API_KEY",
          "valueFrom": "arn:aws:ssm:eu-north-1:123456789012:parameter/healthai/groq-api-key"
        },
        {
          "name": "GOOGLE_API_KEY", 
          "valueFrom": "arn:aws:ssm:eu-north-1:123456789012:parameter/healthai/google-api-key"
        }
      ],
      "healthCheck": {
        "command": [
          "CMD-SHELL",
          "curl -f http://localhost:8000/health || exit 1"
        ],
        "interval": 30,
        "timeout": 5,
        "retries": 3,
        "startPeriod": 60
      }
    }
  ]
}
```

Register the task definition:

```bash
# Create CloudWatch Log Group
aws logs create-log-group --log-group-name /ecs/clinchat-task

# Register task definition
aws ecs register-task-definition --cli-input-json file://task-definition.json
```

#### Create ECS Service

```bash
# Create ECS service
aws ecs create-service \
  --cluster clinchat-cluster \
  --service-name clinchat-service \
  --task-definition clinchat-task \
  --desired-count 2 \
  --launch-type FARGATE \
  --platform-version LATEST \
  --network-configuration "awsvpcConfiguration={subnets=[$PRIVATE_SUBNET_1,$PRIVATE_SUBNET_2],securityGroups=[$ECS_SG],assignPublicIp=DISABLED}" \
  --load-balancers targetGroupArn=$TG_ARN,containerName=healthai-app,containerPort=8000 \
  --health-check-grace-period-seconds 300 \
  --tags key=Name,value=clinchat-service
```

### 9. SSL Certificate Setup (Optional)

If you have a custom domain:

```bash
# Request SSL certificate
CERT_ARN=$(aws acm request-certificate \
  --domain-name yourdomain.com \
  --subject-alternative-names "*.yourdomain.com" \
  --validation-method DNS \
  --query 'CertificateArn' --output text)

# Add HTTPS listener to ALB
aws elbv2 create-listener \
  --load-balancer-arn $ALB_ARN \
  --protocol HTTPS \
  --port 443 \
  --certificates CertificateArn=$CERT_ARN \
  --default-actions Type=forward,TargetGroupArn=$TG_ARN
```

### 10. Parameter Store Setup

Store sensitive configuration in AWS Systems Manager Parameter Store:

```bash
# Store API keys securely
aws ssm put-parameter \
  --name "/healthai/groq-api-key" \
  --value "your_groq_api_key_here" \
  --type "SecureString" \
  --description "GROQ API Key for HealthAI"

aws ssm put-parameter \
  --name "/healthai/google-api-key" \
  --value "your_google_api_key_here" \
  --type "SecureString" \
  --description "Google API Key for HealthAI"

aws ssm put-parameter \
  --name "/healthai/database-url" \
  --value "postgresql://healthai_admin:YourSecurePassword123!@healthai-postgres.amazonaws.com:5432/healthai" \
  --type "SecureString" \
  --description "Database URL for HealthAI"

# Get RDS endpoint
RDS_ENDPOINT=$(aws rds describe-db-instances \
  --db-instance-identifier healthai-postgres \
  --query 'DBInstances[0].Endpoint.Address' --output text)

# Get Redis endpoint  
REDIS_ENDPOINT=$(aws elasticache describe-cache-clusters \
  --cache-cluster-id healthai-redis \
  --show-cache-node-info \
  --query 'CacheClusters[0].CacheNodes[0].Endpoint.Address' --output text)

echo "RDS Endpoint: $RDS_ENDPOINT"
echo "Redis Endpoint: $REDIS_ENDPOINT"
```

## 🔍 Monitoring and Logging

### CloudWatch Setup

```bash
# Create custom dashboard
aws cloudwatch put-dashboard \
  --dashboard-name "HealthAI-Dashboard" \
  --dashboard-body '{
    "widgets": [
      {
        "type": "metric",
        "properties": {
          "metrics": [
            ["AWS/ECS", "CPUUtilization", "ServiceName", "clinchat-service", "ClusterName", "clinchat-cluster"],
            [".", "MemoryUtilization", ".", ".", ".", "."]
          ],
          "period": 300,
          "stat": "Average",
          "region": "eu-north-1",
          "title": "ECS Metrics"
        }
      }
    ]
  }'

# Create CloudWatch Alarms
aws cloudwatch put-metric-alarm \
  --alarm-name "HealthAI-HighCPU" \
  --alarm-description "Alarm when CPU exceeds 80%" \
  --metric-name CPUUtilization \
  --namespace AWS/ECS \
  --statistic Average \
  --period 300 \
  --threshold 80 \
  --comparison-operator GreaterThanThreshold \
  --dimensions Name=ServiceName,Value=clinchat-service Name=ClusterName,Value=clinchat-cluster \
  --evaluation-periods 2
```

## 🔐 Security Hardening

### Enable VPC Flow Logs

```bash
# Create IAM role for VPC Flow Logs
aws iam create-role \
  --role-name flowlogsRole \
  --assume-role-policy-document '{
    "Version": "2012-10-17",
    "Statement": [
      {
        "Effect": "Allow",
        "Principal": {
          "Service": "vpc-flow-logs.amazonaws.com"
        },
        "Action": "sts:AssumeRole"
      }
    ]
  }'

aws iam attach-role-policy \
  --role-name flowlogsRole \
  --policy-arn arn:aws:iam::aws:policy/service-role/VPCFlowLogsDeliveryRolePolicy

# Enable VPC Flow Logs
aws ec2 create-flow-logs \
  --resource-type VPC \
  --resource-ids $VPC_ID \
  --traffic-type ALL \
  --log-destination-type cloud-watch-logs \
  --log-group-name VPCFlowLogs \
  --deliver-logs-permission-arn arn:aws:iam::123456789012:role/flowlogsRole
```

### Enable AWS Config

```bash
# Create S3 bucket for AWS Config
aws s3 mb s3://healthai-config-bucket-$(date +%s) --region eu-north-1

# Enable AWS Config (requires additional IAM setup)
# This is a complex setup - consider using AWS Console for initial configuration
```

## 🚨 Troubleshooting

### Common Issues

#### 1. ECS Tasks Not Starting

Check ECS service events:
```bash
aws ecs describe-services --cluster clinchat-cluster --services clinchat-service
```

#### 2. ALB Health Check Failures

Check target group health:
```bash
aws elbv2 describe-target-health --target-group-arn $TG_ARN
```

#### 3. Database Connection Issues

Test database connectivity from ECS task:
```bash
# Get task ARN
TASK_ARN=$(aws ecs list-tasks --cluster clinchat-cluster --service-name clinchat-service --query 'taskArns[0]' --output text)

# Execute command in running task
aws ecs execute-command \
  --cluster clinchat-cluster \
  --task $TASK_ARN \
  --container healthai-app \
  --interactive \
  --command "/bin/bash"
```

### Useful Commands

```bash
# View ECS service logs
aws logs tail /ecs/clinchat-task --follow

# Update ECS service
aws ecs update-service \
  --cluster clinchat-cluster \
  --service clinchat-service \
  --desired-count 3

# Scale down service
aws ecs update-service \
  --cluster clinchat-cluster \
  --service clinchat-service \
  --desired-count 0

# Get ALB DNS name
aws elbv2 describe-load-balancers \
  --load-balancer-arns $ALB_ARN \
  --query 'LoadBalancers[0].DNSName' --output text
```

## 🔄 Environment Variables Summary

Save these important values for your deployment:

```bash
# Network IDs
export VPC_ID="vpc-xxxxxxxxx"
export PUBLIC_SUBNET_1="subnet-xxxxxxxxx"  
export PUBLIC_SUBNET_2="subnet-xxxxxxxxx"
export PRIVATE_SUBNET_1="subnet-xxxxxxxxx"
export PRIVATE_SUBNET_2="subnet-xxxxxxxxx"

# Security Group IDs
export ALB_SG="sg-xxxxxxxxx"
export ECS_SG="sg-xxxxxxxxx"
export RDS_SG="sg-xxxxxxxxx"
export REDIS_SG="sg-xxxxxxxxx"

# Resource ARNs
export ALB_ARN="arn:aws:elasticloadbalancing:eu-north-1:123456789012:loadbalancer/app/healthai-alb/xxxxxxxxx"
export TG_ARN="arn:aws:elasticloadbalancing:eu-north-1:123456789012:targetgroup/healthai-tg/xxxxxxxxx"

# Endpoints
export RDS_ENDPOINT="healthai-postgres.xxxxxxxxx.eu-north-1.rds.amazonaws.com"
export REDIS_ENDPOINT="healthai-redis.xxxxxxxxx.cache.amazonaws.com"
```

## 📋 Cost Optimization

### Right-Sizing Resources

Monitor and adjust instance sizes based on usage:

```bash
# Check ECS service utilization
aws cloudwatch get-metric-statistics \
  --namespace AWS/ECS \
  --metric-name CPUUtilization \
  --dimensions Name=ServiceName,Value=clinchat-service Name=ClusterName,Value=clinchat-cluster \
  --start-time $(date -u -d '1 hour ago' +%Y-%m-%dT%H:%M:%S) \
  --end-time $(date -u +%Y-%m-%dT%H:%M:%S) \
  --period 300 \
  --statistics Average
```

### Spot Instances for Development

For non-production environments, consider using Spot capacity:

```bash
# Update cluster to use Spot instances
aws ecs put-cluster-capacity-providers \
  --cluster clinchat-cluster \
  --capacity-providers FARGATE FARGATE_SPOT \
  --default-capacity-provider-strategy capacityProvider=FARGATE_SPOT,weight=4 capacityProvider=FARGATE,weight=1
```

## 🔗 Next Steps

After completing the AWS setup:

1. **Configure Domain**: Point your domain to the ALB
2. **Setup Monitoring**: Configure additional CloudWatch alarms
3. **Implement Backups**: Setup automated RDS and data backups
4. **Security Review**: Run AWS Security Hub and Config rules
5. **Performance Testing**: Load test your application
6. **CI/CD Integration**: Connect with GitHub Actions for automated deployments

## 📚 Additional Resources

- [AWS ECS Documentation](https://docs.aws.amazon.com/ecs/)
- [AWS Application Load Balancer Guide](https://docs.aws.amazon.com/elasticloadbalancing/latest/application/)
- [AWS RDS PostgreSQL Documentation](https://docs.aws.amazon.com/AmazonRDS/latest/UserGuide/)
- [AWS ElastiCache for Redis Documentation](https://docs.aws.amazon.com/AmazonElastiCache/latest/red-ug/)
- [AWS Well-Architected Framework](https://aws.amazon.com/architecture/well-architected/)

---

**Remember**: Always test in a development environment first and follow AWS security best practices. Consider using AWS CloudFormation or Terraform for infrastructure as code in production environments.