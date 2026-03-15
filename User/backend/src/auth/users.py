"""User model and MongoDB operations."""
import logging
from typing import Optional, Dict, Any, List
from bson import ObjectId

logger = logging.getLogger(__name__)

# Role constants
ROLE_USER = 'user'
ROLE_ADMIN = 'admin'


def get_users_collection(db):
    """Return the users collection from the given database."""
    if db is None:
        return None
    return db['users']  # collection name from config is applied when calling from app


def _serialize_user(doc: Optional[Dict]) -> Optional[Dict]:
    """Convert MongoDB user document to JSON-serializable dict (no password hash)."""
    if doc is None:
        return None
    out = {
        'id': str(doc['_id']),
        'email': doc.get('email'),
        'full_name': doc.get('full_name', ''),
        'role': doc.get('role', ROLE_USER),
        'created_at': doc.get('created_at'),
        'updated_at': doc.get('updated_at'),
    }
    return out


def create_user(
    users_coll,
    email: str,
    password_hash: str,
    full_name: str = '',
    role: str = ROLE_USER,
) -> Optional[Dict]:
    """Create a new user. Returns serialized user or None if email exists."""
    if users_coll is None:
        return None
    from datetime import datetime
    now = datetime.utcnow().isoformat() + 'Z'
    existing = users_coll.find_one({'email': email.lower().strip()})
    if existing:
        return None
    doc = {
        'email': email.lower().strip(),
        'password_hash': password_hash,
        'full_name': (full_name or '').strip(),
        'role': role if role in (ROLE_USER, ROLE_ADMIN) else ROLE_USER,
        'created_at': now,
        'updated_at': now,
    }
    result = users_coll.insert_one(doc)
    doc['_id'] = result.inserted_id
    return _serialize_user(doc)


def find_user_by_email(users_coll, email: str) -> Optional[Dict]:
    """Find user by email. Returns raw document (includes password_hash)."""
    if users_coll is None:
        return None
    return users_coll.find_one({'email': email.lower().strip()})


def find_user_by_id(users_coll, user_id: str) -> Optional[Dict]:
    """Find user by id. Returns raw document."""
    if users_coll is None:
        return None
    try:
        oid = ObjectId(user_id)
    except Exception:
        return None
    return users_coll.find_one({'_id': oid})


def list_users(users_coll, skip: int = 0, limit: int = 100) -> List[Dict]:
    """List users (no password). For admin."""
    if users_coll is None:
        return []
    cursor = users_coll.find({}).sort('created_at', -1).skip(skip).limit(limit)
    return [_serialize_user(d) for d in cursor]


def update_user_profile(
    users_coll,
    user_id: str,
    full_name: Optional[str] = None,
) -> bool:
    """Update user profile (e.g. full_name). Returns True if updated."""
    if users_coll is None:
        return False
    try:
        oid = ObjectId(user_id)
    except Exception:
        return False
    from datetime import datetime
    updates = {'updated_at': datetime.utcnow().isoformat() + 'Z'}
    if full_name is not None:
        updates['full_name'] = full_name.strip()
    if len(updates) <= 1:
        return True
    result = users_coll.update_one({'_id': oid}, {'$set': updates})
    return result.modified_count > 0


def set_user_role(users_coll, user_id: str, role: str) -> bool:
    """Set user role (admin only). role in ('user', 'admin')."""
    if users_coll is None:
        return False
    if role not in (ROLE_USER, ROLE_ADMIN):
        return False
    try:
        oid = ObjectId(user_id)
    except Exception:
        return False
    from datetime import datetime
    result = users_coll.update_one(
        {'_id': oid},
        {'$set': {'role': role, 'updated_at': datetime.utcnow().isoformat() + 'Z'}},
    )
    return result.modified_count > 0
