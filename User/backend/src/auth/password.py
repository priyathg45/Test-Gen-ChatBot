"""Password hashing with bcrypt."""
import bcrypt


def hash_password(password: str) -> str:
    """Hash a password. Returns bcrypt hash as string."""
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')


def check_password(password: str, password_hash: str) -> bool:
    """Verify password against stored hash."""
    try:
        return bcrypt.checkpw(password.encode('utf-8'), password_hash.encode('utf-8'))
    except Exception:
        return False
