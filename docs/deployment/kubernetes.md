# Kubernetes Deployment Guide
# Smart Tourism Data Platform

## Giới thiệu

Hướng dẫn deploy Smart Tourism Data Platform lên Kubernetes cluster.

## Prerequisites

- Kubernetes cluster (1.24+)
- kubectl configured
- Helm 3.x (optional)
- Ingress controller (nginx/traefik)
- Cert-manager (cho TLS)
- Metrics server

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                      Ingress                            │
│              (SSL termination, routing)                 │
└─────────────────────────────────────────────────────────┘
                          │
    ┌─────────────────────┼─────────────────────┐
    │                     │                     │
┌───▼────┐           ┌────▼────┐           ┌────▼────┐
│  API   │           │  API    │           │  API    │
│ Pod 1  │           │ Pod 2   │           │ Pod N   │
└────┬───┘           └────┬────┘           └────┬────┘
     │                    │                     │
     └────────────────────┼─────────────────────┘
                          │
              ┌───────────▼───────────┐
              │     Services          │
              ├───────────┬───────────┤
              │           │           │
         ┌────▼───┐  ┌───▼────┐  ┌───▼────┐
         │ MongoDB│  │ Redis  │  │Prometheus
         │Stateful│  │        │  │        │
         └────────┘  └────────┘  └────────┘
```

## Quick Start

### 1. Namespace

```bash
kubectl create namespace smart-tourism
kubectl config set-context --current --namespace=smart-tourism
```

### 2. Secrets

```bash
# Tạo secrets
kubectl create secret generic api-secrets \
  --from-literal=jwt-secret=your-jwt-secret \
  --from-literal=mongodb-password=your-mongodb-password \
  --from-literal=redis-password=your-redis-password

# Hoặc dùng file
kubectl apply -f k8s/secrets.yaml
```

### 3. ConfigMaps

```bash
kubectl apply -f k8s/configmap.yaml
```

### 4. Databases

```bash
# MongoDB
kubectl apply -f k8s/mongodb-statefulset.yaml
kubectl apply -f k8s/mongodb-service.yaml

# Redis
kubectl apply -f k8s/redis-deployment.yaml
kubectl apply -f k8s/redis-service.yaml
```

### 5. API Deployment

```bash
kubectl apply -f k8s/api-deployment.yaml
kubectl apply -f k8s/api-service.yaml
kubectl apply -f k8s/api-hpa.yaml
```

### 6. Ingress

```bash
kubectl apply -f k8s/ingress.yaml
```

## Resource Requirements

### API Pods
```yaml
resources:
  requests:
    memory: "256Mi"
    cpu: "250m"
  limits:
    memory: "512Mi"
    cpu: "500m"
```

### MongoDB
```yaml
resources:
  requests:
    memory: "512Mi"
    cpu: "250m"
  limits:
    memory: "1Gi"
    cpu: "500m"
  storage: "10Gi"
```

### Redis
```yaml
resources:
  requests:
    memory: "128Mi"
    cpu: "100m"
  limits:
    memory: "256Mi"
    cpu: "250m"
```

## Scaling

### Horizontal Pod Autoscaler

```yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: api-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: api
  minReplicas: 2
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
```

## Monitoring

### Prometheus ServiceMonitor

```yaml
apiVersion: monitoring.coreos.com/v1
kind: ServiceMonitor
metadata:
  name: api-metrics
spec:
  selector:
    matchLabels:
      app: api
  endpoints:
  - port: metrics
    interval: 30s
```

## Troubleshooting

### Pod không start

```bash
# Xem logs
kubectl logs -f deployment/api

# Describe pod
kubectl describe pod -l app=api

# Events
kubectl get events --sort-by='.lastTimestamp'
```

### Database connection failed

```bash
# Test connection từ pod
kubectl exec -it deployment/api -- python -c "
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
client = AsyncIOMotorClient('mongodb://mongodb:27017')
asyncio.run(client.admin.command('ping'))
print('Connected!')
"
```

## Cleanup

```bash
kubectl delete namespace smart-tourism
```
