# DeterminAI Runtime

DeterminAI Runtime is a deterministic transactional execution runtime for non-deterministic AI systems.
It functions as an immutable, event-sourced execution engine, analogous to a database transaction log for AI pipelines.

## Project Structure
- **/core**: Atomic execution model, graph validation, schemas.
- **/memory**: Snapshot hashing and state branching.
- **/storage**: Event sourcing adapters (local/PostgreSQL logic).
- **/tools**: Record/replay isolation wrappers.
- **/sdk**: Language bindings (Python & TypeScript/Zod).
- **/examples**: Reference implementation logic.

## Setup
```bash
pip install -r requirements.txt
```

## Running the Architecture Example
The codebase ships with a working Enterprise Risk Workflow evaluating a mock loan payload through an abstract "DeterminAI Execution Graph" (DEG).

```bash
python examples/enterprise_workflow.py
```

## Using the CLI
Verify and explore past runs using the event sourcing APIs:
```bash
python cli.py --help
```
