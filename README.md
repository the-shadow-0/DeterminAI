<div align="center">  
# 🚀 DeterminAI ✨ 
</div>

![Python](https://img.shields.io/badge/python-3.12-blue)
![TypeScript](https://img.shields.io/badge/typescript-5.0-blue)
![License MIT](https://img.shields.io/badge/license-MIT-green)
![Build Status](https://img.shields.io/badge/build-passing-brightgreen)
![Version](https://img.shields.io/badge/version-0.1.0-blueviolet)

**DeterminAI** is a **deterministic, transactional AI execution engine** that provides **immutable, event-sourced workflows** for AI systems. 🤖🧠
> 💡 Think of it as **Kubernetes for AI Execution**: deterministic, auditable, and scalable. 📈

---

## 🛠️ Tech Stack

Built with modern, enterprise-ready technologies to ensure robust execution and type safety:

- **Core Engine:** 🐍 Python 3.12, ⚡ FastAPI, 🧩 Pydantic
- **SDKs:** 🐍 Python, 📘 TypeScript 5.0 (with Zod validation)
- **Data & Event Storage:** 🐘 PostgreSQL (Event Log & Snapshots)
- **Deployment:** 🐳 Docker, ☸️ Kubernetes, 🦄 Uvicorn

---

## ✨ Features

- 🔒 **Immutable Event Sourcing** – Append-only logs for full auditability.  
- 🎯 **Deterministic Execution** – Replays produce identical results.  
- 🕸️ **Graph-Based Workflows** – Pre-execution schema validation.  
- 💾 **Memory Versioning** – Snapshot branching & rollback.  
- 🗄️ **Storage-Agnostic** – PostgreSQL, local, and pluggable adapters.  
- 🌍 **Multi-Language SDK** – Python & TypeScript (Zod/Pydantic) bindings.  
- 🏢 **Enterprise-Ready** – Multi-tenant SaaS deployment patterns, RBAC, and metrics.

---

## 📂 Project Structure

```text
📦 Project Structure
├── ⚙️ /core       → AITransactionEngine, graph validation, atomic execution
├── 🧠 /memory     → SnapshotEngine, content-addressed memory, branching & rollback
├── 🗄️ /storage    → Event log adapters (PostgreSQL, local)
├── 🛠️ /tools      → Isolation wrappers, circuit breakers, replay mocking
├── 🌍 /sdk        → Python & TypeScript/Zod language bindings
├── 💡 /examples   → Reference workflows
└── 📚 /docs       → Architecture & deployment docs
```

---

## ⚡ Quick Start

### 📦 1. Requirements
- 🐍 Python 3.12+
- 📘 Node / TypeScript 5.0+ (if using the TypeScript SDK)
- 🐘 PostgreSQL (optional for event logs)

### 💻 2. Install

```bash
pip install -r requirements.txt
# or create a venv first:
# python -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt
```

### 🏃 3. Run the example workflow

```bash
python examples/enterprise_workflow.py
```

This example evaluates a mock loan payload through a **DeterminAI Execution Graph (DEG)**. 📊

### 🔍 4. CLI (explore past runs)

```bash
python cli.py --help
```

---

## 🏛️ Core Principles

1. 📜 **Event Sourcing > Mutation** — Append-only operations for auditability.  
2. 🎯 **Determinism > Convenience** — Replays are bit-for-bit reproducible.  
3. 🧩 **Graph Compilation** — Validate with Pydantic (Python) / Zod (TS) before execution.

---

## 🔧 Architecture Overview

```text
+-------------------------+
|     💻 DeterminAI CLI   |
+-------------------------+
           │
           ▼
+-------------------------+
|      ⚙️ Core Engine     |
|  AITransactionEngine    |
|  begin/validate/commit  |
+-------------------------+
           │
           ▼
+-------------------------+
|   🧠 Memory Versioning  |
|  SnapshotEngine & refs  |
+-------------------------+
           │
           ▼
+-------------------------+
|     🗄️ Storage Layer    |
| PostgreSQL / Local / ...|
+-------------------------+
           │
           ▼
+-------------------------+
|      🛠️ Tools Layer     |
| Circuit Breakers, Mock  |
+-------------------------+
```

- ⚙️ **Core Engine (`/core`)** – Semantic boundaries with atomic transactions.  
- 🧠 **Memory Versioning (`/memory`)** – Constant-time snapshot lookups and branching.  
- 🗄️ **Storage (`/storage`)** – Event log management, pluggable backends.  
- 🛠️ **Tools (`/tools`)** – Deterministic safeguards and replay mocking.

---

## 🚀 Enterprise Deployment

Suitable for multi-tenant SaaS on cloud providers (AWS ☁️ / GCP 🌐 / Azure 🔵).

### 🔐 Environment variables (example)

```bash
export DATABASE_URL="postgresql://user:password@localhost:5432/determinai"
export DETERMINAI_ENCRYPTION_KEY="your-encryption-key-here"
export DETERMINAI_ADMIN_TOKEN="your-admin-token-here"
export DETERMINAI_AUDITOR_TOKEN="your-auditor-token-here"
export DETERMINAI_LLM_ADAPTER="openai"
export OPENAI_API_KEY="sk-your-openai-api-key"
```

> 💡 **Tip:** store secrets in your cloud provider's secret manager or Kubernetes Secrets. 🛡️

### ☸️ Example Kubernetes Deployment (adapt to your cluster)

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
        image: determinai/api:0.1.0
        ports:
        - containerPort: 8000
        envFrom:
        - secretRef:
            name: determinai-secrets
        command: ["uvicorn", "dashboard.app:app", "--host", "0.0.0.0", "--port", "8000"]
```

### 📊 Monitoring & Alerts

- 📡 Expose `/metrics` in Prometheus format.  
- 📈 Useful metrics:
  - `determinai_transactions_total{status="COMMITTED"}` ✅
  - `determinai_transactions_total{status="ROLLED_BACK"}` ❌

⚠️ Set alerts when rollback rate > `0.05` (5%).

---

## 📝 Examples

| 🏷️ Example | 📂 Path | 📄 Description |
|-----------|---------|-------------|
| 🏢 Enterprise Risk Workflow | `examples/enterprise_workflow.py` | Loan evaluation using deterministic graphs |
| 🔄 Replay Testing | `examples/replay_test.py` | Re-run prior traces and assert identical outputs |

---

## 📚 Documentation

- 📐 Architecture: `docs/architecture.md`  
- 🚀 Deployment: `docs/deployment.md`  
- 🐍 Python SDK: `sdk/python/README.md`  
- 📘 TypeScript SDK: `sdk/ts/README.md`

---

## 💡 Contributing

We welcome contributions! 🙌

1. 🍴 Fork the repo  
2. 🌱 Create a feature branch: `git checkout -b feat/your-feature`  
3. 🧪 Run tests & linters locally  
4. 📬 Submit a PR with a descriptive title and tests where applicable

📖 Please read `CONTRIBUTING.md` for guidelines.

---

## ⚖️ License

This project is licensed under the **MIT** License © 2026 DeterminAI. 📜

---
