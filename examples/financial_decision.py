import sys
import os
import json

# Add project root to path for local execution
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from sdk.python.determinai import (
    AITransactionEngine,
    DeterministicExecutionGraph,
    ToolAdapter,
    MemoryStore,
    SnapshotEngine,
    LocalStorageAdapter,
    EventLog
)
from core.contracts import NodeContract

class CreditScoreTool(ToolAdapter):
    def __init__(self):
        super().__init__("CreditScoreTool")
        
    def _execute_impl(self, payload: dict) -> dict:
        applicant = payload.get("name", "Unknown")
        # Mock logic
        score = 750 if applicant == "Alice" else 620
        return {"score": score}

def setup_runtime():
    storage = LocalStorageAdapter("/tmp/determinai_example")
    snapshot_engine = SnapshotEngine(storage)
    memory_store = MemoryStore(snapshot_engine)
    event_log = EventLog(storage)
    engine = AITransactionEngine(memory_store, event_log)
    return engine

def run_enterprise_workflow():
    engine = setup_runtime()
    
    print("--- [DeterminAI] Building Execution Graph ---")
    graph = DeterministicExecutionGraph("EnterpriseRiskDecision", "1.0.0")
    
    graph.add_node(NodeContract(
        node_id="CheckCredit",
        node_type="ToolNode",
        input_schema={"required": ["name"]},
        output_schema={"required": ["score"]},
    ))
    
    graph.add_node(NodeContract(
        node_id="LLMRiskEvaluation",
        node_type="LLMNode",
        input_schema={"required": ["applicant_data", "credit_score"]},
        output_schema={"required": ["risk_decision", "risk_score"]},
        validation_rules=["risk_score_between_0_and_100"],
        guardrails=["deny_if_score_under_650"]
    ))
    
    graph_hash = graph.compile()
    print(f"Compiled Graph Hash: {graph_hash}")
    
    print("\n--- [DeterminAI] Beginning AI Transaction ---")
    input_payload = {
        "applicant_data": {
            "name": "Alice",
            "income": 120000,
            "loan_amount": 500000
        }
    }
    tx = engine.begin(
        graph=graph,
        input_payload=input_payload,
        prompt_version="v2.1",
        model_versions={"CheckCredit": "mock", "LLMRiskEvaluation": "gpt-4"}
    )
    print(f"Started Transaction: {tx.transaction_id}")
    
    # Simulated execution
    from core.execution_graph import LLMNodeRunner
    from core.llm_adapters import get_llm_adapter
    
    print("\n--- [DeterminAI] Executing Nodes ---")
    tool = CreditScoreTool()
    tool_input = {"name": input_payload["applicant_data"]["name"]}
    tool_output = tool.execute(tool_input)
    print(f"Tool executed. Output: {tool_output}")
    
    recorded_tool_call = tool.record_call(tool_input, tool_output)
    tx.tool_call_graph.append(recorded_tool_call)
    
    print("\n--- [DeterminAI] LLM Analysis ---")
    adapter = get_llm_adapter()
    llm = LLMNodeRunner(graph.nodes["LLMRiskEvaluation"], adapter)
    llm_payload = {"applicant_data": input_payload["applicant_data"], "credit_score": tool_output["score"]}
    llm_output = llm.execute(llm_payload)
        
    tx.output_payload = llm_output
    tx.state_delta = {"last_decision_id": tx.transaction_id, "system_state": "ACTIVE"}
    
    print("\n--- [DeterminAI] Committing Transaction ---")
    engine.commit(tx.transaction_id)
    print(f"Transaction {tx.transaction_id} committed successfully!")
    print(f"Final Output: {json.dumps(tx.output_payload, indent=2)}")
    
    print("\n--- [DeterminAI] Replaying Transaction ---")
    # Demonstrates deterministic reproduction capability
    replay_result = engine.replay(tx.transaction_id)
    print(json.dumps(replay_result, indent=2))
    
    print("\n--- Testing Diff ---")
    diff_result = engine.diff(tx.transaction_id, tx.transaction_id)
    assert diff_result["outputs_diff"] == True
    print("Diff ok:", diff_result)
    
    print("\n[✔] Workflow execution complete.")

def run_rollback_edge_case():
    engine = setup_runtime()
    graph = DeterministicExecutionGraph("FinancialDecision_Edge", "1.0.0")
    graph.compile()
    
    try:
        tx = engine.begin(graph, {}, "v1", {})
        if tx.output_payload is None:
            raise ValueError("Edge Case: Missing Output")
        engine.commit(tx.transaction_id)
    except Exception as e:
        print(f"\n--- Edge Case Caught: {e} ---")
        engine.rollback(tx.transaction_id)
        print(f"Transaction {tx.transaction_id} rolled back successfully.")

if __name__ == "__main__":
    run_enterprise_workflow()
    run_rollback_edge_case()
