import { logger } from '../core/logger';
import { StorageAdapter } from './adapters';
import { Transaction } from '../core/contracts';

export class EventLog {
    private storage: StorageAdapter;

    constructor(storage: StorageAdapter) {
        this.storage = storage;
    }

    async saveTransaction(tx: Transaction): Promise<void> {
        await this.storage.save(`tx_${tx.transaction_id}`, tx);
    }

    async loadTransaction(txId: string): Promise<Transaction | null> {
        return (await this.storage.load(`tx_${txId}`)) as Transaction | null;
    }

    async loadDAG(graphHash: string): Promise<any> {
        return await this.storage.load(`dag_${graphHash}`);
    }

    async saveDAG(graphHash: string, data: any): Promise<void> {
        await this.storage.save(`dag_${graphHash}`, data);
    }
}
