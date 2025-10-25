# Makefile for ClinChat HealthAI Docker Management
.PHONY: help build build-optimized build-fast dev prod dev-up dev-down prod-up prod-down clean logs test

# Default target
help: ## Show this help message
	@echo "ClinChat HealthAI Docker Management"
	@echo "=================================="
	@echo "Available commands:"
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "  %-20s %s\n", $$1, $$2}' $(MAKEFILE_LIST)

# Build targets
build: ## Build main Docker image
	docker build -t healthai:latest .

build-optimized: ## Build optimized Docker image
	docker build -f Dockerfile.optimized -t healthai:optimized .

build-fast: ## Build fast multi-stage Docker image
	docker build -f Dockerfile.fast -t healthai:fast .

build-frontend: ## Build frontend Docker image
	docker build -f frontend/Dockerfile -t healthai-frontend:latest ./frontend

build-all: build build-optimized build-fast build-frontend ## Build all Docker images

# Development environment
dev-up: ## Start development environment
	docker-compose -f docker-compose.dev.yml up -d

dev-down: ## Stop development environment
	docker-compose -f docker-compose.dev.yml down

dev-logs: ## Show development logs
	docker-compose -f docker-compose.dev.yml logs -f

dev-restart: dev-down dev-up ## Restart development environment

# Production environment
prod-up: ## Start production environment
	docker-compose -f docker-compose.prod.yml up -d

prod-down: ## Stop production environment
	docker-compose -f docker-compose.prod.yml down

prod-logs: ## Show production logs
	docker-compose -f docker-compose.prod.yml logs -f

prod-restart: prod-down prod-up ## Restart production environment

# Rate limiting environment
rate-up: ## Start rate-limiting environment
	docker-compose -f docker-compose.rate-limiting.yml up -d

rate-down: ## Stop rate-limiting environment
	docker-compose -f docker-compose.rate-limiting.yml down

rate-logs: ## Show rate-limiting logs
	docker-compose -f docker-compose.rate-limiting.yml logs -f

# Utility commands
clean: ## Clean up Docker images and containers
	docker system prune -af
	docker volume prune -f

clean-all: ## Clean everything including volumes
	docker system prune -af --volumes

logs: ## Show logs for default compose
	docker-compose logs -f

ps: ## Show running containers
	docker ps

images: ## Show Docker images
	docker images | grep healthai

# Testing and quality
test: ## Run tests in Docker container
	docker-compose -f docker-compose.dev.yml exec healthai-app pytest tests/ -v

test-frontend: ## Run frontend tests
	docker-compose -f docker-compose.dev.yml exec frontend npm test

lint: ## Run linting
	docker-compose -f docker-compose.dev.yml exec healthai-app flake8 src/
	docker-compose -f docker-compose.dev.yml exec frontend npm run lint

# Security scanning
security-scan: ## Run security scan on images
	docker run --rm -v /var/run/docker.sock:/var/run/docker.sock \
		aquasec/trivy:latest image healthai:latest

# Health checks
health: ## Check health of all services
	@echo "Checking service health..."
	@docker-compose -f docker-compose.prod.yml ps

# Database operations (if using PostgreSQL)
db-migrate: ## Run database migrations
	docker-compose -f docker-compose.dev.yml exec healthai-app alembic upgrade head

db-shell: ## Open database shell
	docker-compose -f docker-compose.dev.yml exec postgres psql -U healthai -d healthai_dev

# Monitoring
monitor: ## Open monitoring dashboards
	@echo "Prometheus: http://localhost:9090"
	@echo "Application: http://localhost:8000/docs"

# Backup and restore
backup: ## Backup volumes
	docker run --rm -v healthai_redis_data:/data -v $(PWD)/backups:/backup alpine tar czf /backup/redis-$(shell date +%Y%m%d-%H%M%S).tar.gz -C /data .

restore-latest: ## Restore latest backup
	@latest=$$(ls -t backups/redis-*.tar.gz | head -1); \
	docker run --rm -v healthai_redis_data:/data -v $(PWD)/backups:/backup alpine tar xzf /backup/$$latest -C /data

# Development shortcuts
shell: ## Open shell in main container
	docker-compose -f docker-compose.dev.yml exec healthai-app /bin/bash

frontend-shell: ## Open shell in frontend container
	docker-compose -f docker-compose.dev.yml exec frontend /bin/sh

redis-cli: ## Open Redis CLI
	docker-compose -f docker-compose.dev.yml exec redis redis-cli

# Update containers
update: ## Pull latest images and rebuild
	docker-compose -f docker-compose.prod.yml pull
	$(MAKE) build-all
	$(MAKE) prod-restart