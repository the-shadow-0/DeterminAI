from abc import ABC, abstractmethod
from typing import Dict, Any
import time
from core.logger import logger

class ToolAdapter(ABC):
    """
    Wraps deterministic adapters around external tools allowing record/replay.
    Provides a stable boundary, circuit breakers, and timeouts.
    """
    def __init__(self, name: str, timeout_ms: int = 5000):
        self.name = name
        self.timeout_ms = timeout_ms
        
    def validate_input(self, payload: Dict[str, Any]) -> bool:
        """Override to validate tool input constraints."""
        return True
        
    def validate_output(self, payload: Dict[str, Any]) -> bool:
        """Override to validate tool output constraints."""
        return True
        
    @abstractmethod
    def _execute_impl(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Internal execution logic implementation. Do not call directly."""
        pass
        
    def execute(self, payload: Dict[str, Any], max_retries: int = 3) -> Dict[str, Any]:
        """Bounded execution with logging validation and retry logic."""
        logger.info(f"Executing tool: {self.name}", payload=payload)
        
        if not self.validate_input(payload):
            logger.error(f"Invalid input to tool {self.name}", payload=payload)
            raise ValueError(f"Invalid input to tool {self.name}")
            
        start_t = time.time()
        
        for attempt in range(max_retries):
            try:
                output = self._execute_impl(payload)
                break
            except Exception as e:
                logger.error(f"Tool {self.name} failed during execution (Attempt {attempt+1}/{max_retries})", error=str(e))
                if attempt == max_retries - 1:
                    raise RuntimeError(f"Tool {self.name} failed after {max_retries} attempts: {str(e)}")
                time.sleep((2 ** attempt) * 0.1) # Exponential backoff
                
        end_t = time.time()
        elapsed_ms = (end_t - start_t) * 1000
        
        if elapsed_ms > self.timeout_ms:
            logger.warn(f"Tool {self.name} execution exceeded timeout limit", elapsed_ms=elapsed_ms, timeout_ms=self.timeout_ms)
            raise TimeoutError(f"Tool {self.name} timed out after {elapsed_ms}ms")
            
        if not self.validate_output(output):
            logger.error(f"Invalid output from tool {self.name}", output=output)
            raise ValueError(f"Invalid output from tool {self.name}")
            
        logger.info(f"Tool {self.name} executed successfully", elapsed_ms=elapsed_ms)
        return output

    def record_call(self, inputs: dict, outputs: dict) -> dict:
        return {
            "tool_name": self.name,
            "inputs": inputs,
            "outputs": outputs,
            "timestamp": time.time()
        }
        
    def replay_call(self, recorded_call: dict) -> dict:
        """Mock return the recorded response during replay mode without side effects."""
        logger.info(f"Replaying tool {self.name} call", recorded_output=recorded_call["outputs"])
        return recorded_call["outputs"]
