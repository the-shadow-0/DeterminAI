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

import { z } from 'zod';

const PatientRecordSchema = z.object({
    patient_id: z.string()
});

const TriageOutputSchema = {
    type: "object",
    properties: {
        triage_level: { type: "string" },
        recommended_action: { type: "string" }
    },
    required: ["triage_level", "recommended_action"]
};

// Mock Database Fetcher
async function fetchPatientHistory(params: Record<string, any>) {
    if (params.patient_id === "P123") {
        return { history: ["hypertension", "diabetes"], allergies: ["penicillin"] };
    }
    return { history: [], allergies: [] };
}

async function run_workflow() {
    logger.info("--- [DeterminAI] Building Execution Graph ---");

    const graph = new DeterministicExecutionGraph("HealthcareTriage_TS", "1.0");

    const recordTool = new ToolAdapter(
        "PatientRecordSystem",
        "Fetches patient history internally.",
        { patient_id: "string" },
        { history: "array", allergies: "array" },
        fetchPatientHistory
    );

    graph.addTool(recordTool);

    const llm = getLLMAdapter();
    graph.setLLM(llm, TriageOutputSchema);

    graph.compile();

    const storage = new LocalStorageAdapter('/tmp/determinai_ts_examples');
    const memory = new MemoryStore(new SnapshotEngine(storage));
    const engine = new AITransactionEngine(memory, new EventLog(storage));

    logger.info("--- [DeterminAI] Beginning AI Transaction ---");

    const payload = { symptoms: ["chest pain", "shortness of breath"], patient_id: "P123" };

    const tx = await engine.begin(graph, payload, "v1", { active_alert: true });

    logger.info("--- [DeterminAI] Committing Transaction ---");
    const txId = await engine.commit(tx);

    console.log(`Final Output:`, JSON.stringify(tx.output_payload, null, 2));

    logger.info("--- [DeterminAI] Replaying Transaction ---");
    const replayRes = await engine.replay(txId);
    console.log(`Replayed exactly matched:`, replayRes.deterministic_match);

    logger.info("--- Testing Diff ---");
    const diffs = await engine.diff(txId, txId);
    console.log("Diff ok:", diffs);

    logger.info("--- Testing Rollback Edge Case ---");
    const brokenTx = await engine.begin(graph, { broken: true }, "v1", {});
    await engine.rollback(brokenTx);
}

if (require.main === module) {
    run_workflow().catch(console.error);
}
