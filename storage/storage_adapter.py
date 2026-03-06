from abc import ABC, abstractmethod
from typing import Dict, Any
import json
import os
from core.logger import logger

class StorageAdapter(ABC):
    @abstractmethod
    def save(self, key: str, data: Dict[str, Any]):
        pass
        
    @abstractmethod
    def load(self, key: str) -> Dict[str, Any]:
        pass

class LocalStorageAdapter(StorageAdapter):
    def __init__(self, root_dir: str = "/tmp/determinai"):
        self.root_dir = root_dir
        os.makedirs(self.root_dir, exist_ok=True)
        
    def save(self, key: str, data: Dict[str, Any]):
        with open(f"{self.root_dir}/{key}.json", "w") as f:
            json.dump(data, f)
            
    def load(self, key: str) -> Dict[str, Any]:
        try:
            with open(f"{self.root_dir}/{key}.json", "r") as f:
                return json.load(f)
        except OSError:
            return None

class PostgresStorageAdapter(StorageAdapter):
    """SaaS backend persistent storage wrapper."""
    def __init__(self, connection_uri: str = None):
        if not connection_uri:
            connection_uri = os.environ.get("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/determinai")
        self.connection_uri = connection_uri
        
        from storage.encryption import AESEncryptor
        self.encryptor = AESEncryptor()
        
        self._init_db()
        
    def _get_connection(self):
        import psycopg2
        return psycopg2.connect(self.connection_uri)

    def _init_db(self):
        logger.info("Initialized Postgres connection pool", uri=self.connection_uri.split("@")[-1])
        
    def save(self, key: str, data: Dict[str, Any]):
        try:
            encrypted_data = self.encryptor.encrypt(data)
            import psycopg2
            from psycopg2.extras import Json
            with self._get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute("""
                        INSERT INTO event_state (key, data) 
                        VALUES (%s, %s)
                        ON CONFLICT (key) DO UPDATE SET data = EXCLUDED.data, updated_at = CURRENT_TIMESTAMP;
                    """, (key, Json(encrypted_data)))
                conn.commit()
            logger.debug("PG: UPSERT INTO event_state", key=key)
        except Exception as e:
            logger.error("Failed to save to Postgres, falling back to local file", error=str(e))
            # Fallback to tmp file for resilience
            with open(f"/tmp/determinai_pg_mock_{key}.json", "w") as f:
                 json.dump(self.encryptor.encrypt(data), f)
             
    def load(self, key: str) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute("SELECT data FROM event_state WHERE key = %s;", (key,))
                    result = cursor.fetchone()
                    if result:
                        logger.debug("PG: SELECT FROM event_state OK", key=key)
                        return self.encryptor.decrypt(result[0])
        except Exception as e:
            logger.error("Failed to load from Postgres, checking local fallback", error=str(e))
        
        # Load fallback if missing or DB failed
        try:
             with open(f"/tmp/determinai_pg_mock_{key}.json", "r") as f:
                 return self.encryptor.decrypt(json.load(f))
        except OSError:
             return None
