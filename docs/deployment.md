# Deployment Guide

## Local

```bash
cp .env.example .env
docker compose up --build
```

## Kubernetes

The `infra/k8s` directory contains starter deployments for the API, worker, web app, Redis, and Nginx ingress. In production, use managed PostgreSQL, managed Redis, and managed object storage instead of in-cluster stateful services.

## Cloud

- **AWS:** ECS or EKS, RDS PostgreSQL with pgvector, ElastiCache Redis, S3, KMS, SES, CloudWatch, OpenTelemetry collector.
- **Azure:** AKS, Azure Database for PostgreSQL, Azure Cache for Redis, Blob Storage, Key Vault, Monitor.
- **GCP:** GKE, Cloud SQL PostgreSQL, Memorystore, Cloud Storage, Secret Manager, Cloud Monitoring.

## CI/CD

GitHub Actions runs API tests, web type checks, and web builds. Add environment-specific deploy jobs once cloud accounts and secrets are configured.

