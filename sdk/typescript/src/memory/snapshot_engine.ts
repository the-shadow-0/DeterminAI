import { createHash } from 'crypto';
import { StorageAdapter } from '../storage/adapters';
import { logger } from '../core/logger';

export class SnapshotEngine {
    private storage: StorageAdapter;

    constructor(storage: StorageAdapter) {
        this.storage = storage;
    }

    private hashDict(data: Record<string, any>): string {
        const sorted = JSON.stringify(data, Object.keys(data).sort());
        return createHash('sha256').update(sorted).digest('hex');
    }

    async saveSnapshot(data: Record<string, any>, parentHash: string | null = null): Promise<string> {
        const snapshotHash = this.hashDict(data);
        const payload = {
            snapshot_hash: snapshotHash,
            parent_hash: parentHash,
            data: data,
            timestamp: Date.now() / 1000.0
        };
        await this.storage.save(`snap_${snapshotHash}`, payload);
        logger.info('Snapshot saved to storage', { snapshot_hash: snapshotHash });
        return snapshotHash;
    }

    async loadSnapshot(snapshotHash: string): Promise<Record<string, any>> {
        const snap = await this.storage.load(`snap_${snapshotHash}`);
        if (!snap) throw new Error(`Snapshot not found: ${snapshotHash}`);
        return snap.data;
    }
}
