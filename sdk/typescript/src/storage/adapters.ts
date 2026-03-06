import * as fs from 'fs';
import * as path from 'path';
import { logger } from '../core/logger';

export abstract class StorageAdapter {
    abstract save(key: string, data: Record<string, any>): Promise<void>;
    abstract load(key: string): Promise<Record<string, any> | null>;
}

export class LocalStorageAdapter extends StorageAdapter {
    private rootDir: string;

    constructor(rootDir: string = '/tmp/determinai') {
        super();
        this.rootDir = rootDir;
        fs.mkdirSync(this.rootDir, { recursive: true });
    }

    async save(key: string, data: Record<string, any>): Promise<void> {
        fs.writeFileSync(path.join(this.rootDir, `${key}.json`), JSON.stringify(data, null, 2));
    }

    async load(key: string): Promise<Record<string, any> | null> {
        try {
            const file = fs.readFileSync(path.join(this.rootDir, `${key}.json`), 'utf-8');
            return JSON.parse(file);
        } catch (e) {
            return null;
        }
    }
}

export class PostgresStorageAdapter extends StorageAdapter {
    private connectionUri: string;
    private pool: any; // pg Pool

    constructor(connectionUri?: string) {
        super();
        this.connectionUri = connectionUri || process.env.DATABASE_URL || 'postgresql://postgres:postgres@localhost:5432/determinai';
        try {
            const { Pool } = require('pg');
            this.pool = new Pool({ connectionString: this.connectionUri });
            logger.info('Initialized Postgres connection pool');
        } catch (e) {
            logger.error('Failed to initialize Postgres pool. Ensure pg is installed.', { error: e });
        }
    }

    async save(key: string, data: Record<string, any>): Promise<void> {
        if (!this.pool) return new LocalStorageAdapter().save(key, data);
        try {
            const query = `
                INSERT INTO event_state (key, data) 
                VALUES ($1, $2)
                ON CONFLICT (key) DO UPDATE SET data = EXCLUDED.data, updated_at = CURRENT_TIMESTAMP;
            `;
            await this.pool.query(query, [key, JSON.stringify(data)]);
            logger.debug('PG: UPSERT INTO event_state', { key });
        } catch (e) {
            logger.error('PG Save failed, falling back', { error: e });
            return new LocalStorageAdapter().save(key, data);
        }
    }

    async load(key: string): Promise<Record<string, any> | null> {
        if (!this.pool) return new LocalStorageAdapter().load(key);
        try {
            const res = await this.pool.query('SELECT data FROM event_state WHERE key = $1', [key]);
            if (res.rows.length > 0) return res.rows[0].data;
        } catch (e) {
            logger.error('PG Load failed, falling back', { error: e });
        }
        return new LocalStorageAdapter().load(key);
    }
}
