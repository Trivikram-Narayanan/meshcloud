# Kubernetes Deployment Guide

This guide covers deploying MeshCloud to a Kubernetes cluster using both raw manifests and Helm charts.

## Prerequisites

- Kubernetes cluster (v1.19+)
- kubectl configured to access your cluster
- Helm 3 (for Helm deployment)
- Storage class configured for persistent volumes

## Quick Start with Helm

### 1. Add the MeshCloud Helm repository

```bash
helm repo add meshcloud https://charts.meshcloud.io
helm repo update
```

### 2. Install MeshCloud

```bash
# Create a namespace
kubectl create namespace meshcloud

# Install with default values
helm install meshcloud meshcloud/meshcloud -n meshcloud

# Or install from local chart
helm install meshcloud ./helm/meshcloud -n meshcloud
```

### 3. Access MeshCloud

```bash
# Get service details
kubectl get svc -n meshcloud

# Port forward for local access
kubectl port-forward -n meshcloud svc/meshcloud 8000:80
```

## Configuration

### Using Helm values

Create a `values.yaml` file to customize your deployment:

```yaml
meshcloud:
  replicaCount: 3
  image:
    tag: "v1.0.0"
  config:
    nodeUrl: "https://meshcloud.example.com"
  secrets:
    jwtSecret: "your-secure-jwt-secret"
    nodeToken: "your-secure-node-token"

ingress:
  enabled: true
  hosts:
    - host: meshcloud.example.com
      paths:
        - path: /
          pathType: Prefix

storage:
  size: 200Gi

postgresql:
  enabled: true
  auth:
    password: "your-secure-db-password"
```

Install with custom values:

```bash
helm install meshcloud ./helm/meshcloud -f values.yaml -n meshcloud
```

## Manual Deployment with kubectl

### 1. Create namespace

```bash
kubectl create namespace meshcloud
```

### 2. Apply manifests

```bash
# Apply in order
kubectl apply -f k8s/secrets.yaml -n meshcloud
kubectl apply -f k8s/headless-service.yaml -n meshcloud
kubectl apply -f k8s/statefulset.yaml -n meshcloud
kubectl apply -f k8s/service.yaml -n meshcloud
kubectl apply -f k8s/ingress.yaml -n meshcloud
```

### 3. Verify deployment

```bash
# Check pods
kubectl get pods -n meshcloud

# Check services
kubectl get svc -n meshcloud

# Check ingress
kubectl get ingress -n meshcloud
```

## Production Configuration

### Security

1. **Update secrets** with strong, unique values:
   ```bash
   # Generate secure secrets
   openssl rand -base64 32  # For JWT secret
   openssl rand -hex 16     # For node token
   ```

2. **Enable TLS** in ingress configuration

3. **Configure RBAC** for service accounts

### Storage

1. **Choose appropriate storage class** for your cloud provider
2. **Configure backup** for persistent volumes
3. **Monitor storage usage** with Prometheus metrics

### Networking

1. **Configure ingress** with proper TLS certificates
2. **Set up load balancer** for high availability
3. **Configure network policies** for security

### Monitoring

1. **Enable Prometheus metrics** in values.yaml
2. **Deploy monitoring stack** (Prometheus + Grafana)
3. **Set up alerts** for critical metrics

## Scaling

### Horizontal Scaling

```bash
# Scale deployment
kubectl scale deployment meshcloud --replicas=5 -n meshcloud

# Or with Helm
helm upgrade meshcloud ./helm/meshcloud --set meshcloud.replicaCount=5 -n meshcloud
```

### Vertical Scaling

Update resource requests/limits in values.yaml:

```yaml
meshcloud:
  resources:
    limits:
      cpu: 1000m
      memory: 1Gi
    requests:
      cpu: 500m
      memory: 512Mi
```

## Troubleshooting

### Common Issues

#### Pods not starting
```bash
# Check pod status
kubectl describe pod <pod-name> -n meshcloud

# Check logs
kubectl logs <pod-name> -n meshcloud
```

#### Storage issues
```bash
# Check PVC status
kubectl get pvc -n meshcloud

# Check storage class
kubectl get storageclass
```

#### Network issues
```bash
# Check services
kubectl get svc -n meshcloud

# Check ingress
kubectl describe ingress meshcloud-ingress -n meshcloud
```

### Health Checks

```bash
# Check application health
curl http://localhost:8000/health

# Check metrics
curl http://localhost:8000/metrics
```

## Backup and Recovery

### Database Backup

```bash
# If using PostgreSQL
kubectl exec -n meshcloud <postgres-pod> -- pg_dump -U meshcloud meshcloud > backup.sql

# If using SQLite (default)
kubectl cp meshcloud/<meshcloud-pod>:/app/db/meshcloud.db ./meshcloud-backup.db
```

### File Storage Backup

```bash
# Copy storage PVC data
kubectl cp meshcloud/<meshcloud-pod>:/app/storage ./storage-backup
```

## Upgrading

### Helm upgrades

```bash
# Update chart
helm repo update

# Upgrade release
helm upgrade meshcloud meshcloud/meshcloud -n meshcloud

# Or upgrade with new values
helm upgrade meshcloud ./helm/meshcloud -f new-values.yaml -n meshcloud
```

### Manual upgrades

```bash
# Update image tag in deployment
kubectl set image deployment/meshcloud meshcloud=meshcloud/meshcloud:v1.1.0 -n meshcloud

# Rolling restart
kubectl rollout restart deployment/meshcloud -n meshcloud
```

## Monitoring and Logging

### Prometheus Metrics

MeshCloud exposes metrics at `/metrics` endpoint. Configure Prometheus to scrape these metrics:

```yaml
scrape_configs:
  - job_name: 'meshcloud'
    static_configs:
      - targets: ['meshcloud:8000']
    metrics_path: '/metrics'
```

### Application Logs

```bash
# View logs
kubectl logs -f deployment/meshcloud -n meshcloud

# Logs with timestamps
kubectl logs --timestamps deployment/meshcloud -n meshcloud
```

### System Metrics

Enable Node Exporter for system-level metrics:

```bash
kubectl apply -f https://raw.githubusercontent.com/prometheus-community/helm-charts/main/charts/prometheus-node-exporter/values.yaml
```

## Security Best Practices

1. **Use strong secrets** for JWT and database credentials
2. **Enable TLS** for all communications
3. **Configure network policies** to restrict pod communication
4. **Regularly update** base images and dependencies
5. **Monitor security logs** for suspicious activity
6. **Implement backup encryption** for sensitive data

## Performance Tuning

### Resource Optimization

```yaml
meshcloud:
  resources:
    limits:
      cpu: 2000m
      memory: 2Gi
    requests:
      cpu: 1000m
      memory: 1Gi
```

### Database Tuning

For PostgreSQL, adjust these settings:

```yaml
postgresql:
  primary:
    extendedConfiguration: |
      max_connections = 100
      shared_buffers = 256MB
      work_mem = 4MB
```

### Caching

Enable Redis for improved performance:

```yaml
redis:
  enabled: true
```

## Support

For deployment issues:

1. Check the [troubleshooting guide](../troubleshooting.md)
2. Review [logs and monitoring](../monitoring.md)
3. Open an issue on [GitHub](https://github.com/yourusername/meshcloud/issues)

## Next Steps

After deployment:

1. **Configure DNS** for your domain
2. **Set up monitoring** and alerting
3. **Configure backups** for data protection
4. **Test the API** with client libraries
5. **Scale as needed** based on usage patterns