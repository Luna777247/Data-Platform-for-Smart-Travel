# Production Deployment Guide
# Smart Tourism Data Platform

## Checklist trước khi deploy

### Security
- [ ] Đổi tất cả default passwords
- [ ] Generate strong JWT secret (32+ chars)
- [ ] Enable HTTPS/TLS
- [ ] Configure CORS origins chính xác
- [ ] Set up rate limiting
- [ ] Enable request logging
- [ ] Configure security headers
- [ ] Set up WAF (nếu có)

### Database
- [ ] MongoDB authentication enabled
- [ ] MongoDB replica set (cho HA)
- [ ] Database backups configured
- [ ] Redis password set
- [ ] Redis persistence enabled

### Monitoring
- [ ] Prometheus scraping configured
- [ ] Grafana dashboards imported
- [ ] Alert rules configured
- [ ] Sentry/Datadog integration
- [ ] Health checks configured
- [ ] Log aggregation setup

### Infrastructure
- [ ] Load balancer configured
- [ ] SSL certificates installed
- [ ] DNS records updated
- [ ] Firewall rules configured
- [ ] Auto-scaling policies
- [ ] Resource limits set

## Deployment Steps

### 1. Environment Setup

```bash
# Production environment
export ENVIRONMENT=production
export LOG_LEVEL=WARNING
export DEBUG=false

# Secrets (không bao giờ commit!)
export JWT_SECRET_KEY=$(openssl rand -base64 32)
export MONGODB_PASSWORD=$(openssl rand -base64 16)
export REDIS_PASSWORD=$(openssl rand -base64 16)
```

### 2. Database Migration

```bash
# Backup existing data
mongodump --uri="$MONGODB_URI" --out=/backup/$(date +%Y%m%d)

# Apply migrations
python -m src.db.migrations upgrade

# Verify
python scripts/verify_db.py
```

### 3. Deploy Application

```bash
# Build production image
docker build -t smart-tourism-api:prod .

# Push to registry
docker push registry.example.com/smart-tourism-api:prod

# Deploy
kubectl apply -f k8s/production/
```

### 4. Verification

```bash
# Health check
curl -f https://api.smarttravel.vn/health

# Readiness check
curl -f https://api.smarttravel.vn/ready

# API test
curl https://api.smarttravel.vn/api/v1/data/stats \
  -H "Authorization: Bearer $TOKEN"
```

## Performance Tuning

### API Tuning

```python
# Uvicorn workers
workers = 2 * cpu_cores + 1

# Connection pooling
MONGODB_MAX_CONNECTIONS = 50
REDIS_POOL_SIZE = 20
```

### Database Tuning

```yaml
# MongoDB
wiredTigerCacheSizeGB: 2
oplogSizeMB: 1024

# Redis
maxmemory: 2gb
maxmemory-policy: allkeys-lru
```

## Backup Strategy

### Automated Backups

```bash
# Database backup (daily at 2 AM)
0 2 * * * /scripts/backup_db.sh

# File backup
0 3 * * * /scripts/backup_files.sh
```

### Backup Verification

```bash
# Weekly restore test
/scripts/test_restore.sh /backup/latest
```

## Disaster Recovery

### RPO/RTO
- **RPO** (Recovery Point Objective): 1 hour
- **RTO** (Recovery Time Objective): 4 hours

### Failover Process

1. **Detect failure**
   ```bash
   ./scripts/health_check.sh || ./scripts/failover.sh
   ```

2. **Activate standby**
   ```bash
   kubectl apply -f k8s/dr/standby-active.yaml
   ```

3. **Update DNS**
   ```bash
   aws route53 change-resource-record-sets --hosted-zone-id $ZONE_ID \
     --change-batch file://dns-update.json
   ```

## Maintenance Windows

### Scheduled Maintenance

```bash
# 1. Enable maintenance mode
kubectl apply -f k8s/maintenance/enable.yaml

# 2. Wait for connections drain
sleep 60

# 3. Apply updates
kubectl set image deployment/api api=smart-tourism-api:v1.1.0

# 4. Verify
./scripts/smoke_tests.sh

# 5. Disable maintenance
kubectl delete -f k8s/maintenance/enable.yaml
```

## Security Best Practices

### Secrets Management
- Dùng Kubernetes Secrets hoặc Vault
- Rotate secrets định kỳ (90 ngày)
- Không bao giờ log secrets

### Network Security
- Pod-to-pod encryption (mTLS)
- Network policies
- DDoS protection

### Compliance
- Audit logs (1 year retention)
- Data encryption at rest
- GDPR compliance (nếu applicable)

## Emergency Contacts

| Role | Name | Phone | Email |
|------|------|-------|-------|
| On-call Engineer | | | |
| DevOps Lead | | | |
| Database Admin | | | |
| Security Lead | | | |

## Runbooks

### High CPU Usage

1. Check metrics: `kubectl top pods`
2. Profile application: `py-spy`
3. Scale nếu cần: `kubectl scale deployment/api --replicas=10`
4. Investigate root cause

### Database Connection Issues

1. Check MongoDB: `kubectl get pods -l app=mongodb`
2. Check connections: `netstat -an | grep 27017`
3. Restart nếu cần: `kubectl rollout restart statefulset/mongodb`

### Memory Leak

1. Get heap dump: `kill -SIGUSR1 <pid>`
2. Analyze: `python -m memray analyze`
3. Deploy fix

## Post-Deployment

### Day 1 Checklist
- [ ] Monitoring dashboards working
- [ ] Alerts configured
- [ ] Logs flowing
- [ ] Backup successful
- [ ] SSL valid
- [ ] Performance baseline captured

### Week 1 Checklist
- [ ] Error rates < 0.1%
- [ ] Latency p95 < 200ms
- [ ] All alerts tested
- [ ] Documentation updated
- [ ] Team trained

## References
- Architecture: `docs/SMART_TOURISM_ARCHITECTURE.md`
- Developer Guide: `docs/SMART_TOURISM_DEVELOPER_GUIDE.md`
- Runbooks: `docs/runbooks/`
