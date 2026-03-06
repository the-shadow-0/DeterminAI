# !DeterminAI

![Python](https://img.shields.io/badge/python-{{PYTHON_VERSION}}-blue)
![TypeScript](https://img.shields.io/badge/typescript-{{TYPESCRIPT_VERSION}}-blue)
![License {{LICENSE}}](https://img.shields.io/badge/license-{{LICENSE}}-green)
![Build Status](https://img.shields.io/badge/build-{{BUILD_STATUS}}-brightgreen)
![Version](https://img.shields.io/badge/version-{{VERSION}}-blueviolet)

**{{PROJECT_NAME}}** is a **deterministic, transactional AI execution engine** that provides **immutable, event-sourced workflows** for AI systems.  
> Think of it as **Kubernetes for AI Execution**: deterministic, auditable, and scalable.

---

## 🔹 Features

- **Immutable Event Sourcing** – Append-only logs for full auditability.  
- **Deterministic Execution** – Replays produce identical results.  
- **Graph-Based Workflows** – Pre-execution schema validation.  
- **Memory Versioning** – Snapshot branching & rollback.  
- **Storage-Agnostic** – PostgreSQL, local, and pluggable adapters.  
- **Multi-Language SDK** – Python & TypeScript (Zod/Pydantic) bindings.  
- **Enterprise-Ready** – Multi-tenant SaaS deployment patterns, RBAC, and metrics.

---

## 📂 Project Structure

    /core       → AITransactionEngine, graph validation, atomic execution
    /memory     → SnapshotEngine, content-addressed memory, branching & rollback
    /storage    → Event log adapters (PostgreSQL, local)
    /tools      → Isolation wrappers, circuit breakers, replay mocking
    /sdk        → Python & TypeScript/Zod language bindings
    /examples   → Reference workflows
    /docs       → Architecture & deployment docs

---

## ⚡ Quick Start

### 1. Requirements
- Python {{PYTHON_VERSION}}+
- Node / TypeScript {{TYPESCRIPT_VERSION}}+ (if using the TypeScript SDK)
- PostgreSQL (optional for event logs)

### 2. Install

    pip install -r requirements.txt
    # or create a venv first:
    # python -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt

### 3. Run the example workflow

    python examples/enterprise_workflow.py

This example evaluates a mock loan payload through a **DeterminAI Execution Graph (DEG)**.

### 4. CLI (explore past runs)

    python cli.py --help

---

## 🏛️ Core Principles

1. **Event Sourcing > Mutation** — Append-only operations for auditability.  
2. **Determinism > Convenience** — Replays are bit-for-bit reproducible.  
3. **Graph Compilation** — Validate with Pydantic (Python) / Zod (TS) before execution.

---

## 🔧 Architecture Overview

    +-------------------------+
    |      DeterminAI CLI     |
    +-------------------------+
               |
               v
    +-------------------------+
    |      Core Engine        |
    |  AITransactionEngine    |
    |  begin/validate/commit  |
    +-------------------------+
               |
               v
    +-------------------------+
    |    Memory Versioning    |
    |  SnapshotEngine & refs  |
    +-------------------------+
               |
               v
    +-------------------------+
    |     Storage Layer       |
    | PostgreSQL / Local / ...|
    +-------------------------+
               |
               v
    +-------------------------+
    |       Tools Layer       |
    | Circuit Breakers, Mock  |
    +-------------------------+

- **Core Engine (`/core`)** – Semantic boundaries with atomic transactions.  
- **Memory Versioning (`/memory`)** – Constant-time snapshot lookups and branching.  
- **Storage (`/storage`)** – Event log management, pluggable backends.  
- **Tools (`/tools`)** – Deterministic safeguards and replay mocking.

---

## 🚀 Enterprise Deployment

Suitable for multi-tenant SaaS on cloud providers (AWS / GCP / Azure).

### Environment variables (example)

    export DATABASE_URL="{{DATABASE_URL}}"
    export DETERMINAI_ENCRYPTION_KEY="{{DETERMINAI_ENCRYPTION_KEY}}"
    export DETERMINAI_ADMIN_TOKEN="{{DETERMINAI_ADMIN_TOKEN}}"
    export DETERMINAI_AUDITOR_TOKEN="{{DETERMINAI_AUDITOR_TOKEN}}"
    export DETERMINAI_LLM_ADAPTER="{{DETERMINAI_LLM_ADAPTER}}"
    export OPENAI_API_KEY="{{OPENAI_API_KEY}}"

> Tip: store secrets in your cloud provider's secret manager or Kubernetes Secrets.

### Example Kubernetes Deployment (adapt to your cluster)

    apiVersion: apps/v1
    kind: Deployment
    metadata:
      name: {{PROJECT_NAME_SLUG}}-api
    spec:
      replicas: 3
      selector:
        matchLabels:
          app: {{PROJECT_NAME_SLUG}}
      template:
        metadata:
          labels:
            app: {{PROJECT_NAME_SLUG}}
        spec:
          containers:
          - name: api
            image: {{DOCKER_IMAGE}}:{{VERSION}}
            ports:
            - containerPort: 8000
            envFrom:
            - secretRef:
                name: {{K8S_SECRET_NAME}}
            command: ["uvicorn", "dashboard.app:app", "--host", "0.0.0.0", "--port", "8000"]

### Monitoring & Alerts

- Expose `/metrics` in Prometheus format.  
- Useful metrics:
  - `{{PROJECT_NAME_SLUG}}_transactions_total{status="COMMITTED"}`
  - `{{PROJECT_NAME_SLUG}}_transactions_total{status="ROLLED_BACK"}`

Set alerts when rollback rate > `{{ROLLBACK_ALERT_THRESHOLD}}` (e.g., `0.05` = 5%).

---

## 📝 Examples

| Example | Path | Description |
|--------:|------|-------------|
| Enterprise Risk Workflow | `examples/enterprise_workflow.py` | Loan evaluation using deterministic graphs |
| Replay Testing | `examples/replay_test.py` | Re-run prior traces and assert identical outputs |

---

## 📚 Documentation

- Architecture: `docs/architecture.md`  
- Deployment: `docs/deployment.md`  
- Python SDK: `sdk/python/README.md`  
- TypeScript SDK: `sdk/ts/README.md`

---

## 💡 Contributing

We welcome contributions!

1. Fork the repo  
2. Create a feature branch: `git checkout -b feat/your-feature`  
3. Run tests & linters locally  
4. Submit a PR with a descriptive title and tests where applicable

Please read `CONTRIBUTING.md` for guidelines.

---

## ⚖️ License

This project is licensed under the **{{LICENSE}}** License © {{YEAR}}.

---

## 📌 Replaceable placeholders

- `{{PROJECT_NAME}}` — project display name  
- `{{PROJECT_NAME_SLUG}}` — lower-kebab project slug (for images/metrics)  
- `{{VERSION}}` — current release version  
- `{{YEAR}}` — copyright year  
- `{{LICENSE}}` — license short name (e.g., MIT)  
- `{{PYTHON_VERSION}}`, `{{TYPESCRIPT_VERSION}}` — versions used in badges  
- `{{LOGO_URL}}` — small logo URL (40x40 or similar)  
- `{{DATABASE_URL}}`, `{{DETERMINAI_ENCRYPTION_KEY}}`, etc. — runtime secrets  
- `{{DOCKER_IMAGE}}`, `{{K8S_SECRET_NAME}}`, `{{BUILD_STATUS}}`, `{{ROLLBACK_ALERT_THRESHOLD}}` — deployment settings

---

## ✅ Next steps (optional)
- Create a short `README_landing.md` (hero + 3 quick links) for the GitHub landing page.  
- Generate a small script to replace `{{PLACEHOLDER}}` tokens from a `.env` file or environment variables.  
- Add a PNG/SVG architecture diagram in `/docs/assets/` and reference it above the architecture section.

---
