"""Authentication and authorization module."""
from src.auth.users import (
    create_user,
    find_user_by_email,
    find_user_by_id,
    list_users,
    update_user_profile,
    set_user_role,
    ROLE_USER,
    ROLE_ADMIN,
)
from src.auth.password import hash_password, check_password
from src.auth.jwt_utils import create_access_token, decode_token
from src.auth.activity import (
    log_activity,
    get_activity_logs,
    ACTION_LOGIN,
    ACTION_LOGOUT,
    ACTION_CHAT,
    ACTION_REGISTER,
)

__all__ = [
    'create_user',
    'find_user_by_email',
    'find_user_by_id',
    'list_users',
    'update_user_profile',
    'set_user_role',
    'ROLE_USER',
    'ROLE_ADMIN',
    'hash_password',
    'check_password',
    'create_access_token',
    'decode_token',
    'log_activity',
    'get_activity_logs',
]
