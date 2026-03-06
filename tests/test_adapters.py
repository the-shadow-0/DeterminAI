import unittest
from core.llm_adapters import get_llm_adapter, OllamaAdapter, OpenAIAdapter
from tools.tool_adapter import ToolAdapter
import time
import os

class FlakyTool(ToolAdapter):
    def __init__(self):
        super().__init__("FlakyTool", timeout_ms=1000)
        self.attempts = 0
        
    def _execute_impl(self, payload: dict) -> dict:
        self.attempts += 1
        if self.attempts < 3:
            raise RuntimeError("Temporary Flake")
        return {"result": "success on attempt 3"}

class TestAdapters(unittest.TestCase):
    def test_llm_factory_mock(self):
        os.environ["DETERMINAI_LLM_ADAPTER"] = "mock"
        adapter = get_llm_adapter()
        res = adapter.generate("Prompt here", {"required": ["dummy_key"]})
        self.assertEqual(res["dummy_key"], "MOCK_DUMMY_KEY")
        
    def test_llm_factory_ollama(self):
        os.environ["DETERMINAI_LLM_ADAPTER"] = "ollama"
        adapter = get_llm_adapter()
        self.assertIsInstance(adapter, OllamaAdapter)
        self.assertEqual(adapter.model_version, "llama3")
        
    def test_llm_factory_gpt5(self):
        os.environ["DETERMINAI_LLM_ADAPTER"] = "gpt5"
        adapter = get_llm_adapter("gpt-5-turbo")
        self.assertIsInstance(adapter, OpenAIAdapter)
        self.assertEqual(adapter.model_version, "gpt-5-turbo")

    def test_tool_adapter_retry_success(self):
        tool = FlakyTool()
        start = time.time()
        res = tool.execute({"test": "data"}, max_retries=3)
        self.assertEqual(res["result"], "success on attempt 3")
        self.assertEqual(tool.attempts, 3)
        self.assertTrue(time.time() - start > 0.1) # Backoff took place

    def test_tool_adapter_retry_exhausted(self):
        tool = FlakyTool()
        with self.assertRaises(RuntimeError):
            tool.execute({"test": "data"}, max_retries=2)
            
if __name__ == "__main__":
    unittest.main()
