# 🚀 Production Deployment Checklist

**Smart Travel Data Platform** - Final Production Readiness Assessment

Last Updated: `$(date)`

---

## 📋 DEPLOYMENT PREREQUISITES

### Prerequisites Checklist
- [ ] **Git Repository**: All code committed, no uncommitted changes
- [ ] **Environment**: `.env.production` configured with real secrets (NOT in git)
- [ ] **SSL Certificates**: Generated and mounted for NGINX
- [ ] **GitHub Secrets**: Configured for CD deployment
- [ ] **Database Backups**: PostgreSQL and MongoDB backed up
- [ ] **Monitoring**: Prometheus/Grafana configured
- [ ] **Domain**: Production domain configured and DNS active

---

## 🔐 SECURITY VERIFICATION

### Run Security Checklist
```bash
# Execute automated security verification
bash scripts/security_checklist.sh
```

**Expected Result**: ✅ ALL CHECKS PASSED (0 failed checks)

### Manual Security Verification

#### 1. No Hardcoded Secrets
```bash
# Search for common secret patterns
grep -r "password.{0,5}=\|secret.{0,5}=\|token.{0,5}=" \
  apps/ src/ infra/ \
  --include="*.py" \
  --include="*.yml" \
  --include="*.yaml" \
  | grep -v ".env" || echo "✅ No secrets found"
```

#### 2. HTTPS/TLS Enabled
```bash
# Verify NGINX HTTPS configuration
grep -A 2 "listen 443" infra/nginx/nginx.conf

# Verify SSL certificate paths
ls -la /etc/ssl/certs/smart_travel.* /etc/ssl/private/smart_travel.*
```

#### 3. Rate Limiting Active
```bash
# Test rate limiting (should return 429 after 60 requests/min)
for i in {1..70}; do
  curl -s -w "%{http_code}\n" http://api.example.com/api/test
done
```

#### 4. Audit Logging
```bash
# Verify audit logs are being written
docker exec smart-travel-backend tail -f /var/log/audit.log
```

---

## 🐳 DOCKER DEPLOYMENT

### 1. Generate SSL Certificates
```bash
# Generate self-signed certificate (development)
# For production, use Let's Encrypt or your CA

mkdir -p /etc/ssl/private /etc/ssl/certs

openssl req -x509 \
  -nodes \
  -days 365 \
  -newkey rsa:2048 \
  -keyout /etc/ssl/private/smart_travel.key \
  -out /etc/ssl/certs/smart_travel.crt \
  -subj "/C=VN/ST=Hanoi/L=Hanoi/O=SmartTravel/CN=api.example.com"

# Verify certificate
openssl x509 -in /etc/ssl/certs/smart_travel.crt -text -noout
```

### 2. Build Docker Images
```bash
# Production build with all services
docker-compose -f docker-compose.yml -f docker-compose.prod.yml build

# Verify images created
docker images | grep smart-travel-
```

### 3. Verify Configuration
```bash
# Validate docker-compose syntax
docker-compose config > /dev/null && echo "✅ Config valid"

# Check service health checks defined
docker-compose config | grep -A 3 "healthcheck"
```

### 4. Deploy Services
```bash
# Production deployment
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d

# Wait for services to be healthy
sleep 30

# Verify all services running
docker-compose ps

# Expected output (all should be "healthy" or "Up")
# backend        "running"
# frontend       "running"
# nginx          "healthy"
# mysql          "healthy"
# postgres       "healthy"
# redis          "healthy"
# mongodb        "healthy"
```

### 5. Post-Deployment Verification
```bash
# Check service logs for errors
for service in backend frontend nginx postgres redis mongodb; do
  echo "=== Logs: $service ==="
  docker-compose logs $service --tail 20
done

# Verify all services responding
curl -s http://localhost:80/ | head -20              # Frontend
curl -s http://localhost:8000/api/health             # Backend health
curl -s http://localhost:8000/api/admin/health       # Admin health
```

