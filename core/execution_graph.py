import json
import hashlib
import time
from typing import Dict, Any, List, Optional, Iterator
from pydantic import ValidationError
from .contracts import NodeContract, EdgeContract
from .logger import logger
from .llm_adapters import LLMAdapter

class LLMNodeRunner:
    """Runner representing LLM API execution. Connects to configured LLMAdapters."""
    def __init__(self, node: NodeContract, adapter: Optional[LLMAdapter] = None):
        self.node = node
        self.adapter = adapter

    def execute(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Generates structured JSON via the injected LLM adapter."""
        if not self.adapter:
            raise ValueError(f"LLMNode {self.node.node_id} requires an instantiated LLMAdapter.")
            
        logger.info(f"LLMNode {self.node.node_id} starting generation", model=self.adapter.model_version)
        
        # In a real environment we'd parse the prompt template. We'll simulate by dumping payload.
        prompt = f"Analyze this payload: {json.dumps(payload)}"
        
        try:
            result = self.adapter.generate(prompt=prompt, schema=self.node.output_schema)
            logger.info(f"LLMNode {self.node.node_id} finished generation", result=result)
            return result
        except ValueError as e:
            logger.error(f"LLMNode {self.node.node_id} failed JSON validation from adapter", error=str(e))
            raise

class ValidationNodeRunner:
    """Mock runner representing pure rule validation."""
    def __init__(self, node: NodeContract):
        self.node = node
        
    def execute(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Runs validation_rules and guardrails on the payload.
        Returns payload unmodified or throws error.
        """
        logger.info(f"ValidationNode {self.node.node_id} checking payload", payload=payload)
        
        # Execute generic constraints defined on contract
        if "risk_score_between_0_and_100" in self.node.validation_rules:
            if not (0 <= payload.get("risk_score", -1) <= 100):
                raise ValueError("Validation Failed: risk_score must be between 0 and 100")
                
        if "deny_if_score_under_650" in self.node.guardrails:
             # In complete system, this would flag an exception or reroute logic
             if payload.get("credit_score", 0) < 650 and payload.get("risk_decision") == "APPROVED":
                 raise ValueError("Guardrail Triggered: Cannot approve score under 650")
                 
        return payload


class DeterministicExecutionGraph:
    """
    A typed DAG representing an AI execution plan logically compiled into a hash.
    No mutation is allowed after compilation.
    """
    def __init__(self, name: str, version: str):
        self.name = name
        self.version = version
        self.nodes: Dict[str, NodeContract] = {}
        self.edges: List[EdgeContract] = []
        self._compiled = False
        self._hash = None
    
    def add_node(self, node: NodeContract):
        if self._compiled:
            raise ValueError("Cannot mutate a compiled graph.")
        self.nodes[node.node_id] = node
        
    def add_edge(self, edge: EdgeContract):
        if self._compiled:
            raise ValueError("Cannot mutate a compiled graph.")
        if edge.source_id not in self.nodes or edge.target_id not in self.nodes:
            raise ValueError("Node IDs for edge must exist in graph.")
        self.edges.append(edge)
        
    def compile(self) -> str:
        """
        Calculates the topological and semantic hash of the DAG.
        Locks the graph from further modification.
        """
        graph_dict = {
            "name": self.name,
            "version": self.version,
            "nodes": [self.nodes[k].model_dump() for k in sorted(self.nodes.keys())],
            "edges": [e.model_dump() for e in self.edges]
        }
        graph_json = json.dumps(graph_dict, sort_keys=True)
        self._hash = hashlib.sha256(graph_json.encode('utf-8')).hexdigest()
        self._compiled = True
        logger.info("Compiled execution graph", graph_name=self.name, hash=self._hash)
        return self._hash

    def get_hash(self) -> str:
        if not self._compiled:
            raise ValueError("Graph must be compiled to get its hash.")
        return self._hash
        
    def validate_inputs(self, node_id: str, payload: Dict[str, Any]) -> bool:
        """
        Validates the incoming payload against the node's input schema.
        MVP: Basic key presence validation. Can be extended to strict JSON schema validation.
        """
        node = self.nodes.get(node_id)
        if not node:
            raise ValueError(f"Unknown node {node_id}")
        
        required_keys = node.input_schema.get("required", [])
        for key in required_keys:
            if key not in payload:
                raise ValueError(f"Missing required input key: {key} for node {node_id}")
                
        # Future: Use `jsonschema` to validate full payloads
        return True

    def validate_outputs(self, node_id: str, payload: Dict[str, Any]) -> bool:
        """
        Validates the generated output against the node's output schema and guardrails.
        """
        node = self.nodes.get(node_id)
        if not node:
            raise ValueError(f"Unknown node {node_id}")
            
        required_keys = node.output_schema.get("required", [])
        for key in required_keys:
            if key not in payload:
                raise ValueError(f"Missing required output key: {key} for node {node_id}")
                
        return True
