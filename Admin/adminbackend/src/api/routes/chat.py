"""Chat management routes for admin — reading from history and sessions collections."""
import logging
from flask import Blueprint, request, jsonify
from bson import ObjectId

from src.config import Config
from src.utils.mongo import get_collection
from .auth import verify_token

logger = logging.getLogger(__name__)

chat_bp = Blueprint('chat', __name__)


def check_admin_auth():
    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        return False
    token = auth_header.split(" ", 1)[1]
    return verify_token(token) is not None


def _col(name):
    return get_collection(Config.MONGO_URI, Config.MONGO_DB, name)


@chat_bp.route('/user/<user_id>/sessions', methods=['GET'])
def get_user_sessions(user_id):
    """List all chat sessions for a specific user ID."""
    if not check_admin_auth():
        return jsonify({"error": "Unauthorized"}), 401
    try:
        coll = _col("sessions")
        # Structure often uses 'user_id' as a string or ObjectId depending on auth.py
        sessions = list(coll.find({
            "$or": [
                {"user_id": user_id},
                {"user_id": ObjectId(user_id) if ObjectId.is_valid(user_id) else None}
            ]
        }).sort("started_at", -1))
        
        for sess in sessions:
            sess["_id"] = str(sess["_id"])
        return jsonify({"success": True, "sessions": sessions}), 200
    except Exception as e:
        logger.error("get_user_sessions error: %s", e)
        return jsonify({"error": str(e)}), 500


@chat_bp.route('/session/<session_id>/messages', methods=['GET'])
def get_session_messages(session_id):
    """Get all messages for a specific session ID."""
    if not check_admin_auth():
        return jsonify({"error": "Unauthorized"}), 401
    try:
        coll = _col("history")
        messages = list(coll.find({"session_id": session_id}).sort("timestamp", 1))
        for msg in messages:
            msg["_id"] = str(msg["_id"])
            if "timestamp" in msg and hasattr(msg["timestamp"], "isoformat"):
                msg["timestamp"] = msg["timestamp"].isoformat()
        return jsonify({"success": True, "messages": messages}), 200
    except Exception as e:
        logger.error("get_session_messages error: %s", e)
        return jsonify({"error": str(e)}), 500


@chat_bp.route('/history/<user_identifier>', methods=['GET'])
def get_user_chat_history(user_identifier):
    """Get flat chat history for a specific user (fallback for simple views)."""
    if not check_admin_auth():
        return jsonify({"error": "Unauthorized"}), 401
    try:
        coll = _col("history")
        # Try finding by user_id OR session_id (if session_id is just username)
        history = list(coll.find({
            "$or": [
                {"user_id": user_identifier},
                {"user_id": ObjectId(user_identifier) if ObjectId.is_valid(user_identifier) else None},
                {"session_id": user_identifier}
            ]
        }).sort("timestamp", -1))
        
        for msg in history:
            msg["_id"] = str(msg["_id"])
            if "timestamp" in msg and hasattr(msg["timestamp"], "isoformat"):
                msg["timestamp"] = msg["timestamp"].isoformat()
            
        return jsonify({"history": history}), 200
    except Exception as e:
        logger.error("get_user_chat_history error: %s", e)
        return jsonify({"error": str(e)}), 500
