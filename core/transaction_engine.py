import copy
from typing import Dict, Any, Optional
from .contracts import Transaction, CommitStatus
from .execution_graph import DeterministicExecutionGraph
from .logger import logger

class AITransactionEngine:
    def __init__(self, memory_store, event_log):
        self.memory_store = memory_store
        self.event_log = event_log
        self.active_transactions: Dict[str, Transaction] = {}
        
    def begin(self, graph: DeterministicExecutionGraph, input_payload: Dict[str, Any], prompt_version: str, model_versions: Dict[str, str]) -> Transaction:
        if not graph._compiled:
            logger.error("Attempted to start transaction with uncompiled graph.", graph_name=graph.name)
            raise ValueError("Execution graph must be compiled before starting transaction.")
            
        memory_ref = self.memory_store.snapshot()
        
        tx = Transaction(
            execution_graph_hash=graph.get_hash(),
            execution_graph_version=graph.version,
            model_versions=model_versions,
            prompt_version=prompt_version,
            input_payload=copy.deepcopy(input_payload),
            memory_snapshot_reference=memory_ref,
            commit_status=CommitStatus.PENDING
        )
        self.active_transactions[tx.transaction_id] = tx
        
        logger.info("Transaction started", transaction_id=tx.transaction_id, graph_hash=tx.execution_graph_hash)
        return tx
        
    def validate(self, transaction_id: str) -> bool:
        tx = self.active_transactions.get(transaction_id)
        if not tx:
            logger.error("Validation failed: Active transaction not found.", transaction_id=transaction_id)
            raise ValueError(f"Active transaction {transaction_id} not found.")
        if tx.commit_status != CommitStatus.PENDING:
            logger.error("Validation failed: Transaction not pending.", transaction_id=transaction_id, status=tx.commit_status.value)
            raise ValueError("Only PENDING transactions can be validated.")
            
        if tx.output_payload is None:
            logger.warn("Validation failed: Output payload is None.", transaction_id=transaction_id)
            return False
            
        logger.info("Transaction validated successfully", transaction_id=transaction_id)
        return True
        
    def commit(self, transaction_id: str) -> None:
        if not self.validate(transaction_id):
            logger.error("Commit aborted: Transaction failed validation.", transaction_id=transaction_id)
            raise ValueError(f"Transaction {transaction_id} failed validation.")
            
        tx = self.active_transactions[transaction_id]
        tx.commit_status = CommitStatus.COMMITTED
        
        self.event_log.append(tx)
        
        if tx.state_delta:
            self.memory_store.apply_delta(tx.state_delta)
            
        del self.active_transactions[transaction_id]
        logger.info("Transaction committed successfully", transaction_id=transaction_id)
        
    def rollback(self, transaction_id: str) -> None:
        tx = self.active_transactions.get(transaction_id)
        if tx:
            tx.commit_status = CommitStatus.ROLLED_BACK
            self.event_log.append(tx)
            del self.active_transactions[transaction_id]
            logger.info("Transaction rolled back", transaction_id=transaction_id)
        else:
            logger.warn("Rollback requested for unknown or inactive transaction", transaction_id=transaction_id)

    def replay(self, transaction_id: str):
        logger.info("Starting deterministic replay", transaction_id=transaction_id)
        from .replay_engine import ReplayEngine
        engine = ReplayEngine(self.event_log, self.memory_store)
        return engine.replay(transaction_id)
        
    def diff(self, transaction_id_a: str, transaction_id_b: str) -> Dict[str, Any]:
        logger.info("Diffing transactions", tx_a=transaction_id_a, tx_b=transaction_id_b)
        tx_a: Transaction = self.event_log.get(transaction_id_a)
        tx_b: Transaction = self.event_log.get(transaction_id_b)
        
        if not tx_a or not tx_b:
            logger.error("Transactions not found for diffing", tx_a=transaction_id_a, tx_b=transaction_id_b)
            raise ValueError("Transactions not found")
        
        return {
            "inputs_diff": tx_a.input_payload == tx_b.input_payload,
            "outputs_diff": tx_a.output_payload == tx_b.output_payload,
            "graph_diff": tx_a.execution_graph_hash == tx_b.execution_graph_hash,
            "memory_diff": tx_a.memory_snapshot_reference == tx_b.memory_snapshot_reference,
        }
