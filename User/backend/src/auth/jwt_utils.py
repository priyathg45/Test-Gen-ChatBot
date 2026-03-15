"""JWT creation and verification."""
import jwt
from datetime import datetime, timedelta
from typing import Optional, Dict, Any


def create_access_token(
    user_id: str,
    email: str,
    role: str,
    secret_key: str,
    expires_hours: float = 24,
) -> str:
    """Create a JWT access token."""
    payload = {
        'sub': user_id,
        'email': email,
        'role': role,
        'iat': datetime.utcnow(),
        'exp': datetime.utcnow() + timedelta(hours=expires_hours),
    }
    return jwt.encode(payload, secret_key, algorithm='HS256')


def decode_token(token: str, secret_key: str) -> Optional[Dict[str, Any]]:
    """Decode and verify JWT. Returns payload dict or None if invalid."""
    try:
        payload = jwt.decode(token, secret_key, algorithms=['HS256'])
        return payload
    except Exception:
        return None
