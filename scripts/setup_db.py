import psycopg2
from psycopg2.extras import Json
import os
import json
from core.logger import logger

def setup_database():
    """Initializes the DeterminAI Postgres tables."""
    connection_uri = os.environ.get("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/determinai")
    
    logger.info(f"Connecting to database: {connection_uri}")
    try:
        conn = psycopg2.connect(connection_uri)
        conn.autocommit = True
        cursor = conn.cursor()
        
        # Create the main event state table.
        # JSONB allows for strict binary indexing and rapid queries across deeply nested memory snapshot traces.
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS event_state (
                key TEXT PRIMARY KEY,
                data JSONB NOT NULL,
                updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
            );
        """)
        
        # Add index for searching transactions by id or graph hashes inside unstructured JSON
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_event_data ON event_state USING GIN (data);
        """)
        
        logger.info("[✔] Database schema initialized successfully.")
        
    except Exception as e:
        logger.error(f"[X] Failed to setup database: {str(e)}")
        raise

if __name__ == "__main__":
    setup_database()
