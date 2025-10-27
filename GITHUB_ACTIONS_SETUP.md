# GitHub Actions CI/CD Setup Guide

This guide will help you set up GitHub Actions for continuous integration and deployment of the HealthAI RAG Application.

## 🎯 Overview

The CI/CD pipeline includes:
- **Automated Testing**: Python backend and React frontend tests
- **Code Quality**: Linting, type checking, and coverage reporting  
- **Security Scanning**: CodeQL analysis and dependency vulnerability checks
- **Docker Build & Push**: Multi-platform container builds to AWS ECR
- **AWS Deployment**: Automated deployment to ECS with blue-green strategy
- **Performance Testing**: Load testing and health checks

## 📋 Prerequisites

Before setting up GitHub Actions, ensure you have:

1. **GitHub Repository**: Your code repository with appropriate permissions
2. **AWS Account**: With necessary IAM roles and permissions
3. **AWS CLI**: Configured locally for initial setup
4. **Docker Hub Account**: (Optional) For additional registry options

## 🔧 Initial Setup

### 1. Repository Configuration

First, ensure your repository has the correct structure:

```bash
# Clone your repository
git clone https://github.com/your-username/ClinChat-style-RAG-app.git
cd ClinChat-style-RAG-app

# Verify the GitHub Actions workflow exists
ls -la .github/workflows/
```

### 2. Required GitHub Secrets

Navigate to your repository on GitHub and set up the following secrets:

**Repository Settings → Secrets and Variables → Actions**

#### Essential Secrets:

```bash
# AWS Configuration
AWS_ACCOUNT_ID=123456789012
AWS_REGION=eu-north-1

# API Keys for Testing
GROQ_API_KEY=your_groq_api_key_here
GOOGLE_API_KEY=your_google_api_key_here
OPENAI_API_KEY=your_openai_api_key_here

# Code Coverage
CODECOV_TOKEN=your_codecov_token

# Docker Registry (if using Docker Hub)
DOCKER_USERNAME=your_docker_username
DOCKER_PASSWORD=your_docker_password

# Production Environment Variables
PRODUCTION_DATABASE_URL=your_production_db_url
REDIS_URL=your_redis_url
```

#### AWS OIDC Configuration (Recommended):

Instead of long-lived AWS access keys, use OpenID Connect:

```bash
# AWS OIDC Role ARN
AWS_ROLE_TO_ASSUME=arn:aws:iam::123456789012:role/GitHubActionsRole

# ECR Repository Details
ECR_REPOSITORY=clinchat-rag
ECS_SERVICE=clinchat-service
ECS_CLUSTER=clinchat-cluster
ECS_TASK_DEFINITION=clinchat-task
```

### 3. AWS OIDC Setup Script

Run this PowerShell script to configure AWS OIDC (requires AWS CLI):

```powershell
# Run the setup script
.\setup-aws-oidc.ps1 -RepositoryOwner "your-username" -RepositoryName "ClinChat-style-RAG-app"
```

Or manually create the IAM role:

```bash
# Create trust policy for GitHub Actions
aws iam create-role --role-name GitHubActionsRole --assume-role-policy-document file://github-actions-trust-policy.json

# Attach necessary policies
aws iam attach-role-policy --role-name GitHubActionsRole --policy-arn arn:aws:iam::aws:policy/AmazonECS_FullAccess
aws iam attach-role-policy --role-name GitHubActionsRole --policy-arn arn:aws:iam::aws:policy/AmazonEC2ContainerRegistryPowerUser
```

## 🚀 Workflow Configuration

### Current Workflow Structure

The `.github/workflows/ci-cd.yml` includes these jobs:

1. **Test Job**: 
   - Python 3.12 setup
   - Dependency installation with build tools
   - Pytest execution with coverage
   - Upload test results and coverage

2. **Frontend Test Job**:
   - Node.js 18 setup
   - npm dependency installation
   - ESLint and TypeScript checks
   - Jest test execution

3. **Security Scan Job**:
   - CodeQL analysis for security vulnerabilities
   - Dependency vulnerability scanning

4. **Build Job**:
   - Multi-platform Docker builds (AMD64/ARM64)
   - Push to AWS ECR
   - Generate deployment artifacts

5. **Deploy Job**:
   - Deploy to AWS ECS
   - Blue-green deployment strategy
   - Health check validation

### Customizing the Workflow

#### Environment Variables

Modify the workflow environment variables in `.github/workflows/ci-cd.yml`:

```yaml
env:
  AWS_REGION: eu-north-1              # Change to your AWS region
  ECR_REPOSITORY: clinchat-rag        # Your ECR repository name
  ECS_SERVICE: clinchat-service       # Your ECS service name
  ECS_CLUSTER: clinchat-cluster       # Your ECS cluster name
  ECS_TASK_DEFINITION: clinchat-task  # Your ECS task definition name
```

#### Adding New Jobs

To add custom jobs, extend the workflow:

```yaml
performance-test:
  needs: [test, frontend-test]
  runs-on: ubuntu-latest
  steps:
    - name: Checkout code
      uses: actions/checkout@v4
    
    - name: Run performance tests
      run: |
        # Your performance testing commands
        python scripts/load_test.py
```

## 🔍 Monitoring and Troubleshooting

### Viewing Workflow Results

1. Navigate to your repository on GitHub
2. Click the **Actions** tab
3. Select a workflow run to view details
4. Check individual job logs for errors

