import os
import json
from base64 import b64encode, b64decode
from typing import Dict, Any, Optional
from cryptography.fernet import Fernet
from cryptography.exceptions import InvalidToken
from core.logger import logger

class AESEncryptor:
    """
    Handles payload encryption at rest using symmetric AES encryption.
    Expects DETERMINAI_ENCRYPTION_KEY to be set in the environment.
    """
    def __init__(self):
        key = os.environ.get("DETERMINAI_ENCRYPTION_KEY")
        self.enabled = bool(key)
        if self.enabled:
            try:
                self.fernet = Fernet(key.encode('utf-8'))
                logger.info("Storage encryption enabled securely.")
            except Exception as e:
                logger.error("Failed to initialize AES encryption.", error=str(e))
                self.enabled = False
        else:
            logger.warn("DETERMINAI_ENCRYPTION_KEY not set. Storing data in plain-text JSONB.")

    def encrypt(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Encrypts a dict into a base64 ciphertext wrapper if enabled."""
        if not self.enabled:
            return payload
            
        raw_json = json.dumps(payload)
        ciphertext = self.fernet.encrypt(raw_json.encode('utf-8'))
        return {"_cipher": b64encode(ciphertext).decode('utf-8')}

    def decrypt(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Decrypts base64 ciphertext back to dict, falling back to plain if unencrypted."""
        if not self.enabled or "_cipher" not in payload:
            return payload
        
        try:
            ciphertext = b64decode(payload["_cipher"].encode('utf-8'))
            raw_json = self.fernet.decrypt(ciphertext).decode('utf-8')
            return json.loads(raw_json)
        except (InvalidToken, ValueError, TypeError) as e:
            logger.error("Failed to decrypt payload. It may be corrupted or encrypted with a different key.", error=str(e))
            raise ValueError("Decryption failed. Data cannot be securely loaded.")
