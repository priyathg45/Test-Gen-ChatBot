"""User management routes for admin."""
import logging
from bson import ObjectId
from flask import Blueprint, request, jsonify

from src.config import Config
from src.utils.mongo import get_collection
from .auth import verify_token

logger = logging.getLogger(__name__)

users_bp = Blueprint('users', __name__)

def check_admin_auth():
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        return False
    token = auth_header.split(" ")[1]
    return verify_token(token) is not None

@users_bp.route('/', methods=['GET'])
def get_users():
    """Get all users."""
    if not check_admin_auth():
        return jsonify({"error": "Unauthorized"}), 401

    try:
        users_col = get_collection(Config.MONGO_URI, Config.MONGO_DB, "users")
        if users_col is None:
            return jsonify({"error": "Database error"}), 500

        users = list(users_col.find(
            {}, 
            {"password": 0} # Don't return passwords
        ).sort("created_at", -1))
        
        # Convert ObjectId to string
        for user in users:
            user["_id"] = str(user["_id"])
            
        return jsonify({"users": users}), 200

    except Exception as e:
        logger.error(f"Error fetching users: {str(e)}")
        return jsonify({"error": "Failed to fetch users"}), 500

@users_bp.route('/<user_id>', methods=['GET'])
def get_user(user_id):
    """Get a specific user."""
    if not check_admin_auth():
        return jsonify({"error": "Unauthorized"}), 401

    try:
        users_col = get_collection(Config.MONGO_URI, Config.MONGO_DB, "users")
        if users_col is None:
            return jsonify({"error": "Database error"}), 500

        user = users_col.find_one(
            {"_id": ObjectId(user_id)},
            {"password": 0}
        )
        
        if not user:
            return jsonify({"error": "User not found"}), 404
            
        user["_id"] = str(user["_id"])
        return jsonify({"user": user}), 200

    except Exception as e:
        logger.error(f"Error fetching user: {str(e)}")
        return jsonify({"error": "Failed to fetch user"}), 500

@users_bp.route('/<user_id>', methods=['DELETE'])
def delete_user(user_id):
    """Delete a specific user."""
    if not check_admin_auth():
        return jsonify({"error": "Unauthorized"}), 401

    try:
        users_col = get_collection(Config.MONGO_URI, Config.MONGO_DB, "users")
        if users_col is None:
            return jsonify({"error": "Database error"}), 500

        result = users_col.delete_one({"_id": ObjectId(user_id)})
        
        if result.deleted_count == 0:
            return jsonify({"error": "User not found"}), 404
            
        return jsonify({"message": "User deleted successfully"}), 200

    except Exception as e:
        logger.error(f"Error deleting user: {str(e)}")
        return jsonify({"error": "Failed to delete user"}), 500
