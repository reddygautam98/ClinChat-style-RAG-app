# AWS ECS Deployment Helper Script
# This script creates the ECS infrastructure needed for your application
# Run this after setup-aws-oidc.ps1

param(
    [string]$AWSRegion = "eu-north-1",
    [string]$ClusterName = "clinchat-cluster",
    [string]$ServiceName = "clinchat-service",
    [string]$TaskDefinitionName = "clinchat-task",
    [string]$ECRRepositoryName = "clinchat-rag",
    [switch]$DryRun = $false
)

Write-Host "🚀 AWS ECS Infrastructure Setup" -ForegroundColor Cyan
Write-Host "=" * 40 -ForegroundColor Cyan

# Step 1: Check AWS CLI and get account info
Write-Host "`n📋 Step 1: Checking AWS Prerequisites..." -ForegroundColor Yellow

try {
    $awsIdentity = aws sts get-caller-identity --output json | ConvertFrom-Json
    Write-Host "✅ AWS CLI is configured" -ForegroundColor Green
    Write-Host "   Account ID: $($awsIdentity.Account)" -ForegroundColor Gray
    Write-Host "   Region: $AWSRegion" -ForegroundColor Gray
    $accountId = $awsIdentity.Account
} catch {
    Write-Host "❌ AWS CLI not configured or no credentials found" -ForegroundColor Red
    exit 1
}

# Step 2: Create ECR Repository
Write-Host "`n📋 Step 2: Creating ECR Repository..." -ForegroundColor Yellow

try {
    $existingRepo = aws ecr describe-repositories --repository-names $ECRRepositoryName --region $AWSRegion --output json 2>$null | ConvertFrom-Json
    if ($existingRepo) {
        Write-Host "✅ ECR repository '$ECRRepositoryName' already exists" -ForegroundColor Green
        $repoUri = $existingRepo.repositories[0].repositoryUri
    }
} catch {
    Write-Host "⚠️  ECR repository '$ECRRepositoryName' not found. Creating..." -ForegroundColor Yellow
    
    if ($DryRun) {
        Write-Host "🔍 DRY RUN: Would create ECR repository: $ECRRepositoryName" -ForegroundColor Magenta
        $repoUri = "$accountId.dkr.ecr.$AWSRegion.amazonaws.com/$ECRRepositoryName"
    } else {
        try {
            $createRepoResult = aws ecr create-repository --repository-name $ECRRepositoryName --region $AWSRegion --output json | ConvertFrom-Json
            $repoUri = $createRepoResult.repository.repositoryUri
            Write-Host "✅ Created ECR repository: $repoUri" -ForegroundColor Green
        } catch {
            Write-Host "❌ Failed to create ECR repository: $($_.Exception.Message)" -ForegroundColor Red
            exit 1
        }
    }
}

# Step 3: Create ECS Cluster
Write-Host "`n📋 Step 3: Creating ECS Cluster..." -ForegroundColor Yellow

