import argparse
import sys
import json
import os
from importlib.util import spec_from_file_location, module_from_spec
sys.path.append(os.path.dirname(__file__))

from sdk.python.determinai import (
    AITransactionEngine, EventLog, LocalStorageAdapter, MemoryStore, 
    SnapshotEngine, PostgresStorageAdapter
)

def main():
    parser = argparse.ArgumentParser(description="DeterminAI Runtime CLI")
    subparsers = parser.add_subparsers(dest="command")
    
    subparsers.add_parser("init", help="Initialize a new determinai project")
    
    run_parser = subparsers.add_parser("run", help="Execute a python script workflow")
    run_parser.add_argument("script_path", help="Path to workflow python execution script")
    run_parser.add_argument("--llm", choices=["ollama", "gpt5", "mock"], default="mock", help="Underlying LLM Adapter to use")
    
    replay_parser = subparsers.add_parser("replay", help="Replay a transaction deterministically")
    replay_parser.add_argument("transaction_id", help="Transaction ID")
    replay_parser.add_argument("--storage", choices=["local", "postgres"], default="local", help="SaaS storage adapter reference")
    
    diff_parser = subparsers.add_parser("diff", help="Diff two transactions")
    diff_parser.add_argument("tx1", help="Transaction 1 ID")
    diff_parser.add_argument("tx2", help="Transaction 2 ID")
    diff_parser.add_argument("--storage", choices=["local", "postgres"], default="local", help="SaaS storage adapter reference")
    
    args = parser.parse_args()
    
    def get_storage(storage_args):
        if storage_args == "postgres":
            return PostgresStorageAdapter()
        return LocalStorageAdapter("/tmp/determinai_example")
    
    if args.command == "init":
        os.makedirs(".determinai", exist_ok=True)
        print("DeterminAI runtime environment initialized in .determinai/")
        
    elif args.command == "run":
        # Export chosen LLM via environment for the script to hook onto
        os.environ["DETERMINAI_LLM_ADAPTER"] = args.llm
        print(f"Running DeterminAI script: {args.script_path} via {args.llm} adapter...")
        
        spec = spec_from_file_location("workflow_module", args.script_path)
        module = module_from_spec(spec)
        sys.modules["workflow_module"] = module
        spec.loader.exec_module(module)
        
        if hasattr(module, "run_workflow"):
             module.run_workflow()
        else:
             print("Error: Target script must define a global 'run_workflow()' method.")
        
    elif args.command == "replay":
        storage = get_storage(args.storage)
        engine = AITransactionEngine(MemoryStore(SnapshotEngine(storage)), EventLog(storage))
        print(f"Replaying {args.transaction_id} from {args.storage}...")
        try:
            res = engine.replay(args.transaction_id)
            print(json.dumps(res, indent=2))
        except Exception as e:
            print(f"Failed to replay: {e}")
            
    elif args.command == "diff":
        storage = get_storage(args.storage)
        engine = AITransactionEngine(MemoryStore(SnapshotEngine(storage)), EventLog(storage))
        try:
            diff = engine.diff(args.tx1, args.tx2)
            print(json.dumps(diff, indent=2))
        except Exception as e:
            print(f"Failed to diff: {e}")
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
