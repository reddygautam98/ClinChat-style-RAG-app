# Load Balancing Configuration for HealthAI RAG Application

This document provides comprehensive load balancing configurations for production deployment of the HealthAI RAG application to eliminate single points of failure and ensure high availability.

## Overview

The load balancing setup includes:
- **NGINX** as the primary load balancer
- **HAProxy** as an alternative configuration
- **Docker Compose** multi-instance deployment
- **Kubernetes** horizontal pod autoscaling
- **Health check integration** for all configurations

## NGINX Load Balancer Configuration

### Primary NGINX Configuration (`nginx.conf`)

```nginx
events {
    worker_connections 1024;
}

http {
    upstream healthai_backend {
        # Health check configuration
        least_conn;
        
        # Application instances
        server healthai-app-1:8000 max_fails=3 fail_timeout=30s;
        server healthai-app-2:8000 max_fails=3 fail_timeout=30s;
        server healthai-app-3:8000 max_fails=3 fail_timeout=30s;
        
        # Backup instance (optional)
        server healthai-app-backup:8000 backup max_fails=2 fail_timeout=15s;
        
        # Health check endpoint
        keepalive 32;
    }
    
    # Rate limiting
    limit_req_zone $binary_remote_addr zone=api_limit:10m rate=10r/s;
    
    # Security headers
    add_header X-Content-Type-Options nosniff;
    add_header X-Frame-Options DENY;
    add_header X-XSS-Protection "1; mode=block";
    
    server {
        listen 80;
        server_name healthai-api.example.com;
        
        # Redirect HTTP to HTTPS
        return 301 https://$server_name$request_uri;
    }
    
    server {
        listen 443 ssl http2;
        server_name healthai-api.example.com;
        
        # SSL Configuration
        ssl_certificate /etc/nginx/ssl/healthai.crt;
        ssl_certificate_key /etc/nginx/ssl/healthai.key;
        ssl_protocols TLSv1.2 TLSv1.3;
        ssl_ciphers ECDHE-RSA-AES256-GCM-SHA512:DHE-RSA-AES256-GCM-SHA512:ECDHE-RSA-AES256-GCM-SHA384;
        ssl_prefer_server_ciphers off;
        
        # Logging
        access_log /var/log/nginx/healthai_access.log;
        error_log /var/log/nginx/healthai_error.log;
        
        # Health check endpoint (bypass load balancing)
        location /health {
            proxy_pass http://healthai_backend/healthz;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
            
            # Health check specific settings
            proxy_connect_timeout 5s;
            proxy_send_timeout 5s;
            proxy_read_timeout 5s;
        }
        
        # Main application endpoints
        location / {
            # Rate limiting
            limit_req zone=api_limit burst=20 nodelay;
            
            # Proxy to backend
            proxy_pass http://healthai_backend;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
            
            # Timeouts
            proxy_connect_timeout 30s;
            proxy_send_timeout 30s;
            proxy_read_timeout 30s;
            
            # WebSocket support (if needed)
            proxy_http_version 1.1;
            proxy_set_header Upgrade $http_upgrade;
            proxy_set_header Connection "upgrade";
            
            # Buffer settings
            proxy_buffering on;
            proxy_buffer_size 4k;
            proxy_buffers 8 4k;
        }
        
        # Monitoring endpoints
        location /monitoring {
            proxy_pass http://healthai_backend;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
            
            # Longer timeout for monitoring data
            proxy_read_timeout 60s;
        }
        
        # Backup endpoints
        location /backup {
            proxy_pass http://healthai_backend;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
            
            # Much longer timeout for backup operations
            proxy_read_timeout 300s;
            proxy_send_timeout 300s;
        }
        
        # Static files (if any)
        location /static/ {
            alias /var/www/healthai/static/;
            expires 1y;
            add_header Cache-Control "public, immutable";
        }
    }
}
```

## HAProxy Configuration (Alternative)

### HAProxy Configuration (`haproxy.cfg`)

