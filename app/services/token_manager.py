import time
import uuid
import jwt
from typing import Dict, Any

class AuthorizationTokenManager:
    def __init__(self, secret: str, ttl_seconds: int = 300, audience: str = "nova-orchestrator"):
        self.secret = secret
        self.ttl_seconds = ttl_seconds
        self.audience = audience

    def generate_token(self, execution_id: str, action_id: str) -> str:
        now = int(time.time())
        payload = {
            "execution_id": execution_id,
            "action_id": action_id,
            "audience": self.audience,
            "issued_at": now,
            "expires_at": now + self.ttl_seconds,
            "nonce": str(uuid.uuid4())
        }
        token = jwt.encode(payload, self.secret, algorithm="HS256")
        return token

    def verify_token(self, token: str, expected_execution_id: str, expected_action_id: str) -> Dict[str, Any]:
        try:
            payload = jwt.decode(token, self.secret, algorithms=["HS256"], options={"verify_exp": False})
        except Exception as e:
            raise ValueError(f"Invalid token signature or structure: {str(e)}")

        now = int(time.time())
        if payload.get("expires_at", 0) <= now:
            raise ValueError("Token has expired")

        if payload.get("audience") != self.audience:
            raise ValueError(f"Invalid token audience '{payload.get('audience')}', expected '{self.audience}'")

        if payload.get("execution_id") != expected_execution_id:
            raise ValueError(f"Token execution_id '{payload.get('execution_id')}' mismatch, expected '{expected_execution_id}'")

        if payload.get("action_id") != expected_action_id:
            raise ValueError(f"Token action_id '{payload.get('action_id')}' mismatch, expected '{expected_action_id}'")

        return payload