### Common Issues and Solutions

#### 1. Python Package Installation Failures

**Issue**: Packages like `spacy` or `transformers` fail to install

**Solution**: Update the workflow to install build dependencies:

```yaml
- name: Install system dependencies
  run: |
    sudo apt-get update
    sudo apt-get install -y build-essential gcc g++ make
    sudo apt-get install -y python3-dev python3-setuptools
```

#### 2. AWS Authentication Errors

**Issue**: AWS operations fail with authentication errors

**Solution**: Verify OIDC setup or check AWS credentials:

```yaml
- name: Configure AWS credentials
  uses: aws-actions/configure-aws-credentials@v4
  with:
    role-to-assume: ${{ secrets.AWS_ROLE_TO_ASSUME }}
    aws-region: ${{ env.AWS_REGION }}
```

#### 3. Docker Build Failures

**Issue**: Docker builds fail due to platform compatibility

**Solution**: Use buildx for multi-platform builds:

```yaml
- name: Set up Docker Buildx
  uses: docker/setup-buildx-action@v3

- name: Build and push Docker image
  uses: docker/build-push-action@v5
  with:
    platforms: linux/amd64,linux/arm64
    push: true
    tags: ${{ steps.login-ecr.outputs.registry }}/${{ env.ECR_REPOSITORY }}:${{ github.sha }}
```

#### 4. Test Coverage Issues

**Issue**: Coverage reports are not uploading to Codecov

**Solution**: Ensure the token is correct and the file path exists:

```yaml
- name: Upload coverage reports
  uses: codecov/codecov-action@v4
  with:
    token: ${{ secrets.CODECOV_TOKEN }}
    file: ./coverage.xml
    fail_ci_if_error: false
```

### Performance Optimization

#### 1. Caching Dependencies

Speed up builds with dependency caching:

```yaml
- name: Cache pip dependencies
  uses: actions/cache@v3
  with:
    path: ~/.cache/pip
    key: ${{ runner.os }}-pip-${{ hashFiles('requirements.txt') }}
    restore-keys: |
      ${{ runner.os }}-pip-
```

#### 2. Parallel Job Execution

Run independent jobs in parallel:

```yaml
strategy:
  matrix:
    python-version: [3.11, 3.12]
    os: [ubuntu-latest, windows-latest]
```

## 📊 Advanced Features

### 1. Environment-Specific Deployments

Deploy to different environments based on branches:

```yaml
deploy-staging:
  if: github.ref == 'refs/heads/develop'
  environment: staging
  # Staging deployment steps

deploy-production:
  if: github.ref == 'refs/heads/main'
  environment: production
  # Production deployment steps
```

### 2. Manual Deployment Approval

Add manual approval for production deployments:

```yaml
deploy-production:
  environment: 
    name: production
    url: https://your-app.com
  # Deployment steps
```

### 3. Slack/Teams Notifications

Add notification steps:

```yaml
- name: Notify Slack
  if: failure()
  uses: 8398a7/action-slack@v3
  with:
    status: failure
    webhook_url: ${{ secrets.SLACK_WEBHOOK }}
```

### 4. Automated Security Scanning

Enhance security with additional scans:

```yaml
security-scan:
  runs-on: ubuntu-latest
  steps:
    - name: Run Trivy vulnerability scanner
      uses: aquasecurity/trivy-action@master
      with:
        image-ref: '${{ steps.login-ecr.outputs.registry }}/${{ env.ECR_REPOSITORY }}:${{ github.sha }}'
        format: 'sarif'
        output: 'trivy-results.sarif'
```

## 🔐 Security Best Practices

1. **Use OIDC instead of long-lived keys**
2. **Store secrets in GitHub Secrets, not in code**
3. **Limit IAM permissions to minimum required**
4. **Regularly rotate secrets and tokens**
5. **Use dependency scanning and vulnerability alerts**
6. **Enable branch protection rules**

## 📝 Validation Checklist

Before going live, verify:

- [ ] All required secrets are configured
- [ ] AWS OIDC role has necessary permissions
- [ ] ECR repository exists and is accessible
- [ ] ECS cluster and service are configured
- [ ] Task definition is valid and deployable
- [ ] Health checks are properly configured
- [ ] Monitoring and alerting are set up
- [ ] Rollback procedures are tested

## 🔗 Additional Resources

- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [AWS OIDC for GitHub Actions](https://docs.github.com/en/actions/deployment/security-hardening-your-deployments/configuring-openid-connect-in-amazon-web-services)
- [Docker Build Push Action](https://github.com/docker/build-push-action)
- [AWS Actions for GitHub](https://github.com/aws-actions)

## 🚨 Emergency Procedures

### Rolling Back Deployments

If deployment fails, manually rollback using AWS CLI:

```bash
# Get previous task definition
aws ecs describe-task-definition --task-definition clinchat-task

# Update service to previous revision
aws ecs update-service --cluster clinchat-cluster --service clinchat-service --task-definition clinchat-task:PREVIOUS_REVISION
```

### Disabling Workflows

To temporarily disable workflows:

```bash
# Disable workflow
gh workflow disable ci-cd.yml

# Re-enable workflow
gh workflow enable ci-cd.yml
```

---

**Need help?** Check the [troubleshooting section](#monitoring-and-troubleshooting) or create an issue in the repository.