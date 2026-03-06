import { SnapshotEngine } from './snapshot_engine';
import { logger } from '../core/logger';

export class MemoryStore {
    private engine: SnapshotEngine;
    private state: Record<string, any>;
    private currentHash: string | null;

    constructor(engine: SnapshotEngine) {
        this.engine = engine;
        this.state = {};
        this.currentHash = null;
    }

    async getOrInitializeState(hashOrNull: string | null): Promise<Record<string, any>> {
        if (!hashOrNull) {
            this.state = {};
            this.currentHash = await this.engine.saveSnapshot(this.state);
        } else {
            this.state = await this.engine.loadSnapshot(hashOrNull);
            this.currentHash = hashOrNull;
            logger.info('Restored historical memory state', { snapshot_hash: hashOrNull });
        }
        return this.state;
    }

    async applyDelta(delta: Record<string, any>): Promise<string> {
        this.state = { ...this.state }; // Clone
        for (const key of Object.keys(delta)) {
            this.state[key] = delta[key];
        }
        this.currentHash = await this.engine.saveSnapshot(this.state, this.currentHash);
        logger.info('Applying memory delta', { dict_update_keys: Object.keys(delta) });
        return this.currentHash;
    }

    getCurrentHash(): string | null {
        return this.currentHash;
    }

    getState(): Record<string, any> {
        return { ...this.state };
    }
}
