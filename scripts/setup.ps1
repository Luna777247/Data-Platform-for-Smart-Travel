# Smart Travel Platform Setup Script for Windows (PowerShell)

Write-Host "🚀 Setting up Smart Travel Data Platform..." -ForegroundColor Cyan

# Check prerequisites
if (!(Get-Command docker -ErrorAction SilentlyContinue)) {
    Write-Error "❌ Docker is required but not installed. Aborting."
    exit 1
}

# Create necessary directories
Write-Host "📁 Creating directories..." -ForegroundColor Yellow
New-Item -ItemType Directory -Force -Path "logs", "data/mongodb", "data/postgres", "data/redis" | Out-Null

# Copy environment files if they don't exist
if (!(Test-Path .env)) {
    Write-Host "📋 Creating .env file..." -ForegroundColor Yellow
    $secretKey = [Convert]::ToBase64String((1..32 | ForEach-Object { [byte](Get-Random -Minimum 0 -Maximum 255) }))
    
    $envContent = @"
# Database
MONGODB_URI=mongodb://admin:secret_password@localhost:27017
DB_NAME=smart_travel
POSTGRES_URL=postgresql+asyncpg://admin:secret_password@localhost:5432/smart_travel
REDIS_URL=redis://localhost:6379

# API Keys
GOOGLE_PLACES_API_KEY=your-api-key-here

# Security
SECRET_KEY=$secretKey
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Airflow
AIRFLOW_FERNET_KEY=your-airflow-fernet-key-here
AIRFLOW_WEBSERVER_SECRET=your-airflow-webserver-secret-here

# External Services
NEXT_PUBLIC_API_URL=http://localhost:8000/api
"@
    Set-Content -Path .env -Value $envContent
    Write-Warning "⚠️ Please update .env file with your actual API keys!"
}

# Build and start services
Write-Host "🐳 Building and starting services..." -ForegroundColor Yellow
docker-compose -f infra/docker/docker-compose.yml up --build -d

# Wait for services to be healthy
Write-Host "⏳ Waiting for services to start (30s)..." -ForegroundColor Yellow
Start-Sleep -Seconds 30

# Run database migrations
Write-Host "🗄️ Running database migrations..." -ForegroundColor Yellow
& ./scripts/migrate.ps1

Write-Host "`n🎉 Setup completed successfully!" -ForegroundColor Green
Write-Host "📊 Frontend: http://localhost:3000"
Write-Host "🔌 API: http://localhost:8000"
Write-Host "🎯 API Docs: http://localhost:8000/docs"
Write-Host "🛩️ Airflow: http://localhost:8080"
