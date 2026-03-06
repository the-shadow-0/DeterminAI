import uuid
import time
from enum import Enum
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field, ConfigDict

class CommitStatus(str, Enum):
    PENDING = "PENDING"
    COMMITTED = "COMMITTED"
    ROLLED_BACK = "ROLLED_BACK"

class NodeContract(BaseModel):
    node_id: str
    node_type: str  # LLMNode, ToolNode, MemoryNode, ValidationNode
    input_schema: Dict[str, Any]
    output_schema: Dict[str, Any]
    validation_rules: List[str] = Field(default_factory=list)
    guardrails: List[str] = Field(default_factory=list)

class EdgeContract(BaseModel):
    source_id: str
    target_id: str
    data_mapping: Dict[str, str]  # Map source output keys -> target input keys

class Snapshot(BaseModel):
    model_config = ConfigDict(protected_namespaces=())
    
    snapshot_hash: str
    prompt_state: Dict[str, Any]
    model_version: str
    input_tokens: int
    output_tokens: int
    tool_outputs: List[Dict[str, Any]]
    memory_state: Dict[str, Any]
    created_at: float = Field(default_factory=time.time)

class Transaction(BaseModel):
    model_config = ConfigDict(protected_namespaces=())

    transaction_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    execution_graph_hash: str
    execution_graph_version: str = "1.0.0"
    model_versions: Dict[str, str]
    prompt_version: str
    input_payload: Dict[str, Any]
    memory_snapshot_reference: str
    tool_call_graph: List[Dict[str, Any]] = Field(default_factory=list)
    output_payload: Optional[Dict[str, Any]] = None
    state_delta: Optional[Dict[str, Any]] = None
    commit_status: CommitStatus = CommitStatus.PENDING
    timestamp: float = Field(default_factory=time.time)
