# AWS OIDC Setup Script for GitHub Actions
# This script sets up OpenID Connect (OIDC) provider and IAM role for secure GitHub Actions deployment
# Run this script with AWS Administrator privileges

param(
    [string]$GitHubRepo = "reddygautam98/ClinChat-style-RAG-app",
    [string]$AWSRegion = "eu-north-1",
    [string]$RoleName = "github-actions-role",
    [switch]$DryRun = $false
)

Write-Host "🚀 AWS OIDC Setup for GitHub Actions CI/CD" -ForegroundColor Cyan
Write-Host "=" * 50 -ForegroundColor Cyan

# Step 1: Check AWS CLI and credentials
Write-Host "`n📋 Step 1: Checking AWS Prerequisites..." -ForegroundColor Yellow

try {
    $awsIdentity = aws sts get-caller-identity --output json | ConvertFrom-Json
    Write-Host "✅ AWS CLI is configured" -ForegroundColor Green
    Write-Host "   Account ID: $($awsIdentity.Account)" -ForegroundColor Gray
    Write-Host "   User ARN: $($awsIdentity.Arn)" -ForegroundColor Gray
    $accountId = $awsIdentity.Account
} catch {
    Write-Host "❌ AWS CLI not configured or no credentials found" -ForegroundColor Red
    Write-Host "   Run: aws configure" -ForegroundColor Yellow
    exit 1
}

# Step 2: Check if OIDC provider already exists
Write-Host "`n📋 Step 2: Checking existing OIDC provider..." -ForegroundColor Yellow

$oidcProviderArn = $null
try {
    $existingProviders = aws iam list-open-id-connect-providers --output json | ConvertFrom-Json
    $githubProvider = $existingProviders.OpenIDConnectProviderList | Where-Object { $_.Arn -like "*token.actions.githubusercontent.com*" }
    
    if ($githubProvider) {
        $oidcProviderArn = $githubProvider.Arn
        Write-Host "✅ GitHub OIDC provider already exists: $oidcProviderArn" -ForegroundColor Green
    } else {
        Write-Host "⚠️  GitHub OIDC provider not found. Will create new one." -ForegroundColor Yellow
    }
} catch {
    Write-Host "⚠️  Could not check existing OIDC providers" -ForegroundColor Yellow
}

# Step 3: Create OIDC provider if it doesn't exist
if (-not $oidcProviderArn) {
    Write-Host "`n📋 Step 3: Creating GitHub OIDC Provider..." -ForegroundColor Yellow
    
    if ($DryRun) {
        Write-Host "🔍 DRY RUN: Would create OIDC provider for token.actions.githubusercontent.com" -ForegroundColor Magenta
        $oidcProviderArn = "arn:aws:iam::$($accountId):oidc-provider/token.actions.githubusercontent.com"
    } else {
        try {
            $createResult = aws iam create-open-id-connect-provider `
                --url "https://token.actions.githubusercontent.com" `
                --thumbprint-list "6938fd4d98bab03faadb97b34396831e3780aea1" `
                --client-id-list "sts.amazonaws.com" `
                --output json | ConvertFrom-Json
            
            $oidcProviderArn = $createResult.OpenIDConnectProviderArn
            Write-Host "✅ Created OIDC provider: $oidcProviderArn" -ForegroundColor Green
        } catch {
            Write-Host "❌ Failed to create OIDC provider: $($_.Exception.Message)" -ForegroundColor Red
            exit 1
        }
    }
} else {
    Write-Host "`n📋 Step 3: Skipping OIDC provider creation (already exists)" -ForegroundColor Yellow
}

# Step 4: Create IAM trust policy
Write-Host "`n📋 Step 4: Creating IAM Trust Policy..." -ForegroundColor Yellow

