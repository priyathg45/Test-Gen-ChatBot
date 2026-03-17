"""User management routes for admin."""
import logging
from datetime import datetime, timezone
from bson import ObjectId
from flask import Blueprint, request, jsonify

from src.config import Config
from src.utils.mongo import get_collection
from .auth import verify_token

logger = logging.getLogger(__name__)

users_bp = Blueprint('users', __name__)


def check_admin_auth():
    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        return False
    token = auth_header.split(" ", 1)[1]
    return verify_token(token) is not None


def _users_col():
    return get_collection(Config.MONGO_URI, Config.MONGO_DB, "users")


@users_bp.route('/', methods=['GET'])
def get_users():
    """Get all users."""
    if not check_admin_auth():
        return jsonify({"error": "Unauthorized"}), 401
    try:
        users_col = _users_col()
        if users_col is None:
            return jsonify({"error": "Database error"}), 500
        users = list(users_col.find({}, {"password": 0}).sort("created_at", -1))
        for user in users:
            user["_id"] = str(user["_id"])
            if "is_active" not in user:
                user["is_active"] = True
        return jsonify({"users": users}), 200
    except Exception as e:
        logger.error("Error fetching users: %s", e)
        return jsonify({"error": "Failed to fetch users"}), 500


@users_bp.route('/<user_id>', methods=['GET'])
def get_user(user_id):
    """Get a specific user."""
    if not check_admin_auth():
        return jsonify({"error": "Unauthorized"}), 401
    try:
        users_col = _users_col()
        user = users_col.find_one({"_id": ObjectId(user_id)}, {"password": 0})
        if not user:
            return jsonify({"error": "User not found"}), 404
        user["_id"] = str(user["_id"])
        if "is_active" not in user:
            user["is_active"] = True
        return jsonify({"user": user}), 200
    except Exception as e:
        logger.error("Error fetching user: %s", e)
        return jsonify({"error": "Failed to fetch user"}), 500


@users_bp.route('/<user_id>', methods=['PUT'])
def update_user(user_id):
    """Update user fields."""
    if not check_admin_auth():
        return jsonify({"error": "Unauthorized"}), 401
    try:
        users_col = _users_col()
        data = request.get_json() or {}
        allowed = {"username", "email", "is_active", "role"}
        updates = {k: v for k, v in data.items() if k in allowed}
        if not updates:
            return jsonify({"error": "No valid fields to update"}), 400
        updates["updated_at"] = datetime.now(timezone.utc).isoformat()
        result = users_col.update_one({"_id": ObjectId(user_id)}, {"$set": updates})
        if result.matched_count == 0:
            return jsonify({"error": "User not found"}), 404
        user = users_col.find_one({"_id": ObjectId(user_id)}, {"password": 0})
        user["_id"] = str(user["_id"])
        return jsonify({"success": True, "user": user}), 200
    except Exception as e:
        logger.error("Error updating user: %s", e)
        return jsonify({"error": str(e)}), 500


@users_bp.route('/<user_id>/activate', methods=['PUT'])
def activate_user(user_id):
    """Activate a user account."""
    if not check_admin_auth():
        return jsonify({"error": "Unauthorized"}), 401
    try:
        users_col = _users_col()
        result = users_col.update_one(
            {"_id": ObjectId(user_id)},
            {"$set": {"is_active": True, "updated_at": datetime.now(timezone.utc).isoformat()}}
        )
        if result.matched_count == 0:
            return jsonify({"error": "User not found"}), 404
        return jsonify({"success": True, "message": "User activated"}), 200
    except Exception as e:
        logger.error("Error activating user: %s", e)
        return jsonify({"error": str(e)}), 500


@users_bp.route('/<user_id>/deactivate', methods=['PUT'])
def deactivate_user(user_id):
    """Deactivate a user account."""
    if not check_admin_auth():
        return jsonify({"error": "Unauthorized"}), 401
    try:
        users_col = _users_col()
        result = users_col.update_one(
            {"_id": ObjectId(user_id)},
            {"$set": {"is_active": False, "updated_at": datetime.now(timezone.utc).isoformat()}}
        )
        if result.matched_count == 0:
            return jsonify({"error": "User not found"}), 404
        return jsonify({"success": True, "message": "User deactivated"}), 200
    except Exception as e:
        logger.error("Error deactivating user: %s", e)
        return jsonify({"error": str(e)}), 500


@users_bp.route('/<user_id>', methods=['DELETE'])
def delete_user(user_id):
    """Delete a specific user."""
    if not check_admin_auth():
        return jsonify({"error": "Unauthorized"}), 401
    try:
        users_col = _users_col()
        result = users_col.delete_one({"_id": ObjectId(user_id)})
        if result.deleted_count == 0:
            return jsonify({"error": "User not found"}), 404
        return jsonify({"message": "User deleted successfully"}), 200
    except Exception as e:
        logger.error("Error deleting user: %s", e)
        return jsonify({"error": "Failed to delete user"}), 500


@users_bp.route('/stats', methods=['GET'])
def users_stats():
    """Return user statistics for the dashboard."""
    if not check_admin_auth():
        return jsonify({"error": "Unauthorized"}), 401
    try:
        users_col = _users_col()
        total = users_col.count_documents({})
        active = users_col.count_documents({"is_active": {"$ne": False}})
        inactive = users_col.count_documents({"is_active": False})
        recent = list(users_col.find({}, {"password": 0, "_id": 1, "username": 1, "email": 1, "created_at": 1})
                      .sort("created_at", -1).limit(5))
        for u in recent:
            u["_id"] = str(u["_id"])
        return jsonify({"success": True, "total": total, "active": active, "inactive": inactive, "recent": recent}), 200
    except Exception as e:
        logger.error("Error fetching user stats: %s", e)
        return jsonify({"error": str(e)}), 500
