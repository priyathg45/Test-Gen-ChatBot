"""Activity logging for monitoring (login, chat, admin actions)."""
import logging
from typing import Optional, List, Dict, Any
from datetime import datetime

logger = logging.getLogger(__name__)

# Action types for filtering
ACTION_LOGIN = 'login'
ACTION_LOGOUT = 'logout'
ACTION_CHAT = 'chat'
ACTION_REGISTER = 'register'
ACTION_VIEW_PROFILE = 'view_profile'
ACTION_ADMIN_VIEW_USERS = 'admin_view_users'
ACTION_ADMIN_VIEW_USER = 'admin_view_user'
ACTION_ADMIN_VIEW_HISTORY = 'admin_view_history'
ACTION_ADMIN_VIEW_LOGS = 'admin_view_logs'
ACTION_ADMIN_UPDATE_USER = 'admin_update_user'


def log_activity(
    logs_coll,
    user_id: Optional[str],
    action: str,
    resource: Optional[str] = None,
    details: Optional[Dict[str, Any]] = None,
    ip: Optional[str] = None,
) -> None:
    """Append one activity log entry."""
    if logs_coll is None:
        return
    try:
        entry = {
            'user_id': user_id,
            'action': action,
            'resource': resource,
            'details': details or {},
            'ip': ip,
            'timestamp': datetime.utcnow().isoformat() + 'Z',
        }
        logs_coll.insert_one(entry)
    except Exception as exc:
        logger.warning("Failed to write activity log: %s", exc)


def get_activity_logs(
    logs_coll,
    user_id: Optional[str] = None,
    action: Optional[str] = None,
    skip: int = 0,
    limit: int = 100,
) -> List[Dict]:
    """Get activity logs, optionally filtered by user_id or action."""
    if logs_coll is None:
        return []
    query = {}
    if user_id is not None:
        query['user_id'] = user_id
    if action is not None:
        query['action'] = action
    cursor = logs_coll.find(query).sort('timestamp', -1).skip(skip).limit(limit)
    return [
        {
            'id': str(doc['_id']),
            'user_id': doc.get('user_id'),
            'action': doc.get('action'),
            'resource': doc.get('resource'),
            'details': doc.get('details', {}),
            'ip': doc.get('ip'),
            'timestamp': doc.get('timestamp'),
        }
        for doc in cursor
    ]
