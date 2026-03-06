import { createHash } from 'crypto';
import { logger } from './logger';
import { GraphCompiledSchema } from './contracts';
import { ToolAdapter } from '../tools/tool_adapter';
import { LLMAdapter } from '../llm/adapters';

export class DeterministicExecutionGraph {
    public name: string;
    public version: string;
    private tools: ToolAdapter[];
    private llmAdapter: LLMAdapter | null;
    public outputSchema: any;
    private compiledHash: string | null;
    public compiledData: any | null;

    constructor(name: string, version: string) {
        this.name = name;
        this.version = version;
        this.tools = [];
        this.llmAdapter = null;
        this.outputSchema = null;
        this.compiledHash = null;
        this.compiledData = null;
    }

    addTool(tool: ToolAdapter) {
        this.tools.push(tool);
    }

    setLLM(adapter: LLMAdapter, outputSchema: any) {
        this.llmAdapter = adapter;
        this.outputSchema = outputSchema;
    }

    compile(): string {
        const repr = {
            graph_name: this.name,
            version: this.version,
            nodes: this.tools.map(t => t.name).concat(this.llmAdapter ? ['LLMNode'] : []),
            edges: this.tools.map(t => [t.name, 'LLMNode']), // Simple star topology to LLM
            timestamp: Date.now() / 1000.0
        };
        const sorted = JSON.stringify(repr, Object.keys(repr).sort());
        this.compiledHash = createHash('sha256').update(sorted).digest('hex');

        const payload = GraphCompiledSchema.parse({
            ...repr,
            compiled_hash: this.compiledHash
        });

        this.compiledData = payload;
        logger.info('Compiled execution graph', { graph_name: this.name, hash: this.compiledHash });
        return this.compiledHash;
    }

    getHash(): string {
        if (!this.compiledHash) throw new Error('Graph must be compiled first.');
        return this.compiledHash;
    }

    async run(inputs: Record<string, any>, context: Record<string, any>, llmPromptTemplate: (i: any, c: any, t: any) => string): Promise<{ toolCalls: any[], llmOutput: any }> {
        if (!this.compiledHash) throw new Error('Graph must be compiled.');

        const toolCalls = [];
        const toolOutputs: Record<string, any> = {};

        for (const tool of this.tools) {
            const call = await tool.execute(inputs);
            toolCalls.push(call);
            toolOutputs[tool.name] = call.outputs;
        }

        let llmOutput = null;
        if (this.llmAdapter) {
            const prompt = llmPromptTemplate(inputs, context, toolOutputs);
            llmOutput = await this.llmAdapter.generate(prompt, this.outputSchema);
        }

        return { toolCalls, llmOutput };
    }
}
