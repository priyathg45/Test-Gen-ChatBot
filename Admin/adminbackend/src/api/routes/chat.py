"""Chat management routes for admin."""
import logging
from flask import Blueprint, request, jsonify

from src.config import Config
from src.utils.mongo import get_collection
from .auth import verify_token

logger = logging.getLogger(__name__)

chat_bp = Blueprint('chat', __name__)

def check_admin_auth():
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        return False
    token = auth_header.split(" ")[1]
    return verify_token(token) is not None

@chat_bp.route('/history/<user_identifier>', methods=['GET'])
def get_user_chat_history(user_identifier):
    """Get chat history for a specific user (either username or user_id)."""
    if not check_admin_auth():
        return jsonify({"error": "Unauthorized"}), 401

    try:
        chat_col = get_collection(Config.MONGO_URI, Config.MONGO_DB, "chat_history")
        if chat_col is None:
            return jsonify({"error": "Database error"}), 500

        # Attempt to get history by user_id first, fallback to username structure depending on how main app saves it
        history = list(chat_col.find({"user_id": user_identifier}).sort("timestamp", -1))
        
        # If the backend saves it as 'session_id' matching the username
        if not history:
            history = list(chat_col.find({"session_id": user_identifier}).sort("timestamp", -1))
            
        for msg in history:
            msg["_id"] = str(msg["_id"])
            if "timestamp" in msg:
                msg["timestamp"] = msg["timestamp"].isoformat()
            
        return jsonify({"history": history}), 200

    except Exception as e:
        logger.error(f"Error fetching chat history: {str(e)}")
        return jsonify({"error": "Failed to fetch chat history"}), 500