---

## 🔍 API VALIDATION

### Health Checks
```bash
# Backend health check
curl -v http://api.example.com/api/health
# Expected: { "status": "ok" }

# Admin diagnostic health
curl -v http://api.example.com/api/admin/health
# Expected: {
#   "status": "ok",
#   "mongodb": "connected",
#   "postgres": "connected",
#   "redis": "connected",
#   "timestamp": "2024-..."
# }
```

### Authentication Test
```bash
# Create test account
curl -X POST http://api.example.com/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "SecurePassword123!",
    "name": "Test User"
  }'

# Login and get token
TOKEN=$(curl -X POST http://api.example.com/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "SecurePassword123!"
  }' | jq -r '.access_token')

# Test protected endpoint
curl -H "Authorization: Bearer $TOKEN" \
  http://api.example.com/api/me
```

### Rate Limiting Test
```bash
# Send 65 requests quickly (limit is 60/min)
for i in {1..65}; do
  curl -s -w "Request $i: %{http_code}\n" http://api.example.com/api/test
done

# Last few should return 429 (Too Many Requests)
```

### Data Endpoints Test
```bash
# Get Smart Travel Places
curl -s http://api.example.com/api/places | jq '.length'

# Get city analytics
curl -s http://api.example.com/api/analytics/city-ranking | jq '.top_cities'

# Get category matrix
curl -s http://api.example.com/api/analytics/category-matrix | jq '.shape'
```

---

## 📊 MONITORING & LOGGING

### Prometheus Metrics
```bash
# Access metrics endpoint
curl -s http://api.example.com:9090/metrics | head -30

# Key metrics to verify:
# - http_requests_total (total requests)
# - http_request_duration_seconds (latency)
# - mongodb_connection_pool_size (DB connections)
```

### Grafana Dashboards
```bash
# Access Grafana
# http://api.example.com:3000
# 
# Default credentials: admin / admin (CHANGE IMMEDIATELY)
# 
# Dashboards to verify:
# - System Overview (CPU, Memory, Disk)
# - API Performance (Response times, error rates)
# - Database Metrics (Connection pool, query times)
# - Business Metrics (Places, searches, analytics)
```

### Log Aggregation (Loki)
```bash
# Access Loki logs
# Query: {job="docker"} | json
# 
# Filter specific service:
# {job="docker",container_name="smart-travel-backend"}
```

---

## 🔄 CI/CD VERIFICATION

### GitHub Actions Status
```bash
# Check CI/CD workflow status
# 1. Go to: https://github.com/YOUR_ORG/smart-travel/actions
# 
# Expected workflows:
# ✅ CI (Python lint, test, security scan, docker build)
# ✅ CD (Deploy to staging, production, create release)
# ✅ Security (Weekly security scanning + on-push)
```

### Manual Test Run
```bash
# Trigger CI workflow manually
# 1. Go to Actions → CI → Run workflow → Branch: main
# 
# Expected jobs to pass:
# - python-lint (Black, isort, flake8, mypy)
# - python-test (pytest with coverage)
# - security-scan (bandit, safety)
# - docker-build (3 images built)
# - frontend-lint (ESLint)
# - deps-check (Trivy scan)
# - ci-success (final check)
```

### Staging Deployment Test (if available)
```bash
# Merge develop → staging should auto-deploy
# 1. Create PR to develop
# 2. Merge to develop
# 3. Watch GitHub Actions for deployment
# 4. Test on staging endpoint
curl -v https://staging-api.example.com/api/health
```

---

## 📁 DATABASE INITIALIZATION

### PostgreSQL Setup
```bash
# Connect to PostgreSQL
docker exec -it smart-travel-postgres psql -U airflow

# Verify Airflow tables created
\dt

# Expected tables:
# - airflow_db.dag
# - airflow_db.task_instance
# - airflow_db.log
```

