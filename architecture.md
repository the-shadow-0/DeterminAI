# DeterminAI Runtime Architecture

DeterminAI operates as an immutable, event-sourced, fully deterministic execution environment for AI. Think about it like "Kubernetes for AI Execution".

## Core Principles
1. **Event Sourcing > Mutation**: AI operations are recorded as append-only states.
2. **Determinism > Convenience**: Everything is strictly versioned and deterministic. Replay guarantees matching outcomes.
3. **Graph Compilation**: Validation of schemas (via Pydantic/Zod constraints) occurs before execution begins.

## Key Layers
- **Core Engine (`/core`)**: Implements `AITransactionEngine`. Has strong semantic boundaries: `begin()`, `validate()`, `commit()`, and `rollback()`.
- **Memory Versioning (`/memory`)**: Pluggable architecture exposing `SnapshotEngine` for constant-time content-addressed lookups of states. Branches and rollbacks supported via memory references.
- **Storage Layer (`/storage`)**: Storage-agnostic plugin architecture managing the Event Logs mapping UUID transactions.
- **Tool Defenses (`/tools`)**: Deterministic bounds with circuit breakers and mocking injection for replays.

## Technical Implementations
- Python handles the core synchronous graph execution and heavy computations.
- Node TS mappings interface tightly with Pydantic JSON Schemas via the `zod` module for strict cross-language typing.
