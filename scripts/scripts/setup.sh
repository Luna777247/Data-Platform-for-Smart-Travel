#!/bin/bash

# Smart Travel Platform Setup Script

set -e

echo "🚀 Setting up Smart Travel Data Platform..."

# Check prerequisites
command -v docker >/dev/null 2>&1 || { echo "❌ Docker is required but not installed. Aborting."; exit 1; }
command -v docker-compose >/dev/null 2>&1 || { echo "❌ Docker Compose is required but not installed. Aborting."; exit 1; }

# Create necessary directories
echo "📁 Creating directories..."
mkdir -p logs
mkdir -p data/mongodb
mkdir -p data/postgres
mkdir -p data/redis

# Copy environment files if they don't exist
if [ ! -f .env ]; then
    echo "📋 Creating .env file..."
    AIRFLOW_WEBSERVER_SECRET=$(python3 -c "import secrets; print(secrets.token_urlsafe(32))" 2>/dev/null || python3 -c "import uuid; print(uuid.uuid4().hex + uuid.uuid4().hex)")

    cat > .env << EOF
# Database
MONGODB_URI=mongodb://admin:${MONGODB_PASSWORD:-your_secure_mongodb_password_here}@localhost:27017
DB_NAME=smart_travel
POSTGRES_URL=postgresql+asyncpg://admin:${POSTGRES_PASSWORD:-your_secure_postgres_password_here}@localhost:5432/smart_travel
REDIS_URL=redis://localhost:6379

# API Keys
GOOGLE_PLACES_API_KEY=your-api-key-here

# Airflow
AIRFLOW_FERNET_KEY=$(python3 -c "from cryptography.fernet import Fernet; print(Fernet.generate().decode())" 2>/dev/null || echo "your-fernet-key-here")
AIRFLOW_WEBSERVER_SECRET=$AIRFLOW_WEBSERVER_SECRET

# Security
JWT_SECRET=$(python3 -c "import secrets; print(secrets.token_urlsafe(32))" 2>/dev/null || echo "your-jwt-secret-here")
EOF
    echo "⚠️  Please update .env file with your actual API keys!"
fi

# Build and start services
echo "🐳 Building and starting services..."
docker-compose -f infra/docker/docker-compose.yml up --build -d

# Wait for services to be healthy
echo "⏳ Waiting for services to start..."
sleep 30

# Run database migrations
echo "🗄️ Running database migrations..."
./scripts/migrate.sh

echo "🎉 Setup completed successfully!"
echo ""
echo "Access your services:"
echo "📊 Frontend: http://localhost:3000"
echo "🔌 API: http://localhost:8000"
echo "🎯 API Docs: http://localhost:8000/docs"
echo "🛩️ Airflow: http://localhost:8080"
echo ""
echo "To view logs: docker-compose -f infra/docker/docker-compose.yml logs -f"
echo "To stop: docker-compose -f infra/docker/docker-compose.yml down"
