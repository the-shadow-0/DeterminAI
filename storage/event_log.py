from typing import List, Optional
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from core.contracts import Transaction
from storage.storage_adapter import StorageAdapter

class EventLog:
    """
    Append-only representation of transaction logs.
    """
    def __init__(self, storage_adapter: StorageAdapter):
        self.storage = storage_adapter
        self._index: List[str] = []
        
        # Recover index if exists
        saved_index = self.storage.load("event_log_index")
        if saved_index:
            self._index = saved_index.get("transactions", [])
            
    def append(self, tx: Transaction) -> None:
        tx_id = tx.transaction_id
        self.storage.save(f"tx_{tx_id}", tx.model_dump())
        self._index.append(tx_id)
        # Flush index
        self.storage.save("event_log_index", {"transactions": self._index})
        
    def get(self, transaction_id: str) -> Optional[Transaction]:
        data = self.storage.load(f"tx_{transaction_id}")
        if data:
            return Transaction(**data)
        return None
        
    def get_by_graph(self, graph_hash: str) -> List[Transaction]:
        matches = []
        for tx_id in self._index:
            tx = self.get(tx_id)
            if tx and tx.execution_graph_hash == graph_hash:
                matches.append(tx)
        return matches
