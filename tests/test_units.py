import unittest
import copy
from core.contracts import Transaction, NodeContract
from core.execution_graph import DeterministicExecutionGraph
from core.transaction_engine import AITransactionEngine
from memory.memory_store import MemoryStore
from memory.snapshot_engine import SnapshotEngine
from storage.storage_adapter import LocalStorageAdapter
from storage.event_log import EventLog

class TestTransactionLifecycle(unittest.TestCase):
    def setUp(self):
        self.storage = LocalStorageAdapter("/tmp/determinai_test")
        self.snapshot_engine = SnapshotEngine(self.storage)
        self.memory_store = MemoryStore(self.snapshot_engine)
        self.event_log = EventLog(self.storage)
        self.engine = AITransactionEngine(self.memory_store, self.event_log)

    def test_graph_compilation_and_hashing(self):
        graph = DeterministicExecutionGraph("TestGraph", "1.0.0")
        graph.add_node(NodeContract(
            node_id="Node1", node_type="LLMNode", 
            input_schema={"required": ["input_value"]}, 
            output_schema={"required": ["output_value"]}))
        
        graph_hash = graph.compile()
        self.assertIsNotNone(graph_hash)
        
        # Verify mutation throws exception after compilation
        with self.assertRaises(ValueError):
            graph.add_node(NodeContract(node_id="Node2", node_type="LLMNode", input_schema={}, output_schema={}))
            
    def test_transaction_commit_and_replay(self):
        graph = DeterministicExecutionGraph("TestGraph", "1.0.0")
        graph.add_node(NodeContract(node_id="Node1", node_type="LLMNode", input_schema={}, output_schema={}))
        graph.compile()
        
        self.memory_store.state = {"counter": 1}
        
        tx = self.engine.begin(graph, {"input": "test"}, "v1", {})
        
        # Simulating execution
        tx.output_payload = {"result": "success"}
        tx.state_delta = {"counter": 2}
        
        self.engine.commit(tx.transaction_id)
        
        # Assert memory updated
        self.assertEqual(self.memory_store.state["counter"], 2)
        
        # Assert replay works exactly
        replay = self.engine.replay(tx.transaction_id)
        self.assertTrue(replay["deterministic_match"])
        self.assertEqual(replay["inputs"], {"input": "test"})
        self.assertEqual(replay["reconstructed_memory"], {"counter": 1}) # Reconstructed from START of transaction
        
if __name__ == '__main__':
    unittest.main()
