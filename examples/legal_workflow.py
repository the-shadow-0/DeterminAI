import sys
import os
import json

sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from sdk.python.determinai import (
    AITransactionEngine, DeterministicExecutionGraph, ToolAdapter,
    MemoryStore, SnapshotEngine, LocalStorageAdapter, EventLog
)
from core.contracts import NodeContract
from core.execution_graph import LLMNodeRunner

class LegalDB(ToolAdapter):
    def __init__(self):
        super().__init__("LegalDB")
        
    def _execute_impl(self, payload: dict) -> dict:
        return {"document": "Party A indemnifies Party B against all third-party claims arising out of this Agreement."}

def setup_runtime():
    storage = LocalStorageAdapter("/tmp/determinai_legal")
    return AITransactionEngine(MemoryStore(SnapshotEngine(storage)), EventLog(storage))

def run_workflow():
    engine = setup_runtime()
    
    graph = DeterministicExecutionGraph("LegalDocumentReview", "1.0.0")
    graph.add_node(NodeContract(
        node_id="FetchDocument",
        node_type="ToolNode",
        input_schema={"required": ["doc_id"]},
        output_schema={"required": ["document"]},
    ))
    graph.add_node(NodeContract(
        node_id="AnalyzeIndemnity",
        node_type="LLMNode",
        input_schema={"required": ["document", "focus"]},
        output_schema={"required": ["risk_level", "issues"]},
        guardrails=["deny_if_risk_critical"]
    ))
    graph.compile()
    
    tx = engine.begin(
        graph=graph,
        input_payload={"doc_id": "D-991", "focus": "Indemnification"},
        prompt_version="v2.0",
        model_versions={"AnalyzeIndemnity": "claude-3-opus"}
    )
    
    from core.llm_adapters import get_llm_adapter
    
    tool = LegalDB()
    tool_input = {"doc_id": "D-991"}
    tool_output = tool.execute(tool_input)
    tx.tool_call_graph.append(tool.record_call(tool_input, tool_output))
    
    print("\n--- [DeterminAI] LLM Analysis ---")
    adapter = get_llm_adapter()
    llm = LLMNodeRunner(graph.nodes["AnalyzeIndemnity"], adapter)
    llm_payload = {"document": tool_output["document"], "focus": "Indemnification"}
    llm_output = llm.execute(llm_payload)
    
    tx.output_payload = llm_output
    engine.commit(tx.transaction_id)
    
    print("\n--- Legal Review Replay ---")
    res = engine.replay(tx.transaction_id)
    print(json.dumps(res, indent=2))

    print("\n--- Testing Diff ---")
    diff_result = engine.diff(tx.transaction_id, tx.transaction_id)
    assert diff_result["outputs_diff"] == True
    print("Diff ok:", diff_result)

def run_rollback_edge_case():
    engine = setup_runtime()
    graph = DeterministicExecutionGraph("LegalWorkflow_Edge", "1.0.0")
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
    run_workflow()
    run_rollback_edge_case()
