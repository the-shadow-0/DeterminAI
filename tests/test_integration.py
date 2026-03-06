import sys
import os
import unittest

sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from examples.financial_decision import run_enterprise_workflow as run_financial, run_rollback_edge_case as run_financial_edge
from examples.healthcare_triage import run_workflow as run_healthcare, run_rollback_edge_case as run_healthcare_edge
from examples.legal_workflow import run_workflow as run_legal, run_rollback_edge_case as run_legal_edge
from examples.enterprise_ops import run_workflow as run_enterprise, run_rollback_edge_case as run_enterprise_edge

class TestIntegrationWorkflows(unittest.TestCase):
    
    def _run_with_adapters(self, func, name):
        adapters = ["mock", "ollama", "gpt5"]
        for adapter in adapters:
            with self.subTest(adapter=adapter, workflow=name):
                os.environ["DETERMINAI_LLM_ADAPTER"] = adapter
                try:
                    func()
                except Exception as e:
                    self.fail(f"[{adapter}] {name} workflow failed: {str(e)}")

    def test_financial_decision_runs(self):
        self._run_with_adapters(run_financial, "Financial")
            
    def test_healthcare_workflow_runs(self):
        self._run_with_adapters(run_healthcare, "Healthcare")
            
    def test_legal_workflow_runs(self):
        self._run_with_adapters(run_legal, "Legal")
             
    def test_enterprise_ops_runs(self):
        self._run_with_adapters(run_enterprise, "Enterprise")

    def test_edge_cases(self):
        # We only need to run edge cases in mock to verify the rollback boundary
        os.environ["DETERMINAI_LLM_ADAPTER"] = "mock"
        try:
            run_financial_edge()
            run_healthcare_edge()
            run_legal_edge()
            run_enterprise_edge()
        except Exception as e:
            self.fail(f"Edge case rollback execution failed: {str(e)}")

if __name__ == '__main__':
    unittest.main()