### MongoDB Setup
```bash
# Connect to MongoDB
docker exec -it smart-travel-mongodb mongosh

# Switch to application database
use dataplatform_db

# Verify collections created
show collections

# Expected collections:
# - api_connections
# - api_schedules
# - api_runs
# - parameter_modes
# - smart_travel_places (with 4,972+ documents)
```

### Redis Setup
```bash
# Connect to Redis
docker exec -it smart-travel-redis redis-cli

# Verify Redis responding
ping

# Check memory usage
info memory

# Expected keys:
# - rate_limit:* (rate limiting)
# - session:* (session cache)
# - cache:* (application cache)
```

---

## 🛠️ TROUBLESHOOTING

### Service Won't Start
```bash
# Check service logs
docker-compose logs backend -f

# Common issues and solutions:
# 1. Port already in use: Change port in docker-compose.yml
# 2. Env vars missing: Verify .env file exists and is readable
# 3. Volume permissions: Check docker-compose volume mounts
```

### Database Connection Errors
```bash
# Test MongoDB connection
docker exec smart-travel-backend python3 -c "
from pymongo import MongoClient
client = MongoClient(os.getenv('MONGODB_URI'))
print('✅ MongoDB connected')
"

# Test PostgreSQL connection
docker exec smart-travel-backend python3 -c "
import psycopg2
conn = psycopg2.connect(os.getenv('POSTGRES_CONNECTION_STRING'))
print('✅ PostgreSQL connected')
"
```

### API Rate Limiting Too Strict
```bash
# Adjust rate limiting in .env
RATE_LIMIT_ENABLED=true
RATE_LIMIT_REQUESTS_PER_MINUTE=120  # Increase from 60
```

### NGINX SSL Certificate Error
```bash
# Verify certificate and key files exist
ls -la /etc/ssl/certs/smart_travel.crt
ls -la /etc/ssl/private/smart_travel.key

# Verify certificate validity
openssl x509 -in /etc/ssl/certs/smart_travel.crt -noout -dates

# Regenerate if expired
bash scripts/generate_certificates.sh
```

---

## ✅ FINAL SIGN-OFF CHECKLIST

**Production Deployment Sign-Off**

- [ ] Security checklist: ✅ PASSED (0 failed)
- [ ] Hardcoded secrets: ✅ None found
- [ ] HTTPS/TLS: ✅ Enabled and verified
- [ ] Rate limiting: ✅ Active (tested)
- [ ] Audit logging: ✅ Recording events
- [ ] Docker images: ✅ Built successfully
- [ ] All services: ✅ Running and healthy
- [ ] Health endpoints: ✅ All responding
- [ ] API authentication: ✅ JWT working
- [ ] Database connections: ✅ All verified
- [ ] Monitoring: ✅ Prometheus/Grafana active
- [ ] CI/CD pipelines: ✅ All workflows passing
- [ ] GitHub Actions: ✅ Secrets configured
- [ ] Backups: ✅ Created before deploy
- [ ] Rollback plan: ✅ Documented

**Deployment Date**: ______________

**Deployed By**: ______________

**Sign-Off**: ______________

---

## 🔄 POST-DEPLOYMENT

### Monitor During First Week
```bash
# Watch logs continuously
docker-compose logs -f backend

# Monitor system resources
docker stats

# Check error rates
curl -s http://api.example.com:9090/api/v1/query?query=http_requests_total | jq '.data.result[] | select(.value[1] > 0)'
```

### Scheduled Maintenance
- Daily: Check error rates, disk usage
- Weekly: Review security logs, verify backups
- Monthly: Update dependencies, review performance metrics

### Rollback Procedure
```bash
# If critical issues found:
docker-compose down

# Revert to previous version in git
git revert HEAD

# Rebuild and redeploy
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d

# Restore database from backup if needed
```

---

**🎉 Deployment Complete!**

For support: Contact DevOps team or create GitHub issue.