$trustPolicy = @{
    Version = "2012-10-17"
    Statement = @(
        @{
            Effect = "Allow"
            Principal = @{
                Federated = $oidcProviderArn
            }
            Action = "sts:AssumeRoleWithWebIdentity"
            Condition = @{
                StringEquals = @{
                    "token.actions.githubusercontent.com:aud" = "sts.amazonaws.com"
                }
                StringLike = @{
                    "token.actions.githubusercontent.com:sub" = "repo:$GitHubRepo`:*"
                }
            }
        }
    )
} | ConvertTo-Json -Depth 10

Write-Host "📄 Trust policy created for repository: $GitHubRepo" -ForegroundColor Gray

# Step 5: Create IAM permissions policy
Write-Host "`n📋 Step 5: Creating IAM Permissions Policy..." -ForegroundColor Yellow

$permissionsPolicy = @{
    Version = "2012-10-17"
    Statement = @(
        @{
            Effect = "Allow"
            Action = @(
                "ecr:BatchCheckLayerAvailability",
                "ecr:GetDownloadUrlForLayer",
                "ecr:BatchGetImage",
                "ecr:GetAuthorizationToken"
            )
            Resource = "*"
        },
        @{
            Effect = "Allow"
            Action = @(
                "ecr:InitiateLayerUpload",
                "ecr:UploadLayerPart",
                "ecr:CompleteLayerUpload",
                "ecr:PutImage",
                "ecr:BatchDeleteImage"
            )
            Resource = "arn:aws:ecr:$AWSRegion`:$accountId`:repository/clinchat-rag"
        },
        @{
            Effect = "Allow"
            Action = @(
                "ecs:UpdateService",
                "ecs:DescribeServices",
                "ecs:DescribeTaskDefinition",
                "ecs:RegisterTaskDefinition"
            )
            Resource = "*"
        },
        @{
            Effect = "Allow"
            Action = @(
                "iam:PassRole"
            )
            Resource = "arn:aws:iam::$accountId`:role/ecsTaskExecutionRole"
        },
        @{
            Effect = "Allow"
            Action = @(
                "logs:CreateLogGroup",
                "logs:CreateLogStream",
                "logs:PutLogEvents"
            )
            Resource = "arn:aws:logs:$AWSRegion`:$accountId`:*"
        }
    )
} | ConvertTo-Json -Depth 10

Write-Host "📄 Permissions policy created with ECS, ECR, and logging permissions" -ForegroundColor Gray

# Step 6: Check if role already exists
Write-Host "`n📋 Step 6: Checking existing IAM role..." -ForegroundColor Yellow

$roleExists = $false
try {
    $existingRole = aws iam get-role --role-name $RoleName --output json 2>$null | ConvertFrom-Json
    if ($existingRole) {
        Write-Host "⚠️  Role '$RoleName' already exists. Will update policies." -ForegroundColor Yellow
        $roleExists = $true
    }
} catch {
    Write-Host "✅ Role '$RoleName' does not exist. Will create new role." -ForegroundColor Green
}

# Step 7: Create or update IAM role
Write-Host "`n📋 Step 7: Creating/Updating IAM Role..." -ForegroundColor Yellow

