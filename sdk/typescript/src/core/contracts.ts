import { z } from 'zod';

// Core structural boundaries identical to Python's Pydantic `contracts.py`

export const ToolCallSchema = z.object({
    tool_name: z.string(),
    inputs: z.record(z.any()),
    outputs: z.record(z.any()).nullable(),
    error: z.string().nullable().optional(),
    timestamp: z.number(),
});
export type ToolCall = z.infer<typeof ToolCallSchema>;

export const SnapshotSchema = z.object({
    snapshot_hash: z.string(),
    parent_hash: z.string().nullable(),
    data: z.record(z.any()),
    timestamp: z.number(),
});
export type Snapshot = z.infer<typeof SnapshotSchema>;

export const TransactionSchema = z.object({
    transaction_id: z.string().uuid(),
    graph_hash: z.string(),
    model_versions: z.record(z.string()),
    prompt_version: z.string(),
    input_payload: z.record(z.any()),
    memory_snapshot_reference: z.string(),
    tool_call_graph: z.array(ToolCallSchema),
    output_payload: z.record(z.any()).nullable(),
    state_delta: z.record(z.any()).nullable(),
    commit_status: z.enum(['PENDING', 'COMMITTED', 'ROLLED_BACK']),
    timestamp: z.number(),
});
export type Transaction = z.infer<typeof TransactionSchema>;

export const GraphCompiledSchema = z.object({
    graph_name: z.string(),
    version: z.string(),
    nodes: z.array(z.string()),
    edges: z.array(z.tuple([z.string(), z.string()])),
    compiled_hash: z.string(),
    timestamp: z.number()
});
export type GraphCompiled = z.infer<typeof GraphCompiledSchema>;
