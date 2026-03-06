import { logger } from '../core/logger';

export abstract class LLMAdapter {
    abstract generate(prompt: string, schema: any): Promise<any>;
}

export class MockLLMAdapter extends LLMAdapter {
    async generate(prompt: string, schema: any): Promise<any> {
        logger.info('Using fallback mock LLM adapter for deterministic tests.');
        // Mocks structured output for local tests
        const res: Record<string, any> = {};
        if (schema?.properties) {
            for (const [key, val] of Object.entries(schema.properties)) {
                res[key] = `MOCK_${key.toUpperCase()}`;
            }
        }
        return res;
    }
}

export class OllamaAdapter extends LLMAdapter {
    private model: string;
    private endpoint: string;

    constructor(model: string = 'mistral', endpoint: string = 'http://localhost:11434/api/generate') {
        super();
        this.model = model;
        this.endpoint = endpoint;
    }

    async generate(prompt: string, schema: any): Promise<any> {
        logger.info(`Ollama adapter generating with model: ${this.model}`);

        try {
            const resp = await fetch(this.endpoint, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    model: this.model,
                    prompt: prompt,
                    format: 'json',
                    stream: false,
                    system: `You must output strictly matching this JSON schema: ${JSON.stringify(schema)}`
                })
            });

            if (!resp.ok) {
                throw new Error(`Ollama HTTP Error: ${resp.status}`);
            }

            const raw = await resp.json();
            return JSON.parse(raw.response);

        } catch (e) {
            logger.error('Failed to connect to Ollama. Ensure Ollama is running.', { error: e });
            logger.info('Falling back to mock logic.');
            return new MockLLMAdapter().generate(prompt, schema);
        }
    }
}

export class OpenAIAdapter extends LLMAdapter {
    private model: string;
    private apiKey: string | undefined;

    constructor(model: string = 'gpt-4o') {
        super();
        this.model = model;
        this.apiKey = process.env.OPENAI_API_KEY;
    }

    async generate(prompt: string, schema: any): Promise<any> {
        if (!this.apiKey) {
            logger.error('OPENAI_API_KEY is not set. Falling back to Mock.');
            return new MockLLMAdapter().generate(prompt, schema);
        }

        try {
            const resp = await fetch('https://api.openai.com/v1/chat/completions', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${this.apiKey}`
                },
                body: JSON.stringify({
                    model: this.model,
                    messages: [
                        {
                            role: 'system',
                            content: `You are a strict data formatter. Output exact JSON matching this schema: ${JSON.stringify(schema)}`
                        },
                        {
                            role: 'user',
                            content: prompt
                        }
                    ],
                    response_format: { type: 'json_object' }
                })
            });

            if (!resp.ok) {
                throw new Error(`OpenAI HTTP Error: ${resp.status}`);
            }

            const raw = await resp.json();
            return JSON.parse(raw.choices[0].message.content);

        } catch (e) {
            logger.error(`OpenAI Request Failed.`, { error: e });
            throw e;
        }
    }
}

export function getLLMAdapter(): LLMAdapter {
    const choice = process.env.DETERMINAI_LLM_ADAPTER || 'mock';
    if (choice === 'ollama') return new OllamaAdapter();
    if (choice === 'gpt5') return new OpenAIAdapter();
    return new MockLLMAdapter();
}
