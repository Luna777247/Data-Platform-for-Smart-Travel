#!/bin/bash
# deploy.sh - Deployment Script
# =============================
# Script deploy Smart Tourism Data Platform
#
# Usage: ./scripts/deploy.sh [environment]
#   environment: development | staging | production (default: development)

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Configuration
ENVIRONMENT=${1:-development}
COMPOSE_FILE="docker-compose.yml"

# Print functions
print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_step() {
    echo -e "${BLUE}[STEP]${NC} $1"
}

# Header
echo "🚀 Smart Tourism Data Platform - Deployment Script"
echo "=================================================="
echo "Environment: $ENVIRONMENT"
echo ""

# Validate environment
if [[ ! "$ENVIRONMENT" =~ ^(development|staging|production)$ ]]; then
    print_error "Invalid environment. Must be: development, staging, or production"
    exit 1
fi

# Step 1: Pre-deployment checks
print_step "1. Running pre-deployment checks..."

# Check Docker
if ! command -v docker &> /dev/null; then
    print_error "Docker is not installed"
    exit 1
fi
print_status "✓ Docker found"

# Check Docker Compose
if ! command -v docker-compose &> /dev/null; then
    print_error "Docker Compose is not installed"
    exit 1
fi
print_status "✓ Docker Compose found"

# Check .env file
if [ ! -f ".env" ]; then
    print_error ".env file not found. Run setup.sh first or create .env file"
    exit 1
fi
print_status "✓ .env file found"

# Step 2: Environment-specific configuration
print_step "2. Configuring for $ENVIRONMENT environment..."

case $ENVIRONMENT in
    development)
        export COMPOSE_FILE="docker-compose.yml"
        print_status "✓ Using development configuration"
        ;;
    staging)
        export COMPOSE_FILE="docker-compose.yml:docker-compose.staging.yml"
        print_status "✓ Using staging configuration"
        ;;
    production)
        export COMPOSE_FILE="docker-compose.yml:docker-compose.prod.yml"
        print_status "✓ Using production configuration"
        ;;
esac

# Step 3: Build images
print_step "3. Building Docker images..."
docker-compose build --no-cache
print_status "✓ Docker images built"

# Step 4: Database migrations (if any)
print_step "4. Running database setup..."
docker-compose up -d mongodb redis
sleep 5  # Wait for databases to be ready
print_status "✓ Database containers started"

# Step 5: Start services
print_step "5. Starting services..."
docker-compose up -d
print_status "✓ All services started"

# Step 6: Health checks
print_step "6. Running health checks..."
sleep 10  # Wait for services to be ready

# Check API health
if curl -f http://localhost:8000/health &> /dev/null; then
    print_status "✓ API is healthy"
else
    print_warning "API health check failed. Check logs with: docker-compose logs api"
fi

# Check MongoDB
if docker-compose exec -T mongodb mongosh --eval "db.adminCommand('ping')" &> /dev/null; then
    print_status "✓ MongoDB is healthy"
else
    print_warning "MongoDB health check failed"
fi

# Check Redis
if docker-compose exec -T redis redis-cli ping | grep -q "PONG"; then
    print_status "✓ Redis is healthy"
else
    print_warning "Redis health check failed"
fi

# Step 7: Post-deployment summary
print_step "7. Deployment Summary"
echo "=================================================="
echo "✅ Deployment completed successfully!"
echo "=================================================="
echo ""
echo "Services:"
docker-compose ps
echo ""
echo "Access points:"
echo "  API:        http://localhost:8000"
echo "  API Docs:   http://localhost:8000/docs"
echo "  Prometheus: http://localhost:9090"
echo "  Grafana:    http://localhost:3001"
echo "  MongoDB:    localhost:27017"
echo "  Redis:      localhost:6379"
echo ""
echo "Useful commands:"
echo "  docker-compose logs -f api    # View API logs"
echo "  docker-compose logs -f mongodb  # View MongoDB logs"
echo "  docker-compose down           # Stop all services"
echo "  docker-compose ps             # List running services"
echo ""
