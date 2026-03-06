from typing import Dict, Any, List
from .snapshot_engine import SnapshotEngine
from core.logger import logger

class MemoryStore:
    def __init__(self, snapshot_engine: SnapshotEngine):
        self.state: Dict[str, Any] = {}
        self.snapshot_engine = snapshot_engine
        
    def snapshot(self) -> str:
        """Saves current state and returns hash reference."""
        return self.snapshot_engine.save_snapshot(self.state)
        
    def apply_delta(self, delta: Dict[str, Any]):
        """Applies state changes from an AI transaction output."""
        logger.info("Applying memory delta", dict_update_keys=list(delta.keys()))
        self.state.update(delta)
            
    def rollback(self, snapshot_hash: str):
        """Revert entire memory store to previous safe state."""
        logger.warn("Rolling back memory to historical snapshot", snapshot_hash=snapshot_hash)
        past_state = self.snapshot_engine.get_snapshot(snapshot_hash)
        if past_state is None:
            raise ValueError("Snapshot not found.")
        self.state = past_state
        
    def branch(self) -> 'MemoryStore':
        """Creates an independent clone for branching execution logic."""
        logger.info("Branching memory store from current state")
        new_store = MemoryStore(self.snapshot_engine)
        new_store.state = dict(self.state)
        return new_store
