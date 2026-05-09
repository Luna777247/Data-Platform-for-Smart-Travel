# Configuration Directory

Thư mục này chứa các file cấu hình cho Smart Tourism Data Platform.

## Cấu trúc

```
config/
├── environments/          # Environment-specific configs
│   ├── development.yaml  # Local development
│   ├── staging.yaml      # Staging/pre-production
│   └── production.yaml   # Production
├── logging/              # Logging configurations
└── monitoring/           # Monitoring configurations
```

## Sử dụng

### 1. Environment Variable

```bash
export ENVIRONMENT=development
# hoặc
export ENVIRONMENT=production
```

### 2. Load trong code

```python
from src.core.config import settings

# Config tự động load theo environment
print(settings.environment)  # "development"
print(settings.mongodb_host)  # "localhost"
```

## Environment Variables

Tất cả sensitive data nên được set qua environment variables:

- `MONGODB_URI` / `MONGODB_PASSWORD`
- `REDIS_URL` / `REDIS_PASSWORD`
- `JWT_SECRET_KEY`
- `GOOGLE_PLACES_API_KEY`
- `SENTRY_DSN`

## Development

```bash
# Copy template
cp .env.example .env

# Edit
nano .env

# Load
source .env
```

## Production

Trong production, sử dụng Kubernetes Secrets hoặc Vault:

```bash
# Kubernetes Secret
kubectl create secret generic app-secrets \
  --from-env-file=.env.production
```
