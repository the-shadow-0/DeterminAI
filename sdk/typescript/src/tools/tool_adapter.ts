import { logger } from '../core/logger';
import { ToolCall } from '../core/contracts';

export class ToolAdapter {
    public name: string;
    public description: string;
    public inputSchema: Record<string, any>;
    public outputSchema: Record<string, any>;
    private handler: (params: Record<string, any>) => Promise<Record<string, any>>;
    private maxRetries: number;

    constructor(
        name: string,
        description: string,
        inputSchema: Record<string, any>,
        outputSchema: Record<string, any>,
        handler: (params: Record<string, any>) => Promise<Record<string, any>>,
        maxRetries: number = 3
    ) {
        this.name = name;
        this.description = description;
        this.inputSchema = inputSchema;
        this.outputSchema = outputSchema;
        this.handler = handler;
        this.maxRetries = maxRetries;
    }

    async execute(params: Record<string, any>): Promise<ToolCall> {
        const startTime = Date.now();
        logger.info(`Executing tool: ${this.name}`, { payload: params });

        let attempts = 0;
        while (attempts < this.maxRetries) {
            try {
                const result = await Promise.race([
                    this.handler(params),
                    new Promise((_, reject) => setTimeout(() => reject(new Error('Tool timeout')), 10000))
                ]) as Record<string, any>;

                logger.info(`Tool ${this.name} executed successfully`);
                return {
                    tool_name: this.name,
                    inputs: params,
                    outputs: result,
                    timestamp: Date.now() / 1000.0,
                    error: null
                };
            } catch (e: any) {
                attempts++;
                logger.error(`Tool Execution Failed (Attempt ${attempts}/${this.maxRetries}): ${e.message}`);
                if (attempts >= this.maxRetries) {
                    return {
                        tool_name: this.name,
                        inputs: params,
                        outputs: null,
                        timestamp: Date.now() / 1000.0,
                        error: e.message
                    };
                }
                await new Promise(res => setTimeout(res, Math.pow(2, attempts) * 1000));
            }
        }
        throw new Error('Unreachable state in ToolAdapter retries.');
    }
}
