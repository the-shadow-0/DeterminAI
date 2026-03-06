from fastapi import Request, HTTPException, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import os
from core.logger import logger

security = HTTPBearer()

def get_current_user_role(credentials: HTTPAuthorizationCredentials = Security(security)):
    """Validates the bearer token providing rudimentary Enterprise RBAC"""
    token = credentials.credentials
    admin_token = os.environ.get("DETERMINAI_ADMIN_TOKEN", "mock-admin-token")
    auditor_token = os.environ.get("DETERMINAI_AUDITOR_TOKEN", "mock-auditor-token")
    
    if token == admin_token:
        return "admin"
    elif token == auditor_token:
        return "auditor"
        
    logger.warn("RBAC failed: Unauthorized access attempt")
    raise HTTPException(status_code=403, detail="Unauthorized")

def verify_admin_access(role: str = Security(get_current_user_role)):
    if role != "admin":
        raise HTTPException(status_code=403, detail="Admin role required to trigger mutations or replays.")
    return True
