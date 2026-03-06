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
from core.llm_adapters import get_llm_adapter

class EnterpriseResourceDB(ToolAdapter):
    def __init__(self):
        super().__init__("EnterpriseResourceDB")
        
    def _execute_impl(self, payload: dict) -> dict:
        return {"available_budget": 50000, "staff_count": 12}

def setup_runtime():
    storage = LocalStorageAdapter("/tmp/determinai_enterprise")
    return AITransactionEngine(MemoryStore(SnapshotEngine(storage)), EventLog(storage))

def run_workflow():
    engine = setup_runtime()
    
    graph = DeterministicExecutionGraph("EnterpriseOperations", "1.0.0")
    graph.add_node(NodeContract(
        node_id="FetchResources",
        node_type="ToolNode",
        input_schema={"required": ["project_id"]},
        output_schema={"required": ["available_budget", "staff_count"]},
    ))
    graph.add_node(NodeContract(
        node_id="LLMResourceAllocation",
        node_type="LLMNode",
        input_schema={"required": ["available_budget", "staff_count", "requested_resources"]},
        output_schema={"required": ["allocation_decision", "allocated_budget"]},
    ))
    graph.compile()
    
    tx = engine.begin(
        graph=graph,
        input_payload={"project_id": "PRJ-Alpha", "requested_resources": {"budget": 40000, "staff": 5}},
        prompt_version="v3.0",
        model_versions={"LLMResourceAllocation": "gpt-4"}
    )
    
    tool = EnterpriseResourceDB()
    tool_input = {"project_id": "PRJ-Alpha"}
    tool_output = tool.execute(tool_input)
    tx.tool_call_graph.append(tool.record_call(tool_input, tool_output))
    
    print("\n--- [DeterminAI] LLM Analysis ---")
    adapter = get_llm_adapter()
    llm = LLMNodeRunner(graph.nodes["LLMResourceAllocation"], adapter)
    llm_payload = {
        "available_budget": tool_output["available_budget"],
        "staff_count": tool_output["staff_count"],
        "requested_resources": "Budget: 40000, Staff: 5"
    }
    llm_output = llm.execute(llm_payload)
    
    tx.output_payload = llm_output
    engine.commit(tx.transaction_id)
    
    print("\n--- Enterprise Ops Replay ---")
    res = engine.replay(tx.transaction_id)
    print(json.dumps(res, indent=2))

    print("\n--- Testing Diff ---")
    diff_result = engine.diff(tx.transaction_id, tx.transaction_id)
    assert diff_result["outputs_diff"] == True
    print("Diff ok:", diff_result)

def run_rollback_edge_case():
    engine = setup_runtime()
    graph = DeterministicExecutionGraph("EnterpriseOps_Edge", "1.0.0")
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
