# DeterminAI Runtime - Enterprise Deployment Guide

Welcome to the **DeterminAI Enterprise Edition** deployment handbook! This guide covers configuring DeterminAI as a multi-tenant SaaS application operating directly on secure cloud environments (AWS, GCP, Azure).

---

## 🏗️ 1. Infrastructure Overview

DeterminAI natively splits its workload into three horizontally scalable components:
1. **The Core Runtime & API:** Node generation and state routing via the `AITransactionEngine`.
2. **PostgreSQL Event Logs:** Scalable persistent memory snapshot storage bound to JSONB columns.
3. **Audit Dashboard:** FastAPI admin panel providing 100% deterministic visual traces.

## 🔐 2. Environment Secrets

To initialize the Enterprise Layer, you must set the following environment variables on your cloud instances (or via AWS Secrets Manager / Kubernetes Secrets):

```bash
# PostgreSQL Connection (Use AWS RDS or GCP Cloud SQL)
export DATABASE_URL="postgresql://determinai_admin:secure_password@my-rds-cluster.us-east-1.rds.amazonaws.com:5432/determinai"

# AES-256 Encryption (REQUIRED FOR COMPLIANCE)
# Generate via: `python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode('utf-8'))"`
export DETERMINAI_ENCRYPTION_KEY="<base64-fernet-key>"

# RBAC Dashboard Access Tokens
export DETERMINAI_ADMIN_TOKEN="super-secret-admin-pass"
export DETERMINAI_AUDITOR_TOKEN="read-only-auditor-pass"

# Production LLM Adapters
export DETERMINAI_LLM_ADAPTER="gpt5"
export OPENAI_API_KEY="sk-..."
```

## 📊 3. Monitoring & Grafana

The DeterminAI dashboard natively exposes a `/metrics` endpoint built in strict Prometheus syntax.

### Prometheus `prometheus.yml` Scrape Configuration
Attach the FastAPI metrics endpoint to Prometheus:
```yaml
scrape_configs:
  - job_name: 'determinai_runtime'
    static_configs:
      - targets: ['determinai-api.internal:8000']
    metrics_path: '/metrics'
```

### Key Metrics to Alert On
- `determinai_transactions_total{status="COMMITTED"}`: Healthy executions.
- `determinai_transactions_total{status="ROLLED_BACK"}`: Fired when guardrails fail. Alert if this spikes > 5% hourly.

## 🚀 4. Kubernetes Deployment

We recommend deploying the API layer via Docker across an EKS/GKE cluster.

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: determinai-api
spec:
  replicas: 3
  selector:
    matchLabels:
      app: determinai
  template:
    metadata:
      labels:
        app: determinai
    spec:
      containers:
      - name: api
        image: determinai/runtime:v2.1
        ports:
        - containerPort: 8000
        envFrom:
        - secretRef:
            name: determinai-production-secrets
        command: ["uvicorn", "dashboard.app:app", "--host", "0.0.0.0", "--port", "8000"]
```

## 🛡️ 5. Handling Old Semantic Versions

DeterminAI natively maintains backward-compatible Graph Versions across schema migrations. Ensure that `AITransactionEngine` initialization explicitly bounds new instances to isolated graphs like:
`graph = DeterministicExecutionGraph("LoanApproval_V2", "2.0.0")`.

The `ReplayEngine` will dynamically handle `V1` transactions seamlessly parsing the encrypted Postgres states natively, guaranteeing 100% verifiable audits!
