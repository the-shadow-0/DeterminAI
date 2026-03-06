import json
import hashlib
from typing import Dict, Any, Optional
from core.logger import logger

class SnapshotEngine:
    """
    Immutable, content-addressable memory state snapshots.
    """
    def __init__(self, storage_adapter):
        self.storage = storage_adapter
        
    def save_snapshot(self, state: Dict[str, Any]) -> str:
        state_str = json.dumps(state, sort_keys=True)
        h = hashlib.sha256(state_str.encode('utf-8')).hexdigest()
        
        # Objects addressed by hash
        self.storage.save(f"snapshot_{h}", state)
        logger.info("Snapshot saved to storage", snapshot_hash=h)
        return h
        
    def get_snapshot(self, snapshot_hash: str) -> Optional[Dict[str, Any]]:
        logger.debug("Loading snapshot from storage", snapshot_hash=snapshot_hash)
        return self.storage.load(f"snapshot_{snapshot_hash}")
