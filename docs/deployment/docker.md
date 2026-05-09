# Docker Deployment Guide
# Smart Tourism Data Platform

## Giới thiệu

Hướng dẫn này mô tả cách deploy Smart Tourism Data Platform sử dụng Docker và Docker Compose.

## Yêu cầu hệ thống

- Docker Engine 24.0+
- Docker Compose 2.20+
- 4GB RAM minimum (8GB recommended)
- 10GB disk space

## Quick Start

```bash
# 1. Clone repository
git clone https://github.com/your-org/smart-tourism-platform.git
cd smart-tourism-platform

# 2. Copy environment file
cp .env.example .env

# 3. Edit .env với your configuration
nano .env

# 4. Start services
docker-compose up -d

# 5. Verify
curl http://localhost:8000/health
```

## Services

| Service | Port | Description |
|---------|------|-------------|
| API | 8000 | FastAPI application |
| MongoDB | 27017 | Database |
| Redis | 6379 | Cache |
| Prometheus | 9090 | Metrics |
| Grafana | 3001 | Dashboards |

## Production Deployment

### 1. Build Image

```bash
docker build -t smart-tourism-api:latest .
```

### 2. Push to Registry

```bash
docker tag smart-tourism-api:latest registry.example.com/smart-tourism-api:1.0.0
docker push registry.example.com/smart-tourism-api:1.0.0
```

### 3. Deploy

```bash
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d
```

## Environment Variables

Xem `.env.example` để biết đầy đủ các biến môi trường.

## Monitoring

- Prometheus: http://localhost:9090
- Grafana: http://localhost:3001 (admin/admin123)

## Troubleshooting

### Service không start

```bash
# Xem logs
docker-compose logs -f api

# Kiểm tra status
docker-compose ps
```

### Database connection failed

```bash
# Kiểm tra MongoDB
docker-compose exec mongodb mongosh --eval 'db.adminCommand({ ping: 1 })'

# Kiểm tra Redis
docker-compose exec redis redis-cli ping
```
