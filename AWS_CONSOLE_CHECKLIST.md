# 🔍 AWS Console Setup Checklist for ClinChat HealthAI RAG

## 📋 **CRITICAL AWS CONSOLE ITEMS TO CHECK/CONFIGURE**

### 🎯 **Priority 1: Load Balancer Setup (MISSING - CRITICAL)**

**Problem**: Your ECS service needs a Load Balancer to be accessible from the internet.

**AWS Console Actions Required**:

#### **1. Create Application Load Balancer**
**Navigate to**: EC2 Console → Load Balancers → Create Load Balancer
- **Type**: Application Load Balancer
- **Name**: `clinchat-alb`
- **Scheme**: Internet-facing
- **IP address type**: IPv4
- **VPC**: Select your default VPC
- **Subnets**: Select at least 2 public subnets (different AZs)
- **Security Group**: Create new or use existing (allow HTTP 80, HTTPS 443)

#### **2. Create Target Group**
**Navigate to**: EC2 Console → Target Groups → Create Target Group  
- **Type**: IP addresses
- **Name**: `clinchat-tg-v2` (use unique name if clinchat-targets exists)
- **Protocol**: HTTP
- **Port**: 8080 (matches your container)
- **VPC**: Same as ALB
- **Health Check Path**: `/health`
- **Health Check Port**: 8080

#### **3. Configure ALB Listener**
- **Protocol**: HTTP
- **Port**: 80
- **Action**: Forward to `clinchat-tg-v2` (or whatever target group name you used)

---

### 🔐 **Priority 2: Security Groups (NEEDS VERIFICATION)**

**Navigate to**: EC2 Console → Security Groups

#### **Check/Create Security Group for ALB**:
```
Name: clinchat-alb-sg
Inbound Rules:
- HTTP (80) from 0.0.0.0/0
- HTTPS (443) from 0.0.0.0/0

Outbound Rules:
- All traffic to clinchat-service-sg (port 8080)
```

#### **Check/Update Security Group for ECS Service**:
```
Name: clinchat-service-sg (should exist from deploy script)
Inbound Rules:
- Port 8080 from clinchat-alb-sg
- Port 8080 from your IP (for testing)

Outbound Rules:
- HTTPS (443) to 0.0.0.0/0 (for API calls)
- All traffic (for dependencies)
```

---

### 📊 **Priority 3: ECS Service Update (REQUIRED)**

**Navigate to**: ECS Console → Clusters → clinchat-cluster → Services → clinchat-service

#### **Update Service Configuration**:
1. **Click "Update Service"**
2. **Load Balancing Section**:
   - **Load balancer type**: Application Load Balancer
   - **Load balancer name**: Select `clinchat-alb`
   - **Container to load balance**: clinchat-container:8080
   - **Target group name**: Select `clinchat-tg-v2` (or whatever target group name you created)

3. **Service Discovery** (Optional but recommended):
   - Enable service discovery
   - Namespace: Create new `clinchat.local`
   - Service name: `api`

---

### 🔍 **Priority 4: CloudWatch Logs Verification**

**Navigate to**: CloudWatch Console → Log Groups

#### **Verify Log Group Exists**:
- **Log Group**: `/ecs/clinchat-rag`
- **Region**: eu-north-1
- **Status**: Should exist (created by deploy script)

If missing, create manually:
```
Name: /ecs/clinchat-rag
Retention: 7 days (or as needed)
```

---

### 💾 **Priority 5: ECR Repository Check**

**Navigate to**: ECR Console → Repositories

#### **Verify Repository**:
- **Repository**: `clinchat-rag`
- **URI**: `607520774335.dkr.ecr.eu-north-1.amazonaws.com/clinchat-rag`
- **Status**: Should contain images after deployment

---

### 🚨 **Priority 6: IAM Roles Verification**

**Navigate to**: IAM Console → Roles

#### **Check Required Roles Exist**:
1. **`ecsTaskExecutionRole`**
   - Trust policy: ECS Tasks
   - Policies: AmazonECSTaskExecutionRolePolicy

2. **`ecsTaskRole`**  
   - Trust policy: ECS Tasks
   - Policies: Custom policies for your app

3. **`github-actions-role`**
   - Trust policy: GitHub OIDC
   - Policies: ECS, ECR permissions

---

## 🎯 **MOST CRITICAL MISSING PIECE**

### **🚨 APPLICATION LOAD BALANCER - MUST CREATE**

**Your deployment will work internally but won't be accessible from the internet without an ALB.**

**Quick Setup Steps**:
1. Go to AWS Console → EC2 → Load Balancers
2. Create Application Load Balancer (internet-facing)
3. Create Target Group (IP addresses, port 8080, health check /health)
4. Update ECS Service to use the Load Balancer
5. Get the ALB DNS name for public access

**Expected Result**: 
```
Public URL: http://clinchat-alb-xxxxxxxxx.eu-north-1.elb.amazonaws.com
API Health: http://clinchat-alb-xxxxxxxxx.eu-north-1.elb.amazonaws.com/health
API Docs: http://clinchat-alb-xxxxxxxxx.eu-north-1.elb.amazonaws.com/docs
```

---

## 📱 **Quick Verification Commands**

Once ALB is created, test with:
```bash
# Replace with your actual ALB DNS name
curl http://your-alb-dns-name/health
curl http://your-alb-dns-name/docs
```

**The main missing piece is the Application Load Balancer setup. Everything else should be configured by your deploy scripts!** 🎯