```haproxy
global
    daemon
    chroot /var/lib/haproxy
    stats socket /run/haproxy/admin.sock mode 660 level admin
    stats timeout 30s
    user haproxy
    group haproxy
    
    # SSL Configuration
    ssl-default-bind-ciphers ECDHE+AESGCM:ECDHE+CHACHA20:RSA+AESGCM:RSA+SHA256
    ssl-default-bind-options ssl-min-ver TLSv1.2 no-tls-tickets

defaults
    mode http
    timeout connect 5s
    timeout client 30s
    timeout server 30s
    option httplog
    option dontlognull
    option http-server-close
    option forwardfor except 127.0.0.0/8
    retries 3
    
    # Health check defaults
    option httpchk GET /healthz
    http-check expect status 200

frontend healthai_frontend
    bind *:80
    bind *:443 ssl crt /etc/ssl/certs/healthai.pem
    
    # Redirect HTTP to HTTPS
    redirect scheme https code 301 if !{ ssl_fc }
    
    # Rate limiting
    stick-table type ip size 100k expire 30s store http_req_rate(10s)
    http-request track-sc0 src
    http-request deny if { sc_http_req_rate(0) gt 20 }
    
    # Security headers
    http-response set-header X-Content-Type-Options nosniff
    http-response set-header X-Frame-Options DENY
    http-response set-header X-XSS-Protection "1; mode=block"
    
    # Route to backend
    default_backend healthai_backend

backend healthai_backend
    balance leastconn
    
    # Health check configuration
    option httpchk GET /healthz
    http-check expect status 200
    
    # Server instances
    server healthai-app-1 healthai-app-1:8000 check inter 30s rise 2 fall 3 maxconn 100
    server healthai-app-2 healthai-app-2:8000 check inter 30s rise 2 fall 3 maxconn 100
    server healthai-app-3 healthai-app-3:8000 check inter 30s rise 2 fall 3 maxconn 100
    
    # Backup server
    server healthai-app-backup healthai-app-backup:8000 backup check inter 30s rise 2 fall 2 maxconn 50

# Statistics interface
listen stats
    bind *:8404
    stats enable
    stats uri /stats
    stats refresh 30s
    stats admin if TRUE
```

## Docker Compose Multi-Instance Deployment

### Production Docker Compose (`docker-compose.prod.yml`)

```yaml
version: '3.8'

services:
  # Load Balancer
  nginx:
    image: nginx:alpine
    container_name: healthai-nginx
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx/nginx.conf:/etc/nginx/nginx.conf:ro
      - ./nginx/ssl:/etc/nginx/ssl:ro
      - nginx_logs:/var/log/nginx
    depends_on:
      - healthai-app-1
      - healthai-app-2
      - healthai-app-3
    restart: always
    networks:
      - healthai-network

  # Application Instances
  healthai-app-1:
    build: .
    container_name: healthai-app-1
    environment:
      - APP_INSTANCE=1
      - PORT=8000
    volumes:
      - ./data:/app/data
      - ./backups:/app/backups
    restart: always
    networks:
      - healthai-network
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/healthz"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s

  healthai-app-2:
    build: .
    container_name: healthai-app-2
    environment:
      - APP_INSTANCE=2
      - PORT=8000
    volumes:
      - ./data:/app/data
      - ./backups:/app/backups
    restart: always
    networks:
      - healthai-network
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/healthz"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s

  healthai-app-3:
    build: .
    container_name: healthai-app-3
    environment:
      - APP_INSTANCE=3
      - PORT=8000
    volumes:
      - ./data:/app/data
      - ./backups:/app/backups
    restart: always
    networks:
      - healthai-network
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/healthz"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s

  # Backup Instance
  healthai-app-backup:
    build: .
    container_name: healthai-app-backup
    environment:
      - APP_INSTANCE=backup
      - PORT=8000
    volumes:
      - ./data:/app/data
      - ./backups:/app/backups
    restart: always
    networks:
      - healthai-network
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/healthz"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s

  # Monitoring
  prometheus:
    image: prom/prometheus
    container_name: healthai-prometheus
    ports:
      - "9090:9090"
    volumes:
      - ./monitoring/prometheus.yml:/etc/prometheus/prometheus.yml:ro
      - prometheus_data:/prometheus
    command:
      - '--config.file=/etc/prometheus/prometheus.yml'
      - '--storage.tsdb.path=/prometheus'
      - '--web.console.libraries=/etc/prometheus/console_libraries'
      - '--web.console.templates=/etc/prometheus/consoles'
    restart: always
    networks:
      - healthai-network

  grafana:
    image: grafana/grafana
    container_name: healthai-grafana
    ports:
      - "3000:3000"
    volumes:
      - grafana_data:/var/lib/grafana
      - ./monitoring/grafana/dashboards:/etc/grafana/provisioning/dashboards
      - ./monitoring/grafana/datasources:/etc/grafana/provisioning/datasources
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=admin
    restart: always
    networks:
      - healthai-network

networks:
  healthai-network:
    driver: bridge

volumes:
  nginx_logs:
  prometheus_data:
  grafana_data:
```