try {
    $existingCluster = aws ecs describe-clusters --clusters $ClusterName --region $AWSRegion --output json 2>$null | ConvertFrom-Json
    if ($existingCluster.clusters -and $existingCluster.clusters[0].status -eq "ACTIVE") {
        Write-Host "✅ ECS cluster '$ClusterName' already exists and is active" -ForegroundColor Green
    } else {
        Write-Host "⚠️  ECS cluster '$ClusterName' not found or inactive. Creating..." -ForegroundColor Yellow
        
        if ($DryRun) {
            Write-Host "🔍 DRY RUN: Would create ECS cluster: $ClusterName" -ForegroundColor Magenta
        } else {
            $createClusterResult = aws ecs create-cluster --cluster-name $ClusterName --region $AWSRegion --output json | ConvertFrom-Json
            Write-Host "✅ Created ECS cluster: $($createClusterResult.cluster.clusterArn)" -ForegroundColor Green
        }
    }
} catch {
    Write-Host "❌ Failed to create ECS cluster: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}

# Step 4: Check/Create ECS Task Execution Role
Write-Host "`n📋 Step 4: Checking ECS Task Execution Role..." -ForegroundColor Yellow

$taskExecutionRoleName = "ecsTaskExecutionRole"
try {
    $existingTaskRole = aws iam get-role --role-name $taskExecutionRoleName --output json 2>$null | ConvertFrom-Json
    if ($existingTaskRole) {
        Write-Host "✅ ECS task execution role already exists" -ForegroundColor Green
    }
} catch {
    Write-Host "⚠️  Creating ECS task execution role..." -ForegroundColor Yellow
    
    $taskRoleTrustPolicy = @{
        Version = "2012-10-17"
        Statement = @(
            @{
                Effect = "Allow"
                Principal = @{
                    Service = "ecs-tasks.amazonaws.com"
                }
                Action = "sts:AssumeRole"
            }
        )
    } | ConvertTo-Json -Depth 10
    
    if ($DryRun) {
        Write-Host "🔍 DRY RUN: Would create ECS task execution role" -ForegroundColor Magenta
    } else {
        $trustPolicyFile = [System.IO.Path]::GetTempFileName()
        $taskRoleTrustPolicy | Out-File -FilePath $trustPolicyFile -Encoding UTF8
        
        $createRoleResult = aws iam create-role `
            --role-name $taskExecutionRoleName `
            --assume-role-policy-document "file://$trustPolicyFile" `
            --description "ECS task execution role" `
            --output json | ConvertFrom-Json
        
        # Attach the AWS managed policy
        aws iam attach-role-policy `
            --role-name $taskExecutionRoleName `
            --policy-arn "arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy"
        
        Remove-Item $trustPolicyFile -Force
        Write-Host "✅ Created ECS task execution role" -ForegroundColor Green
    }
}

# Step 5: Register Initial Task Definition
Write-Host "`n📋 Step 5: Registering Task Definition..." -ForegroundColor Yellow

$taskDefinition = @{
    family = $TaskDefinitionName
    networkMode = "awsvpc"
    requiresCompatibilities = @("FARGATE")
    cpu = "256"
    memory = "512"
    executionRoleArn = "arn:aws:iam::$accountId`:role/$taskExecutionRoleName"
    containerDefinitions = @(
        @{
            name = "clinchat-container"
            image = "$repoUri`:latest"
            portMappings = @(
                @{
                    containerPort = 8080
                    protocol = "tcp"
                }
            )
            environment = @(
                @{ name = "GOOGLE_GEMINI_API_KEY"; value = "your_google_gemini_api_key_here" },
                @{ name = "GROQ_API_KEY"; value = "your_groq_api_key_here" },
                @{ name = "FUSION_STRATEGY"; value = "weighted_average" },
                @{ name = "GEMINI_WEIGHT"; value = "0.6" },
                @{ name = "GROQ_WEIGHT"; value = "0.4" },
                @{ name = "PORT"; value = "8080" },
                @{ name = "DEBUG"; value = "True" },
                @{ name = "HOST"; value = "0.0.0.0" }
            )
            logConfiguration = @{
                logDriver = "awslogs"
                options = @{
                    "awslogs-group" = "/ecs/$TaskDefinitionName"
                    "awslogs-region" = $AWSRegion
                    "awslogs-stream-prefix" = "ecs"
                }
            }
            essential = $true
        }
    )
} | ConvertTo-Json -Depth 10

if ($DryRun) {
    Write-Host "🔍 DRY RUN: Would register task definition: $TaskDefinitionName" -ForegroundColor Magenta
} else {
    # Create CloudWatch log group first
    try {
        aws logs create-log-group --log-group-name "/ecs/$TaskDefinitionName" --region $AWSRegion 2>$null
        Write-Host "✅ Created CloudWatch log group" -ForegroundColor Green
    } catch {
        Write-Host "⚠️  Log group may already exist" -ForegroundColor Yellow
    }
    
    $taskDefFile = [System.IO.Path]::GetTempFileName()
    $taskDefinition | Out-File -FilePath $taskDefFile -Encoding UTF8
    
    try {
        $registerResult = aws ecs register-task-definition --cli-input-json "file://$taskDefFile" --region $AWSRegion --output json | ConvertFrom-Json
        Write-Host "✅ Registered task definition: $($registerResult.taskDefinition.taskDefinitionArn)" -ForegroundColor Green
    } catch {
        Write-Host "❌ Failed to register task definition: $($_.Exception.Message)" -ForegroundColor Red
    }
    
    Remove-Item $taskDefFile -Force
}

# Step 6: Get Default VPC and Subnets
Write-Host "`n📋 Step 6: Getting VPC Information..." -ForegroundColor Yellow

try {
    $defaultVpc = aws ec2 describe-vpcs --filters "Name=isDefault,Values=true" --region $AWSRegion --output json | ConvertFrom-Json
    if ($defaultVpc.Vpcs.Count -eq 0) {
        Write-Host "❌ No default VPC found. You'll need to specify VPC and subnets manually." -ForegroundColor Red
        exit 1
    }
    
    $vpcId = $defaultVpc.Vpcs[0].VpcId
    Write-Host "✅ Found default VPC: $vpcId" -ForegroundColor Green
    
    $subnets = aws ec2 describe-subnets --filters "Name=vpc-id,Values=$vpcId" --region $AWSRegion --output json | ConvertFrom-Json
    $publicSubnets = $subnets.Subnets | Where-Object { $_.MapPublicIpOnLaunch -eq $true }
    
    if ($publicSubnets.Count -eq 0) {
        Write-Host "❌ No public subnets found in default VPC" -ForegroundColor Red
        exit 1
    }
    
    $subnetIds = $publicSubnets | Select-Object -First 2 | ForEach-Object { $_.SubnetId }
    Write-Host "✅ Found public subnets: $($subnetIds -join ', ')" -ForegroundColor Green
    
} catch {
    Write-Host "❌ Failed to get VPC information: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}

# Step 7: Create Security Group
Write-Host "`n📋 Step 7: Creating Security Group..." -ForegroundColor Yellow

$sgName = "$ServiceName-sg"
try {
    $existingSg = aws ec2 describe-security-groups --filters "Name=group-name,Values=$sgName" "Name=vpc-id,Values=$vpcId" --region $AWSRegion --output json 2>$null | ConvertFrom-Json
    if ($existingSg.SecurityGroups.Count -gt 0) {
        $sgId = $existingSg.SecurityGroups[0].GroupId
        Write-Host "✅ Security group '$sgName' already exists: $sgId" -ForegroundColor Green
    }
} catch {
    Write-Host "⚠️  Creating security group..." -ForegroundColor Yellow
    
    if ($DryRun) {
        Write-Host "🔍 DRY RUN: Would create security group: $sgName" -ForegroundColor Magenta
        $sgId = "sg-dryrun123"
    } else {
        $createSgResult = aws ec2 create-security-group --group-name $sgName --description "Security group for $ServiceName" --vpc-id $vpcId --region $AWSRegion --output json | ConvertFrom-Json
        $sgId = $createSgResult.GroupId
        
        # Add inbound rule for port 8080
        aws ec2 authorize-security-group-ingress --group-id $sgId --protocol tcp --port 8080 --cidr 0.0.0.0/0 --region $AWSRegion
        
        Write-Host "✅ Created security group: $sgId" -ForegroundColor Green
    }
}

# Step 8: Create ECS Service
Write-Host "`n📋 Step 8: Creating ECS Service..." -ForegroundColor Yellow

try {
    $existingService = aws ecs describe-services --cluster $ClusterName --services $ServiceName --region $AWSRegion --output json 2>$null | ConvertFrom-Json
    if ($existingService.services -and $existingService.services[0].status -ne "INACTIVE") {
        Write-Host "✅ ECS service '$ServiceName' already exists" -ForegroundColor Green
    } else {
        Write-Host "⚠️  Creating ECS service..." -ForegroundColor Yellow
        
        if ($DryRun) {
            Write-Host "🔍 DRY RUN: Would create ECS service: $ServiceName" -ForegroundColor Magenta
        } else {
            $serviceConfig = @{
                serviceName = $ServiceName
                cluster = $ClusterName
                taskDefinition = $TaskDefinitionName
                desiredCount = 1
                launchType = "FARGATE"
                networkConfiguration = @{
                    awsvpcConfiguration = @{
                        subnets = $subnetIds
                        securityGroups = @($sgId)
                        assignPublicIp = "ENABLED"
                    }
                }
                enableExecuteCommand = $true
            } | ConvertTo-Json -Depth 10
            
            $serviceFile = [System.IO.Path]::GetTempFileName()
            $serviceConfig | Out-File -FilePath $serviceFile -Encoding UTF8
            
            $createServiceResult = aws ecs create-service --cli-input-json "file://$serviceFile" --region $AWSRegion --output json | ConvertFrom-Json
            Write-Host "✅ Created ECS service: $($createServiceResult.service.serviceArn)" -ForegroundColor Green
            
            Remove-Item $serviceFile -Force
        }
    }
} catch {
    Write-Host "❌ Failed to create ECS service: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}

# Summary
Write-Host "`n🎉 ECS INFRASTRUCTURE SETUP COMPLETE!" -ForegroundColor Green
Write-Host "=" * 50 -ForegroundColor Green

Write-Host "`n📋 CREATED RESOURCES:" -ForegroundColor Cyan
Write-Host "✅ ECR Repository: $repoUri" -ForegroundColor White
Write-Host "✅ ECS Cluster: $ClusterName" -ForegroundColor White
Write-Host "✅ Task Definition: $TaskDefinitionName" -ForegroundColor White
Write-Host "✅ ECS Service: $ServiceName" -ForegroundColor White
Write-Host "✅ Security Group: $sgId" -ForegroundColor White

Write-Host "`n🚀 NEXT STEPS:" -ForegroundColor Yellow
Write-Host "1. Your GitHub Actions pipeline will now be able to:" -ForegroundColor White
Write-Host "   - Build and push Docker images to ECR" -ForegroundColor Gray
Write-Host "   - Update the ECS service with new deployments" -ForegroundColor Gray
Write-Host ""
Write-Host "2. Make sure you have added these GitHub secrets:" -ForegroundColor White
Write-Host "   - AWS_ROLE_ARN (from previous script)" -ForegroundColor Cyan
Write-Host "   - GOOGLE_GEMINI_API_KEY" -ForegroundColor Cyan
Write-Host "   - GROQ_API_KEY" -ForegroundColor Cyan
Write-Host ""
Write-Host "3. Push a commit to trigger your first deployment!" -ForegroundColor White

if ($DryRun) {
    Write-Host "`n⚠️  This was a DRY RUN. No actual resources were created." -ForegroundColor Yellow
    Write-Host "   Remove -DryRun parameter to execute for real." -ForegroundColor Yellow
}

Write-Host "`n✨ Your ECS infrastructure is ready for CI/CD deployments!" -ForegroundColor Green