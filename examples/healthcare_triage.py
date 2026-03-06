import sys
import os
import json

sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from sdk.python.determinai import (
    AITransactionEngine, DeterministicExecutionGraph, ToolAdapter,
    MemoryStore, SnapshotEngine, LocalStorageAdapter, EventLog
)
from core.contracts import NodeContract
from core.execution_graph import LLMNodeRunner, ValidationNodeRunner

class PatientRecordSystem(ToolAdapter):
    def __init__(self):
        super().__init__("PatientRecordSystem", timeout_ms=3000)

    def _execute_impl(self, payload: dict) -> dict:
        patient_id = payload.get("patient_id", "Unknown")
        # Mock API logic
        if patient_id == "P123":
            return {"history": ["hypertension", "diabetes"], "allergies": ["penicillin"]}
        return {"history": [], "allergies": []}


def setup_runtime():
    storage = LocalStorageAdapter("/tmp/determinai_healthcare")
    snapshot_engine = SnapshotEngine(storage)
    memory_store = MemoryStore(snapshot_engine)
    event_log = EventLog(storage)
    engine = AITransactionEngine(memory_store, event_log)
    return engine

def run_workflow():
    engine = setup_runtime()
    
    graph = DeterministicExecutionGraph("HealthcareTriage", "1.0.0")
    graph.add_node(NodeContract(
        node_id="FetchHistory",
        node_type="ToolNode",
        input_schema={"required": ["patient_id"]},
        output_schema={"required": ["history", "allergies"]},
    ))
    graph.add_node(NodeContract(
        node_id="TriageLLM",
        node_type="LLMNode",
        input_schema={"required": ["symptoms", "history"]},
        output_schema={"required": ["triage_level", "recommended_action"]},
        guardrails=["deny_if_triage_level_incorrect"]
    ))
    graph.compile()
    
    input_payload = {
        "symptoms": ["chest pain", "shortness of breath"],
        "patient_id": "P123"
    }
    
    tx = engine.begin(
        graph=graph,
        input_payload=input_payload,
        prompt_version="v1.0",
        model_versions={"TriageLLM": "gpt-4-medical"}
    )
    
    # Tool Execution
    tool = PatientRecordSystem()
    tool_input = {"patient_id": input_payload["patient_id"]}
    tool_output = tool.execute(tool_input)
    tx.tool_call_graph.append(tool.record_call(tool_input, tool_output))
    
    from core.llm_adapters import get_llm_adapter
    
    print("\n--- [DeterminAI] LLM Analysis ---")
    adapter = get_llm_adapter()
    llm = LLMNodeRunner(graph.nodes["TriageLLM"], adapter)
    llm_payload = {"symptoms": input_payload["symptoms"], "history": tool_output["history"]}
    llm_output = llm.execute(llm_payload)
    
    tx.output_payload = llm_output
    tx.state_delta = {"last_triage": tx.transaction_id, "active_patients": ["P123"]}
    
    engine.commit(tx.transaction_id)
    print("\n--- Testing Replay ---")
    replay_result = engine.replay(tx.transaction_id)
    print("Replayed Triage exactly:", replay_result)
    
    print("\n--- Testing Diff ---")
    # Trivial diff against itself should show no difference
    diff_result = engine.diff(tx.transaction_id, tx.transaction_id)
    assert diff_result["outputs_diff"] == True
    print("Diff ok:", diff_result)

def run_rollback_edge_case():
    engine = setup_runtime()
    graph = DeterministicExecutionGraph("HealthcareTriage_Edge", "1.0.0")
    # Missing nodes for edge case test
    graph.compile()
    
    try:
        tx = engine.begin(graph, {}, "v1", {})
        # Simulating a failure or validation error
        if tx.output_payload is None:
            raise ValueError("Edge Case: Missing Output")
        engine.commit(tx.transaction_id)
    except Exception as e:
        print(f"\n--- Edge Case Caught: {e} ---")
        engine.rollback(tx.transaction_id)
        print(f"Transaction {tx.transaction_id} rolled back successfully.")

if __name__ == "__main__":
    run_workflow()
    run_rollback_edge_case()
