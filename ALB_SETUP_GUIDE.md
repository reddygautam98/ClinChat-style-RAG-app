# Application Load Balancer (ALB) Setup Guide
## ClinChat-style-RAG-app

### Table of Contents
- [Overview](#overview)
- [Prerequisites](#prerequisites)
- [ALB Configuration Details](#alb-configuration-details)
- [Target Groups Configuration](#target-groups-configuration)
- [Security Groups](#security-groups)
- [SSL/TLS Configuration](#ssltls-configuration)
- [Health Checks](#health-checks)
- [Auto Scaling Integration](#auto-scaling-integration)
- [Monitoring and Logging](#monitoring-and-logging)
- [Step-by-Step Creation](#step-by-step-creation)
- [Troubleshooting](#troubleshooting)

---

## Overview
This guide provides detailed configuration for setting up an Application Load Balancer for the ClinChat RAG application to ensure high availability, scalability, and secure traffic distribution.

## Prerequisites
- [ ] AWS Account with appropriate permissions
- [ ] VPC with at least 2 subnets in different AZs
- [ ] ECS Cluster or EC2 instances ready for deployment
- [ ] SSL Certificate (ACM) for HTTPS traffic
- [ ] Route 53 hosted zone (if using custom domain)

---

## ALB Configuration Details

### Basic Settings
| Field | Value | Notes |
|-------|--------|-------|
| **Name** | `clinchat-rag-alb` | Descriptive name for the load balancer |
| **Scheme** | `internet-facing` | Public-facing for web traffic |
| **IP Address Type** | `IPv4` | Standard IPv4 addressing |
| **VPC** | `clinchat-vpc` | Your project VPC |
| **Availability Zones** | `us-east-1a`, `us-east-1b` | At least 2 AZs for high availability |
| **Subnets** | Public subnets in selected AZs | Internet-facing requires public subnets |

### Advanced Settings
| Field | Value | Notes |
|-------|--------|-------|
| **Deletion Protection** | `Enabled` | Prevent accidental deletion |
| **Idle Timeout** | `60 seconds` | Connection timeout |
| **Cross-Zone Load Balancing** | `Enabled` | Distribute traffic evenly |
| **Access Logs** | `Enabled` | Store in S3 for analysis |
| **Connection Logs** | `Enabled` | Debug connection issues |

---

## Target Groups Configuration

### Backend API Target Group
```yaml
Name: clinchat-api-tg
Target Type: IP addresses (for ECS Fargate) / Instances (for EC2)
Protocol: HTTP
Port: 8000
VPC: clinchat-vpc
Protocol Version: HTTP1

Health Check Settings:
  Protocol: HTTP
  Path: /health
  Port: traffic port
  Healthy Threshold: 2
  Unhealthy Threshold: 3
  Timeout: 5 seconds
  Interval: 30 seconds
  Success Codes: 200

Advanced Health Check:
  Grace Period: 300 seconds
  Deregistration Delay: 30 seconds
```

### Frontend Target Group
```yaml
Name: clinchat-frontend-tg
Target Type: IP addresses (for ECS Fargate) / Instances (for EC2)
Protocol: HTTP
Port: 3000
VPC: clinchat-vpc
Protocol Version: HTTP1

Health Check Settings:
  Protocol: HTTP
  Path: /
  Port: traffic port
  Healthy Threshold: 2
  Unhealthy Threshold: 3
  Timeout: 5 seconds
  Interval: 30 seconds
  Success Codes: 200
```

---

## Security Groups

### ALB Security Group
```yaml
Name: clinchat-alb-sg
Description: Security group for ClinChat ALB

Inbound Rules:
  - Type: HTTP
    Protocol: TCP
    Port: 80
    Source: 0.0.0.0/0
    Description: Allow HTTP traffic from internet
    
  - Type: HTTPS
    Protocol: TCP  
    Port: 443
    Source: 0.0.0.0/0
    Description: Allow HTTPS traffic from internet

Outbound Rules:
  - Type: All Traffic
    Protocol: All
    Port Range: All
    Destination: 0.0.0.0/0
    Description: Allow all outbound traffic
```

### Target Security Group Updates
```yaml
# Add these rules to your ECS/EC2 security groups
Inbound Rules:
  - Type: Custom TCP
    Protocol: TCP
    Port: 8000
    Source: clinchat-alb-sg
    Description: Allow ALB to backend API
    
  - Type: Custom TCP
    Protocol: TCP
    Port: 3000
    Source: clinchat-alb-sg
    Description: Allow ALB to frontend
```

---

## SSL/TLS Configuration

### SSL Certificate Setup
1. **Request Certificate in ACM**
   ```yaml
   Domain Names:
     - clinchat.yourdomain.com
     - *.clinchat.yourdomain.com
   Validation Method: DNS validation
   Key Algorithm: RSA 2048
   ```

2. **Listener Configuration**
   ```yaml
   HTTPS Listener (443):
     Protocol: HTTPS
     Port: 443
     SSL Certificate: arn:aws:acm:region:account:certificate/cert-id
     Security Policy: ELBSecurityPolicy-TLS-1-2-2017-01
     
   HTTP Listener (80):
     Protocol: HTTP
     Port: 80
     Default Action: Redirect to HTTPS
   ```

---

## Health Checks

### API Health Check Endpoint
Ensure your backend API has a health check endpoint:
```python
# Example health check endpoint in your FastAPI app
@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "service": "clinchat-rag-api",
        "version": "1.0.0"
    }
```

### Frontend Health Check
Ensure your frontend serves a basic response at root path `/`.

---

## Auto Scaling Integration

### ECS Service Auto Scaling
```yaml
Service Name: clinchat-api-service
Min Capacity: 2
Max Capacity: 10
Desired Capacity: 2

Scaling Policies:
  CPU Target Tracking:
    Target Value: 70%
    Scale Out Cooldown: 300s
    Scale In Cooldown: 300s
    
  ALB Request Count:
    Target Value: 100 requests per target
    Scale Out Cooldown: 300s
    Scale In Cooldown: 300s
```

---

## Monitoring and Logging

### CloudWatch Metrics to Monitor
- [ ] `RequestCount` - Total requests
- [ ] `TargetResponseTime` - Response latency
- [ ] `HTTPCode_Target_2XX_Count` - Successful responses
- [ ] `HTTPCode_Target_4XX_Count` - Client errors
- [ ] `HTTPCode_Target_5XX_Count` - Server errors
- [ ] `HealthyHostCount` - Healthy targets
- [ ] `UnHealthyHostCount` - Unhealthy targets

### Access Logs S3 Bucket
```yaml
Bucket Name: clinchat-alb-access-logs
Bucket Policy: Allow ALB to write logs
Lifecycle Policy: Delete logs after 30 days
```

### CloudWatch Alarms
```yaml
High Error Rate Alarm:
  Metric: HTTPCode_Target_5XX_Count
  Threshold: > 10 errors in 5 minutes
  Action: SNS notification

High Response Time Alarm:
  Metric: TargetResponseTime  
  Threshold: > 2 seconds
  Action: SNS notification

Low Healthy Host Count:
  Metric: HealthyHostCount
  Threshold: < 2 hosts
  Action: SNS notification
```

---

## Step-by-Step Creation

### Step 1: Create ALB
1. Navigate to EC2 → Load Balancers → Create Load Balancer
2. Choose Application Load Balancer
3. Fill in basic configuration from table above
4. Select VPC and subnets
5. Configure security groups

### Step 2: Configure Target Groups
1. Create target groups using configurations above
2. Register targets (ECS tasks or EC2 instances)
3. Configure health checks

### Step 3: Configure Listeners
1. Add HTTPS listener (443) with SSL certificate
2. Add HTTP listener (80) with redirect to HTTPS
3. Configure routing rules

### Step 4: Configure Routing Rules
```yaml
Default Rule (Frontend):
  Condition: Default
  Action: Forward to clinchat-frontend-tg

API Rule:
  Condition: Path pattern = /api/*
  Action: Forward to clinchat-api-tg
  Priority: 100

Health Check Rule:
  Condition: Path pattern = /health
  Action: Forward to clinchat-api-tg  
  Priority: 200
```

### Step 5: Test Configuration
1. Verify health checks pass
2. Test HTTP → HTTPS redirect
3. Test API endpoints through ALB
4. Test frontend through ALB

---

## Troubleshooting

### Common Issues and Solutions

#### 1. Targets Showing Unhealthy
- [ ] Check security group rules allow ALB to reach targets
- [ ] Verify health check path returns 200 status code
- [ ] Check target is running and accessible on specified port
- [ ] Review health check configuration (timeout, interval)

#### 2. 502 Bad Gateway Errors  
- [ ] Verify targets are healthy and running
- [ ] Check target application is binding to 0.0.0.0, not localhost
- [ ] Verify target security group allows inbound from ALB
- [ ] Check ECS task definition port mappings

#### 3. SSL Certificate Issues
- [ ] Verify certificate is validated and issued
- [ ] Check certificate covers the domain being used
- [ ] Ensure certificate is in the same region as ALB
- [ ] Verify DNS validation records are present

#### 4. Timeout Issues
- [ ] Check idle timeout settings on ALB
- [ ] Verify target group deregistration delay
- [ ] Check application response times
- [ ] Review CloudWatch metrics for patterns

### Useful CLI Commands
```bash
# Check ALB status
aws elbv2 describe-load-balancers --names clinchat-rag-alb

# Check target health
aws elbv2 describe-target-health --target-group-arn <target-group-arn>

# Check listeners
aws elbv2 describe-listeners --load-balancer-arn <alb-arn>

# View access logs
aws s3 ls s3://clinchat-alb-access-logs/
```

---

## Validation Checklist

### Pre-Deployment
- [ ] VPC and subnets configured
- [ ] Security groups created and configured
- [ ] SSL certificate requested and validated
- [ ] Target groups created with proper health checks
- [ ] ECS services or EC2 instances ready

### Post-Deployment  
- [ ] ALB shows as "Active" state
- [ ] All targets showing as "Healthy"
- [ ] HTTP redirects to HTTPS properly
- [ ] API endpoints accessible via ALB DNS name
- [ ] Frontend loads correctly via ALB DNS name
- [ ] SSL certificate working (no browser warnings)
- [ ] CloudWatch metrics populating
- [ ] Access logs being generated in S3

### Production Readiness
- [ ] Custom domain configured (if applicable)
- [ ] Route 53 records pointing to ALB
- [ ] Auto scaling policies configured
- [ ] CloudWatch alarms set up
- [ ] Access logs retention policy set
- [ ] Backup and disaster recovery plan documented

---

## Configuration Summary

**ALB DNS Name**: `clinchat-rag-alb-xxxxxxxxx.us-east-1.elb.amazonaws.com`  
**Frontend URL**: `https://your-alb-dns-name/`  
**API Base URL**: `https://your-alb-dns-name/api/`  
**Health Check**: `https://your-alb-dns-name/health`

---

*Last Updated: October 26, 2025*  
*Project: ClinChat-style-RAG-app*  
*Environment: Production*