## Kubernetes Deployment

### Deployment Configuration (`k8s-deployment.yaml`)

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: healthai-rag-deployment
  labels:
    app: healthai-rag
spec:
  replicas: 3
  selector:
    matchLabels:
      app: healthai-rag
  template:
    metadata:
      labels:
        app: healthai-rag
    spec:
      containers:
      - name: healthai-rag
        image: healthai-rag:latest
        ports:
        - containerPort: 8000
        env:
        - name: PORT
          value: "8000"
        resources:
          requests:
            memory: "512Mi"
            cpu: "250m"
          limits:
            memory: "1Gi"
            cpu: "500m"
        livenessProbe:
          httpGet:
            path: /healthz
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 30
          timeoutSeconds: 10
          failureThreshold: 3
        readinessProbe:
          httpGet:
            path: /readyz
            port: 8000
          initialDelaySeconds: 10
          periodSeconds: 10
          timeoutSeconds: 5
          failureThreshold: 3
        volumeMounts:
        - name: data-volume
          mountPath: /app/data
        - name: backup-volume
          mountPath: /app/backups
      volumes:
      - name: data-volume
        persistentVolumeClaim:
          claimName: healthai-data-pvc
      - name: backup-volume
        persistentVolumeClaim:
          claimName: healthai-backup-pvc

---
apiVersion: v1
kind: Service
metadata:
  name: healthai-rag-service
  labels:
    app: healthai-rag
spec:
  selector:
    app: healthai-rag
  ports:
  - protocol: TCP
    port: 80
    targetPort: 8000
  type: LoadBalancer

---
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: healthai-rag-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: healthai-rag-deployment
  minReplicas: 3
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
  - type: Resource
    resource:
      name: memory
      target:
        type: Utilization
        averageUtilization: 80
  behavior:
    scaleDown:
      stabilizationWindowSeconds: 300
      policies:
      - type: Percent
        value: 50
        periodSeconds: 60
    scaleUp:
      stabilizationWindowSeconds: 60
      policies:
      - type: Percent
        value: 100
        periodSeconds: 30

---
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: healthai-data-pvc
spec:
  accessModes:
    - ReadWriteMany
  resources:
    requests:
      storage: 10Gi

---
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: healthai-backup-pvc
spec:
  accessModes:
    - ReadWriteMany
  resources:
    requests:
      storage: 50Gi
```

## Load Balancer Health Check Integration

### Custom Health Check Endpoint

The application provides comprehensive health endpoints that integrate with load balancers:

- `/healthz` - Liveness probe (basic health check)
- `/readyz` - Readiness probe (dependency checks)
- `/health/detailed` - Comprehensive health information

### Health Check Configuration Script

```bash
#!/bin/bash
# health-check-setup.sh

