import {
    AITransactionEngine,
    DeterministicExecutionGraph,
    ToolAdapter,
    getLLMAdapter,
    LocalStorageAdapter,
    MemoryStore,
    SnapshotEngine,
    EventLog,
    logger
} from '../../sdk/typescript/src/index';

const OutputSchema = {
    type: "object",
    properties: {
        risk_level: { type: "string" },
        issues: { type: "string" }
    },
    required: ["risk_level", "issues"]
};

// Mock Database Fetcher
async function fetchFinancialHistory(params: Record<string, any>) {
    if (params.doc_id === "D-991") {
        return { document: "Party A indemnifies Party B against all third-party claims arising out of this Agreement." };
    }
    return { document: "" };
}

async function run_workflow() {
    logger.info("--- [DeterminAI] Building Execution Graph ---");

    const graph = new DeterministicExecutionGraph("LegalWorkflow_TS", "1.0");

    const recordTool = new ToolAdapter(
        "LegalDB",
        "Fetches legal history internally.",
        { doc_id: "string" },
        { document: "string" },
        fetchFinancialHistory
    );

    graph.addTool(recordTool);
    graph.setLLM(getLLMAdapter(), OutputSchema);
    graph.compile();

    const storage = new LocalStorageAdapter('/tmp/determinai_ts_examples_legal');
    const memory = new MemoryStore(new SnapshotEngine(storage));
    const engine = new AITransactionEngine(memory, new EventLog(storage));

    logger.info("--- [DeterminAI] Beginning AI Transaction ---");
    const payload = { doc_id: "D-991", focus: "Indemnification" };
    const tx = await engine.begin(graph, payload, "v1", {});

    logger.info("--- [DeterminAI] Committing Transaction ---");
    const txId = await engine.commit(tx);
    console.log(`Final Output:`, JSON.stringify(tx.output_payload, null, 2));

    logger.info("--- [DeterminAI] Replaying Transaction ---");
    const replayRes = await engine.replay(txId);
    console.log(`Replayed exactly matched:`, replayRes.deterministic_match);

    logger.info("--- Testing Diff ---");
    const diffs = await engine.diff(txId, txId);
    console.log("Diff ok:", diffs);
}

if (require.main === module) {
    run_workflow().catch(console.error);
}
