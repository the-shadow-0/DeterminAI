import json
from abc import ABC, abstractmethod
from typing import Any, Dict
from core.logger import logger
import urllib.request
import urllib.error
import urllib.parse

class LLMAdapter(ABC):
    """
    Base strategy for generating structured responses.
    """
    def __init__(self, model_version: str):
        self.model_version = model_version
        
    @abstractmethod
    def generate(self, prompt: str, schema: Dict[str, Any]) -> Dict[str, Any]:
        """Generate purely conforming Pydantic/Zod representation mapped backwards."""
        pass

class OllamaAdapter(LLMAdapter):
    def __init__(self, model_version: str = "llama3"):
        super().__init__(model_version)
        self.endpoint = "http://localhost:11434/api/generate"
        
    def generate(self, prompt: str, schema: Dict[str, Any]) -> Dict[str, Any]:
        logger.info(f"Ollama generating locally via {self.model_version}")
        
        # Enforce json schema boundary
        payload = {
            "model": self.model_version,
            "prompt": f"{prompt}\n\nYou MUST return raw JSON. Strictly conform to this schema: {json.dumps(schema)}",
            "stream": False,
            "format": "json"
        }
        
        req = urllib.request.Request(self.endpoint, data=json.dumps(payload).encode('utf-8'))
        req.add_header('Content-Type', 'application/json')
        
        try:
            with urllib.request.urlopen(req) as response:
                result = json.loads(response.read().decode('utf-8'))
                text = result.get("response", "{}")
                return json.loads(text)
        except urllib.error.URLError as e:
            logger.error("Ollama connection failed (Ensure it is running via 'ollama run')", error=str(e))
            # Fallback for testing when Ollama isn't running
            return self._mock_fallback(schema)
        except json.JSONDecodeError:
            logger.error("Ollama broke JSON constraints", raw_output=text)
            raise ValueError("LLM generation failed JSON parser.")

    def _mock_fallback(self, schema: dict) -> dict:
         """Returns a safe predictable mock when no local runner is found."""
         logger.warn("Ollama adapter falling back to deterministic mock response.")
         # Return a valid mock of their requested schema keys
         res = {}
         for key in schema.get("required", []):
             res[key] = "mock_value_from_adapter"
         return res

class OpenAIAdapter(LLMAdapter):
    def __init__(self, model_version: str = "gpt-4o"):
        super().__init__(model_version)
        self.endpoint = "https://api.openai.com/v1/chat/completions"
        import os
        self.api_key = os.environ.get("OPENAI_API_KEY", "MOCK_KEY_FOR_TESTS")
        
    def generate(self, prompt: str, schema: Dict[str, Any]) -> Dict[str, Any]:
        logger.info(f"OpenAI GPT layer generating securely via {self.model_version}")
        
        if self.api_key == "MOCK_KEY_FOR_TESTS":
             logger.warn("No OPENAI_API_KEY set. Returning strict mocked JSON constraint.")
             res = {}
             for key in schema.get("required", []):
                 res[key] = f"mock_gpt_response_for_{key}"
             return res
             
        payload = {
            "model": self.model_version,
            "messages": [
                {"role": "system", "content": f"You are a deterministic engine boundary. Output strictly JSON adhering to: {json.dumps(schema)}"},
                {"role": "user", "content": prompt}
            ],
            "response_format": { "type": "json_object" }
        }
        req = urllib.request.Request(self.endpoint, data=json.dumps(payload).encode('utf-8'))
        req.add_header('Content-Type', 'application/json')
        req.add_header('Authorization', f'Bearer {self.api_key}')
        
        try:
            with urllib.request.urlopen(req) as response:
                result = json.loads(response.read().decode('utf-8'))
                text = result["choices"][0]["message"]["content"]
                return json.loads(text)
        except Exception as e:
             logger.error("GPT request failed", error=str(e))
def get_llm_adapter(model_version: str = "default") -> LLMAdapter:
    """Factory builder mapping CLI environment flags `DETERMINAI_LLM_ADAPTER` to concrete adapters."""
    import os
    choice = os.environ.get("DETERMINAI_LLM_ADAPTER", "mock")
    
    if choice == "ollama":
        if model_version == "default": model_version = "llama3"
        return OllamaAdapter(model_version)
    elif choice == "gpt5":
        if model_version == "default": model_version = "gpt-5"
        return OpenAIAdapter(model_version)
    else:
         logger.info("Using fallback mock LLM adapter for deterministic tests.")
         # Stub an anonymous mock adapter subclass inline
         class MockAdapter(LLMAdapter):
             def generate(self, prompt: str, schema: dict) -> dict:
                  res = {}
                  for key in schema.get("required", []):
                      res[key] = f"MOCK_{key.upper()}"
                  return res
         return MockAdapter(model_version)