if ($DryRun) {
    Write-Host "🔍 DRY RUN: Would create/update role: $RoleName" -ForegroundColor Magenta
    Write-Host "🔍 DRY RUN: Trust policy would be applied" -ForegroundColor Magenta
    Write-Host "🔍 DRY RUN: Permissions policy would be attached" -ForegroundColor Magenta
} else {
    try {
        if (-not $roleExists) {
            # Create new role
            $trustPolicyFile = [System.IO.Path]::GetTempFileName()
            $trustPolicy | Out-File -FilePath $trustPolicyFile -Encoding UTF8
            
            $createRoleResult = aws iam create-role `
                --role-name $RoleName `
                --assume-role-policy-document "file://$trustPolicyFile" `
                --description "GitHub Actions role for ECS deployment" `
                --output json | ConvertFrom-Json
            
            Remove-Item $trustPolicyFile -Force
            Write-Host "✅ Created IAM role: $($createRoleResult.Role.Arn)" -ForegroundColor Green
        } else {
            # Update trust policy for existing role
            $trustPolicyFile = [System.IO.Path]::GetTempFileName()
            $trustPolicy | Out-File -FilePath $trustPolicyFile -Encoding UTF8
            
            aws iam update-assume-role-policy `
                --role-name $RoleName `
                --policy-document "file://$trustPolicyFile"
            
            Remove-Item $trustPolicyFile -Force
            Write-Host "✅ Updated trust policy for existing role" -ForegroundColor Green
        }
        
        # Create and attach permissions policy
        $policyName = "$RoleName-permissions"
        $permissionsPolicyFile = [System.IO.Path]::GetTempFileName()
        $permissionsPolicy | Out-File -FilePath $permissionsPolicyFile -Encoding UTF8
        
        # Delete existing policy if it exists
        try {
            aws iam delete-role-policy --role-name $RoleName --policy-name $policyName 2>$null
        } catch {
            # Policy doesn't exist, that's fine
        }
        
        # Attach new policy
        aws iam put-role-policy `
            --role-name $RoleName `
            --policy-name $policyName `
            --policy-document "file://$permissionsPolicyFile"
        
        Remove-Item $permissionsPolicyFile -Force
        Write-Host "✅ Attached permissions policy: $policyName" -ForegroundColor Green
        
    } catch {
        Write-Host "❌ Failed to create/update IAM role: $($_.Exception.Message)" -ForegroundColor Red
        exit 1
    }
}

# Step 8: Get final role ARN
Write-Host "`n📋 Step 8: Getting Role Information..." -ForegroundColor Yellow

if ($DryRun) {
    $finalRoleArn = "arn:aws:iam::$($accountId):role/$RoleName"
    Write-Host "🔍 DRY RUN: Final role ARN would be: $finalRoleArn" -ForegroundColor Magenta
} else {
    try {
        $roleInfo = aws iam get-role --role-name $RoleName --output json | ConvertFrom-Json
        $finalRoleArn = $roleInfo.Role.Arn
        Write-Host "✅ Role ARN: $finalRoleArn" -ForegroundColor Green
    } catch {
        Write-Host "❌ Failed to get role information" -ForegroundColor Red
        exit 1
    }
}

# Step 9: Summary and next steps
Write-Host "`n🎉 SETUP COMPLETE!" -ForegroundColor Green
Write-Host "=" * 50 -ForegroundColor Green

Write-Host "`n📋 SUMMARY:" -ForegroundColor Cyan
Write-Host "✅ OIDC Provider: $oidcProviderArn" -ForegroundColor White
Write-Host "✅ IAM Role: $finalRoleArn" -ForegroundColor White
Write-Host "✅ GitHub Repository: $GitHubRepo" -ForegroundColor White
Write-Host "✅ AWS Region: $AWSRegion" -ForegroundColor White

Write-Host "`n🚀 NEXT STEPS:" -ForegroundColor Yellow
Write-Host "1. Add this secret to your GitHub repository:" -ForegroundColor White
Write-Host "   Secret Name: AWS_ROLE_ARN" -ForegroundColor Cyan
Write-Host "   Secret Value: $finalRoleArn" -ForegroundColor Cyan
Write-Host ""
Write-Host "2. Go to: https://github.com/$GitHubRepo/settings/secrets/actions" -ForegroundColor White
Write-Host "3. Click 'New repository secret'" -ForegroundColor White
Write-Host "4. Add your API keys as secrets:" -ForegroundColor White
Write-Host "   - GOOGLE_GEMINI_API_KEY" -ForegroundColor Cyan
Write-Host "   - GROQ_API_KEY" -ForegroundColor Cyan
Write-Host ""
Write-Host "5. Run the deployment helper script:" -ForegroundColor White
Write-Host "   ./deploy-helper.ps1" -ForegroundColor Cyan

if ($DryRun) {
    Write-Host "`n⚠️  This was a DRY RUN. No actual resources were created." -ForegroundColor Yellow
    Write-Host "   Remove -DryRun parameter to execute for real." -ForegroundColor Yellow
}

Write-Host "`n✨ Your CI/CD pipeline is ready to deploy!" -ForegroundColor Green