# Docker Setup Guide

Complete guide for containerizing and running the HealthAI RAG Application with Docker and Docker Compose.

## 🐳 Overview

This guide covers:
- **Docker Configuration**: Optimized Dockerfiles for development and production
- **Docker Compose**: Multi-service orchestration with networking
- **Environment Management**: Development, staging, and production configurations
- **Performance Optimization**: Build optimization and caching strategies
- **Security**: Container security best practices
- **Monitoring**: Container health checks and logging
- **Troubleshooting**: Common issues and solutions

## 📋 Prerequisites

Ensure you have the following installed:

1. **Docker Desktop**: Version 4.0+ (includes Docker Compose V2)
   - Windows: [Download Docker Desktop](https://www.docker.com/products/docker-desktop/)
   - macOS: [Download Docker Desktop](https://www.docker.com/products/docker-desktop/)
   - Linux: [Install Docker Engine](https://docs.docker.com/engine/install/)

2. **System Requirements**:
   - Windows: WSL 2 enabled (for Docker Desktop)
   - RAM: 4GB minimum, 8GB recommended
   - Storage: 10GB free space minimum

3. **Verify Installation**:
   ```bash
   docker --version
   docker compose version
   ```

## 🚀 Quick Start

### 1. Clone and Navigate

```bash
git clone https://github.com/reddygautam98/ClinChat-style-RAG-app.git
cd ClinChat-style-RAG-app
```

### 2. Environment Setup

Create environment files:

```bash
# Development environment
cp .env.example .env.dev

# Production environment  
cp .env.example .env.prod
```

Edit the environment files with your configuration:

**.env.dev** (Development):
```bash
# API Keys
GROQ_API_KEY=your_groq_key_here
GOOGLE_API_KEY=your_google_key_here
OPENAI_API_KEY=your_openai_key_here

# Development Database
DATABASE_URL=postgresql://healthai:password@postgres:5432/healthai_dev
REDIS_URL=redis://redis:6379/0

# Application Settings
ENVIRONMENT=development
DEBUG=true
LOG_LEVEL=DEBUG
WORKERS=1

# Frontend Settings
REACT_APP_API_URL=http://localhost:8000
REACT_APP_ENVIRONMENT=development
```

**.env.prod** (Production):
```bash
# API Keys (use secrets management in production)
GROQ_API_KEY=your_groq_key_here
GOOGLE_API_KEY=your_google_key_here
OPENAI_API_KEY=your_openai_key_here

# Production Database
DATABASE_URL=postgresql://healthai:secure_password@postgres:5432/healthai
REDIS_URL=redis://redis:6379/0

# Application Settings
ENVIRONMENT=production
DEBUG=false
LOG_LEVEL=INFO
WORKERS=4

# Security
SECRET_KEY=your_super_secure_secret_key_here
ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com

# Frontend Settings
REACT_APP_API_URL=https://api.yourdomain.com
REACT_APP_ENVIRONMENT=production
```

### 3. Development Setup

```bash
# Start development environment
docker compose -f docker-compose.dev.yml up -d

# View logs
docker compose -f docker-compose.dev.yml logs -f

# Access the application
# Backend API: http://localhost:8000
# Frontend: http://localhost:3000
# API Documentation: http://localhost:8000/docs
```

### 4. Production Setup

```bash
# Build and start production environment
docker compose -f docker-compose.prod.yml up -d

# View logs
docker compose -f docker-compose.prod.yml logs -f

# Access through load balancer
# Application: http://localhost (port 80)
# HTTPS: http://localhost:443 (if SSL configured)
```

## 🏗️ Docker Configuration Details

### Dockerfile Structure

The project includes multiple Dockerfile configurations:

#### 1. **Dockerfile** (Standard Build)
```dockerfile
# Use Python 3.12 slim for balance of features and size
FROM python:3.12.1-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PYTHONPATH=/app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy and install Python dependencies
COPY requirements.txt .
RUN pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY src/ ./src/
COPY data/ ./data/

# Create non-root user
RUN useradd --create-home --shell /bin/bash --uid 1000 app && \
    chown -R app:app /app
USER app

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Expose port
EXPOSE 8000

# Run application
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

#### 2. **Dockerfile.optimized** (Production Optimized)
```dockerfile
# Multi-stage build for smaller production image
FROM python:3.12.1-slim as builder

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Create virtual environment
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Copy and install requirements
COPY requirements.txt .
RUN pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Production stage
FROM python:3.12.1-slim

# Copy virtual environment from builder
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Runtime dependencies only
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app

WORKDIR /app

# Copy application code
COPY src/ ./src/
COPY data/ ./data/

# Create non-root user
RUN useradd --create-home --shell /bin/bash --uid 1000 app && \
    chown -R app:app /app
USER app

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

EXPOSE 8000

# Use gunicorn for production
CMD ["gunicorn", "src.main:app", "-w", "4", "-k", "uvicorn.workers.UvicornWorker", "--bind", "0.0.0.0:8000"]
```

#### 3. **Dockerfile.fast** (Development Build)
```dockerfile
FROM python:3.12.1-slim

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy requirements and install (cached layer)
COPY requirements.txt .
RUN pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy source code (changes frequently)
COPY . .

# Create app user
RUN useradd --create-home --uid 1000 app && chown -R app:app /app
USER app

EXPOSE 8000

# Development server with auto-reload
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
```

### Frontend Dockerfile

**frontend/Dockerfile** (Production):
```dockerfile
# Build stage
FROM node:18-alpine as builder

WORKDIR /app

# Copy package files
COPY package*.json ./
RUN npm ci --only=production

# Copy source and build
COPY . .
RUN npm run build

# Production stage
FROM nginx:1.25.3-alpine

# Copy built app
COPY --from=builder /app/build /usr/share/nginx/html

# Copy nginx configuration
COPY nginx.conf /etc/nginx/nginx.conf

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD wget --no-verbose --tries=1 --spider http://localhost/ || exit 1

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
```

**frontend/Dockerfile.dev** (Development):
```dockerfile
FROM node:18-alpine

WORKDIR /app

# Install dependencies
COPY package*.json ./
RUN npm install

# Copy source code
COPY . .

EXPOSE 3000

# Development server with hot reload
CMD ["npm", "start"]
```

## 🔧 Docker Compose Configurations

### Development Configuration

**docker-compose.dev.yml**:
```yaml
version: '3.8'

services:
  # Backend API
  healthai-api:
    build:
      context: .
      dockerfile: Dockerfile.fast
    container_name: healthai-api-dev
    ports:
      - "8000:8000"
    environment:
      - ENVIRONMENT=development
      - DEBUG=true
      - DATABASE_URL=postgresql://healthai:password@postgres:5432/healthai_dev
      - REDIS_URL=redis://redis:6379/0
    env_file:
      - .env.dev
    volumes:
      - .:/app
      - /app/node_modules  # Prevent overwriting node_modules
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy
    networks:
      - healthai-network
    restart: unless-stopped

  # Frontend React App
  healthai-frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile.dev
    container_name: healthai-frontend-dev
    ports:
      - "3000:3000"
    environment:
      - REACT_APP_API_URL=http://localhost:8000
      - REACT_APP_ENVIRONMENT=development
    volumes:
      - ./frontend:/app
      - /app/node_modules
    depends_on:
      - healthai-api
    networks:
      - healthai-network
    restart: unless-stopped

  # PostgreSQL Database
  postgres:
    image: postgres:15.4-alpine
    container_name: healthai-postgres-dev
    environment:
      - POSTGRES_DB=healthai_dev
      - POSTGRES_USER=healthai
      - POSTGRES_PASSWORD=password
    ports:
      - "5432:5432"
    volumes:
      - postgres_data_dev:/var/lib/postgresql/data
      - ./scripts/init-db.sql:/docker-entrypoint-initdb.d/init-db.sql
    networks:
      - healthai-network
    restart: unless-stopped
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U healthai -d healthai_dev"]
      interval: 10s
      timeout: 5s
      retries: 5

  # Redis Cache
  redis:
    image: redis:7.2-alpine
    container_name: healthai-redis-dev
    ports:
      - "6379:6379"
    volumes:
      - redis_data_dev:/data
    networks:
      - healthai-network
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 3s
      retries: 5

  # Monitoring (Optional)
  prometheus:
    image: prom/prometheus:latest
    container_name: healthai-prometheus-dev
    ports:
      - "9090:9090"
    volumes:
      - ./config/prometheus.yml:/etc/prometheus/prometheus.yml
      - prometheus_data_dev:/prometheus
    networks:
      - healthai-network
    restart: unless-stopped

networks:
  healthai-network:
    driver: bridge

volumes:
  postgres_data_dev:
  redis_data_dev:
  prometheus_data_dev:
```

### Production Configuration

**docker-compose.prod.yml**:
```yaml
version: '3.8'

services:
  # Load Balancer
  nginx:
    image: nginx:1.25.3-alpine
    container_name: healthai-nginx
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./config/nginx.conf:/etc/nginx/nginx.conf:ro
      - ./config/ssl:/etc/nginx/ssl:ro
      - nginx_logs:/var/log/nginx
    depends_on:
      healthai-app-1:
        condition: service_healthy
      healthai-app-2:
        condition: service_healthy
    restart: unless-stopped
    networks:
      - healthai-network
    deploy:
      resources:
        limits:
          memory: 128M
          cpus: '0.2'

  # Application Instances (Scaled)
  healthai-app-1:
    build:
      context: .
      dockerfile: Dockerfile.optimized
    container_name: healthai-app-1
    environment:
      - APP_INSTANCE=1
      - WORKERS=2
    env_file:
      - .env.prod
    volumes:
      - ./data:/app/data:rw
      - ./logs:/app/logs:rw
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy
    restart: unless-stopped
    networks:
      - healthai-network
    deploy:
      resources:
        limits:
          memory: 1G
          cpus: '0.5'
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s

  healthai-app-2:
    build:
      context: .
      dockerfile: Dockerfile.optimized
    container_name: healthai-app-2
    environment:
      - APP_INSTANCE=2
      - WORKERS=2
    env_file:
      - .env.prod
    volumes:
      - ./data:/app/data:rw
      - ./logs:/app/logs:rw
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy
    restart: unless-stopped
    networks:
      - healthai-network
    deploy:
      resources:
        limits:
          memory: 1G
          cpus: '0.5'
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s

  # Frontend
  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile
    container_name: healthai-frontend
    restart: unless-stopped
    networks:
      - healthai-network
    deploy:
      resources:
        limits:
          memory: 256M
          cpus: '0.2'

  # Database
  postgres:
    image: postgres:15.4-alpine
    container_name: healthai-postgres
    environment:
      - POSTGRES_DB=healthai
      - POSTGRES_USER=healthai
      - POSTGRES_PASSWORD_FILE=/run/secrets/postgres_password
    secrets:
      - postgres_password
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./backups:/backups
    networks:
      - healthai-network
    restart: unless-stopped
    deploy:
      resources:
        limits:
          memory: 512M
          cpus: '0.3'
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U healthai -d healthai"]
      interval: 30s
      timeout: 10s
      retries: 5

  # Redis
  redis:
    image: redis:7.2-alpine
    container_name: healthai-redis
    command: redis-server --requirepass ${REDIS_PASSWORD}
    volumes:
      - redis_data:/data
    networks:
      - healthai-network
    restart: unless-stopped
    deploy:
      resources:
        limits:
          memory: 256M
          cpus: '0.2'
    healthcheck:
      test: ["CMD", "redis-cli", "--raw", "incr", "ping"]
      interval: 30s
      timeout: 3s
      retries: 5

  # Monitoring Stack
  prometheus:
    image: prom/prometheus:latest
    container_name: healthai-prometheus
    ports:
      - "9090:9090"
    volumes:
      - ./config/prometheus.yml:/etc/prometheus/prometheus.yml:ro
      - prometheus_data:/prometheus
    networks:
      - healthai-network
    restart: unless-stopped

  grafana:
    image: grafana/grafana:latest
    container_name: healthai-grafana
    ports:
      - "3001:3000"
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=secure_password
    volumes:
      - grafana_data:/var/lib/grafana
      - ./config/grafana:/etc/grafana/provisioning
    networks:
      - healthai-network
    restart: unless-stopped

secrets:
  postgres_password:
    file: ./secrets/postgres_password.txt

networks:
  healthai-network:
    driver: bridge

volumes:
  postgres_data:
  redis_data:
  nginx_logs:
  prometheus_data:
  grafana_data:
```

### Rate Limiting Configuration

**docker-compose.rate-limiting.yml**:
```yaml
version: '3.8'

services:
  # Rate Limiting with Redis
  rate-limiter:
    image: nginx:1.25.3-alpine
    container_name: healthai-rate-limiter
    ports:
      - "80:80"
    volumes:
      - ./config/nginx-rate-limit.conf:/etc/nginx/nginx.conf:ro
    depends_on:
      - redis
      - healthai-app
    networks:
      - healthai-network
    restart: unless-stopped

  healthai-app:
    build:
      context: .
      dockerfile: Dockerfile.optimized
    container_name: healthai-app-rate-limited
    env_file:
      - .env.prod
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy
    networks:
      - healthai-network
    restart: unless-stopped

  redis:
    image: redis:7.2-alpine
    container_name: healthai-redis-rate-limit
    volumes:
      - redis_data:/data
    networks:
      - healthai-network
    restart: unless-stopped

  postgres:
    image: postgres:15.4-alpine
    container_name: healthai-postgres-rate-limit
    environment:
      - POSTGRES_DB=healthai
      - POSTGRES_USER=healthai
      - POSTGRES_PASSWORD=secure_password
    volumes:
      - postgres_data:/var/lib/postgresql/data
    networks:
      - healthai-network
    restart: unless-stopped
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U healthai -d healthai"]
      interval: 30s
      timeout: 10s
      retries: 5

networks:
  healthai-network:
    driver: bridge

volumes:
  redis_data:
  postgres_data:
```

## 🔧 Common Docker Commands

### Development Workflow

```bash
# Start development environment
docker compose -f docker-compose.dev.yml up -d

# View real-time logs
docker compose -f docker-compose.dev.yml logs -f healthai-api

# Restart a specific service
docker compose -f docker-compose.dev.yml restart healthai-api

# Rebuild and restart after code changes
docker compose -f docker-compose.dev.yml up -d --build healthai-api

# Execute commands in running container
docker compose -f docker-compose.dev.yml exec healthai-api bash
docker compose -f docker-compose.dev.yml exec postgres psql -U healthai -d healthai_dev

# Stop all services
docker compose -f docker-compose.dev.yml down

# Stop and remove volumes (clean slate)
docker compose -f docker-compose.dev.yml down -v
```

### Production Operations

```bash
# Deploy production stack
docker compose -f docker-compose.prod.yml up -d

# Scale application instances
docker compose -f docker-compose.prod.yml up -d --scale healthai-app=3

# Rolling update
docker compose -f docker-compose.prod.yml build healthai-app
docker compose -f docker-compose.prod.yml up -d --no-deps healthai-app

# View application logs
docker compose -f docker-compose.prod.yml logs -f --tail=100

# Check container health
docker compose -f docker-compose.prod.yml ps

# Backup database
docker compose -f docker-compose.prod.yml exec postgres pg_dump -U healthai healthai > backup.sql

# Monitor resource usage
docker stats
```

### Image Management

```bash
# Build specific image
docker build -t healthai-app:latest -f Dockerfile.optimized .

# Build with build args
docker build --build-arg ENVIRONMENT=production -t healthai-app:prod .

# Tag and push to registry
docker tag healthai-app:latest your-registry.com/healthai-app:latest
docker push your-registry.com/healthai-app:latest

# Clean up unused images
docker image prune -f

# Remove all stopped containers
docker container prune -f

# Clean up everything (use with caution)
docker system prune -af
```

## 🔍 Monitoring and Debugging

### Health Checks

Check container health:

```bash
# View health check status
docker compose -f docker-compose.prod.yml ps

# Inspect health check details
docker inspect healthai-app-1 --format='{{.State.Health}}'

# Manual health check
docker compose -f docker-compose.prod.yml exec healthai-app-1 curl -f http://localhost:8000/health
```

### Log Management

```bash
# View logs from all services
docker compose -f docker-compose.prod.yml logs

# Follow logs from specific service
docker compose -f docker-compose.prod.yml logs -f healthai-app-1

# View logs with timestamps
docker compose -f docker-compose.prod.yml logs -t

# Export logs to file
docker compose -f docker-compose.prod.yml logs > application.log

# Configure log rotation (add to compose file)
logging:
  driver: "json-file"
  options:
    max-size: "10m"
    max-file: "3"
```

### Performance Monitoring

```bash
# Monitor resource usage
docker stats

# Get detailed container info
docker compose -f docker-compose.prod.yml top

# Monitor network traffic
docker network ls
docker network inspect clinchat-style-rag-app_healthai-network
```

## 🔐 Security Best Practices

### Container Security

1. **Use Non-Root Users**:
```dockerfile
RUN useradd --create-home --shell /bin/bash --uid 1000 app
USER app
```

2. **Minimize Attack Surface**:
```dockerfile
# Use slim base images
FROM python:3.12.1-slim

# Remove package caches
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl && rm -rf /var/lib/apt/lists/*
```

3. **Secrets Management**:
```yaml
# Use Docker secrets
secrets:
  db_password:
    file: ./secrets/db_password.txt

services:
  app:
    secrets:
      - db_password
```

4. **Network Security**:
```yaml
networks:
  healthai-network:
    driver: bridge
    internal: true  # Prevent external access
```

### Environment Security

```bash
# Scan images for vulnerabilities
docker scout cves healthai-app:latest

# Use security scanning tools
docker run --rm -v /var/run/docker.sock:/var/run/docker.sock \
  aquasec/trivy image healthai-app:latest
```

## 🚨 Troubleshooting

### Common Issues

#### 1. Port Conflicts
```bash
# Error: Port already in use
# Solution: Change port mapping or stop conflicting service
docker compose -f docker-compose.dev.yml down
netstat -tlnp | grep :8000
```

#### 2. Build Failures
```bash
# Error: Package installation fails
# Solution: Clear Docker cache and rebuild
docker builder prune -f
docker compose -f docker-compose.dev.yml build --no-cache
```

#### 3. Database Connection Issues
```bash
# Check database connectivity
docker compose -f docker-compose.dev.yml exec healthai-api \
  python -c "import psycopg2; print('Database connection OK')"

# Reset database
docker compose -f docker-compose.dev.yml down -v
docker compose -f docker-compose.dev.yml up -d postgres
```

#### 4. Memory Issues
```bash
# Increase Docker Desktop memory allocation
# Or add memory limits to services
deploy:
  resources:
    limits:
      memory: 1G
```

#### 5. Volume Permission Issues
```bash
# Fix volume permissions
sudo chown -R $USER:$USER ./data
sudo chown -R $USER:$USER ./logs
```

### Debug Mode

Enable debug mode for troubleshooting:

```yaml
# Add to service in docker-compose.dev.yml
environment:
  - DEBUG=true
  - LOG_LEVEL=DEBUG
command: ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload", "--log-level", "debug"]
```

### Performance Issues

```bash
# Monitor container resource usage
docker stats --format "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.NetIO}}\t{{.BlockIO}}"

# Check for memory leaks
docker compose -f docker-compose.prod.yml exec healthai-app-1 \
  python -c "import psutil; print(f'Memory: {psutil.virtual_memory().percent}%')"
```

## 📊 Production Deployment Checklist

Before deploying to production:

- [ ] All secrets are properly managed (not in .env files)
- [ ] SSL certificates are configured
- [ ] Database backups are automated
- [ ] Health checks are working
- [ ] Resource limits are set
- [ ] Logging is configured and centralized
- [ ] Monitoring is set up (Prometheus/Grafana)
- [ ] Security scanning is performed
- [ ] Load testing is completed
- [ ] Rollback procedures are tested

## 📚 Additional Resources

- [Docker Documentation](https://docs.docker.com/)
- [Docker Compose Documentation](https://docs.docker.com/compose/)
- [Docker Security Best Practices](https://docs.docker.com/engine/security/)
- [Docker Multi-stage Builds](https://docs.docker.com/build/building/multi-stage/)
- [Docker Networking](https://docs.docker.com/network/)

---

**Next Steps**: Once Docker setup is complete, proceed with the [AWS Setup Guide](./AWS_SETUP_GUIDE.md) for cloud deployment or [GitHub Actions Setup](./GITHUB_ACTIONS_SETUP.md) for CI/CD automation.