# Configure NGINX health checks
sudo tee /etc/nginx/conf.d/health-check.conf <<EOF
location /nginx-health {
    access_log off;
    return 200 "healthy\n";
    add_header Content-Type text/plain;
}
EOF

# Restart NGINX
sudo systemctl restart nginx

# Verify health checks
echo "Testing health endpoints..."
curl -f http://localhost/healthz || exit 1
curl -f http://localhost/readyz || exit 1
curl -f http://localhost/nginx-health || exit 1

echo "All health checks passed!"
```

## Monitoring and Alerting

### Prometheus Configuration (`prometheus.yml`)

```yaml
global:
  scrape_interval: 15s
  evaluation_interval: 15s

rule_files:
  - "alert-rules.yml"

alerting:
  alertmanagers:
    - static_configs:
        - targets:
          - alertmanager:9093

scrape_configs:
  - job_name: 'healthai-rag'
    static_configs:
      - targets: 
        - 'healthai-app-1:8000'
        - 'healthai-app-2:8000'
        - 'healthai-app-3:8000'
    metrics_path: /monitoring/export
    scrape_interval: 30s
    
  - job_name: 'nginx'
    static_configs:
      - targets: ['nginx:9113']
    
  - job_name: 'node-exporter'
    static_configs:
      - targets: ['node-exporter:9100']
```

## Deployment Scripts

### Production Deployment Script (`deploy-production.sh`)

```bash
#!/bin/bash
set -e

echo "Starting HealthAI RAG production deployment..."

# Build application image
echo "Building application image..."
docker build -t healthai-rag:latest .

# Stop existing deployment
echo "Stopping existing services..."
docker-compose -f docker-compose.prod.yml down

# Start new deployment
echo "Starting new deployment..."
docker-compose -f docker-compose.prod.yml up -d

# Wait for services to be ready
echo "Waiting for services to be ready..."
sleep 60

# Health check verification
echo "Verifying deployment health..."
for i in {1..5}; do
    if curl -f http://localhost/health; then
        echo "Deployment successful!"
        exit 0
    fi
    echo "Waiting for services... ($i/5)"
    sleep 30
done

echo "Deployment verification failed!"
exit 1
```

### Rolling Update Script (`rolling-update.sh`)

```bash
#!/bin/bash
set -e

echo "Starting rolling update..."

INSTANCES=("healthai-app-1" "healthai-app-2" "healthai-app-3")

for instance in "${INSTANCES[@]}"; do
    echo "Updating $instance..."
    
    # Stop instance
    docker-compose -f docker-compose.prod.yml stop $instance
    
    # Update image
    docker-compose -f docker-compose.prod.yml up -d $instance
    
    # Wait for health check
    for i in {1..10}; do
        if docker exec $instance curl -f http://localhost:8000/healthz; then
            echo "$instance is healthy"
            break
        fi
        if [ $i -eq 10 ]; then
            echo "Health check failed for $instance"
            exit 1
        fi
        sleep 10
    done
    
    echo "$instance updated successfully"
    sleep 10
done

echo "Rolling update completed successfully!"
```

## Security Considerations

1. **SSL/TLS Configuration**: All load balancers should terminate SSL with strong cipher suites
2. **Rate Limiting**: Implement rate limiting to prevent abuse
3. **Security Headers**: Add security headers to all responses
4. **Access Control**: Restrict access to monitoring and backup endpoints
5. **Network Segmentation**: Use private networks for backend communication

## Performance Tuning

1. **Connection Pooling**: Configure appropriate connection pool sizes
2. **Caching**: Implement response caching where appropriate
3. **Compression**: Enable gzip compression for responses
4. **Buffer Sizes**: Tune buffer sizes based on expected payload sizes
5. **Timeout Values**: Set appropriate timeout values for different endpoints

This configuration provides a robust, scalable, and highly available deployment for the HealthAI RAG application with proper load balancing, health checks, and monitoring integration.