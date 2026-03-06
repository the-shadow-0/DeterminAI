from fastapi import FastAPI, HTTPException, Request, Depends
from fastapi.responses import HTMLResponse, PlainTextResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from dashboard.rbac import verify_admin_access
import psycopg2
import json
import os
from contextlib import contextmanager

app = FastAPI(title="DeterminAI Audit & Replay Dashboard")
templates = Jinja2Templates(directory="dashboard/templates")

DB_URI = os.environ.get("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/determinai")

@contextmanager
def get_db_cursor():
    conn = psycopg2.connect(DB_URI)
    try:
        yield conn.cursor()
    finally:
        conn.close()

@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    """Serve the main UI dashboard."""
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/api/transactions")
def get_transactions():
    """Fetch all unique transaction keys from the event log."""
    try:
        with get_db_cursor() as cursor:
            # We are querying the event_state table to find all keys matching transaction structures
            cursor.execute("SELECT key, data, updated_at FROM event_state WHERE key LIKE 'tx_%' ORDER BY updated_at DESC LIMIT 50;")
            results = cursor.fetchall()
            transactions = []
            for row in results:
                 transactions.append({
                      "transaction_id": row[0].replace("tx_", ""),
                      "data": row[1],
                      "timestamp": row[2].isoformat()
                 })
            return {"transactions": transactions}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/replay/{transaction_id}", dependencies=[Depends(verify_admin_access)])
def replay_transaction(transaction_id: str):
    """Trigger a replay for a specific transaction by relying on DeterminAI SDK."""
    from sdk.python.determinai import (
        AITransactionEngine, MemoryStore, SnapshotEngine, PostgresStorageAdapter, EventLog
    )
    
    try:
        # Re-initialize the engine cleanly using Postgres SaaS config
        storage = PostgresStorageAdapter(DB_URI)
        engine = AITransactionEngine(MemoryStore(SnapshotEngine(storage)), EventLog(storage))
        
        replay_res = engine.replay(transaction_id)
        return replay_res
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Replay Failed: {str(e)}")

@app.get("/metrics")
def get_metrics():
    """Prometheus-compatible metrics endpoint."""
    try:
        with get_db_cursor() as cursor:
            # We want to count total transactions by status
            cursor.execute("SELECT data->>'commit_status', COUNT(*) FROM event_state WHERE key LIKE 'tx_%' GROUP BY data->>'commit_status';")
            results = cursor.fetchall()
            
            lines = [
                "# HELP determinai_transactions_total Total number of AI transactions",
                "# TYPE determinai_transactions_total counter"
            ]
            
            for status, count in results:
                lines.append(f'determinai_transactions_total{{status="{status}"}} {count}')
                
            return PlainTextResponse("\n".join(lines) + "\n")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/diff/{tx_id}", dependencies=[Depends(verify_admin_access)])
def diff_transaction(tx_id: str):
    """Trigger a diff between a transaction and itself (to prove determinism) or another tx."""
    from sdk.python.determinai import (
        AITransactionEngine, MemoryStore, SnapshotEngine, PostgresStorageAdapter, EventLog
    )
    
    try:
        storage = PostgresStorageAdapter(DB_URI)
        engine = AITransactionEngine(MemoryStore(SnapshotEngine(storage)), EventLog(storage))
        
        diff_res = engine.diff(tx_id, tx_id)
        return diff_res
    except Exception as e:
         raise HTTPException(status_code=500, detail=f"Diff Failed: {str(e)}")
