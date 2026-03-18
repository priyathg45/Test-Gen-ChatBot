import logging
import io
from flask import Blueprint, request, jsonify, send_file
from bson import ObjectId
from datetime import datetime
from gridfs import GridFS
from pymongo import MongoClient

from src.config import Config
from src.utils.mongo import get_collection, get_mongo_client
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


def _get_fs():
    """Return GridFS instance using singleton client."""
    client = get_mongo_client(Config.MONGO_URI)
    if not client:
        raise Exception("Failed to connect to MongoDB")
    db = client[Config.MONGO_DB]
    return GridFS(db, "attachments")


@chat_bp.route('/user/<user_id>/sessions', methods=['GET'])
def get_user_sessions(user_id):
    """List all chat sessions for a specific user ID by aggregating history."""
    if not check_admin_auth():
        return jsonify({"error": "Unauthorized"}), 401
    try:
        coll = _col("history")
        
        # Aggregate history to find unique session_ids for this user
        pipeline = [
            {"$match": {
                "$or": [
                    {"user_id": user_id},
                    {"user_id": ObjectId(user_id) if ObjectId.is_valid(user_id) else None}
                ]
            }},
            {"$sort": {"timestamp": 1}},
            {"$group": {
                "_id": "$session_id",
                "first_msg": {"$first": "$content"},
                "started_at": {"$first": "$timestamp"},
                "last_msg_at": {"$last": "$timestamp"},
                "message_count": {"$sum": 1}
            }},
            {"$sort": {"last_msg_at": -1}}
        ]
        
        cursor = coll.aggregate(pipeline)
        sessions = []
        for doc in cursor:
            sessions.append({
                "_id": doc["_id"], # session_id acts as the ID here
                "session_id": doc["_id"],
                "title": (doc["first_msg"][:50] + "...") if doc["first_msg"] else "Untitled Session",
                "started_at": doc["started_at"],
                "last_message_at": doc["last_msg_at"],
                "message_count": doc["message_count"]
            })
            
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
            # Ensure timestamp is ISO string
            if "timestamp" in msg and hasattr(msg["timestamp"], "isoformat"):
                msg["timestamp"] = msg["timestamp"].isoformat()
        return jsonify({"success": True, "messages": messages}), 200
    except Exception as e:
        logger.error("get_session_messages error: %s", e)
        return jsonify({"error": str(e)}), 500


@chat_bp.route('/session/<session_id>/attachments', methods=['GET'])
def get_session_attachments(session_id):
    """List all attachments for a specific session ID."""
    if not check_admin_auth():
        return jsonify({"error": "Unauthorized"}), 401
    try:
        coll = _col("chat_attachments") # The collection name is chat_attachments as per User backend
        attachments = list(coll.find({"session_id": session_id}).sort("created_at", 1))
        for att in attachments:
            att["_id"] = str(att["_id"])
            att["file_id"] = str(att["file_id"])
        return jsonify({"success": True, "attachments": attachments}), 200
    except Exception as e:
        logger.error("get_session_attachments error: %s", e)
        return jsonify({"error": str(e)}), 500


@chat_bp.route('/attachment/<attachment_id>/download', methods=['GET'])
def download_attachment(attachment_id):
    """Download a specific attachment from GridFS."""
    if not check_admin_auth():
        return jsonify({"error": "Unauthorized"}), 401
    try:
        coll = _col("chat_attachments")
        att = coll.find_one({"_id": ObjectId(attachment_id)})
        if not att:
            logger.error(f"Attachment record {attachment_id} not found in collection")
            return jsonify({"error": "Attachment not found"}), 404
        
        fs = _get_fs()
        file_id = att.get("file_id")
        if not file_id:
            logger.error("File ID missing in attachment record")
            return jsonify({"error": "File ID missing"}), 404
            
        # Ensure file_id is an ObjectId for GridFS.get()
        if isinstance(file_id, str):
            file_id = ObjectId(file_id)
            
        grid_out = fs.get(file_id)
        return send_file(
            io.BytesIO(grid_out.read()),
            mimetype=att.get("content_type", "application/octet-stream"),
            as_attachment=True,
            download_name=att.get("filename", "download")
        )
    except Exception as e:
        logger.error("download_attachment error: %s", e)
        return jsonify({"error": f"Internal server error: {str(e)}"}), 500


@chat_bp.route('/history/<user_identifier>', methods=['GET'])
def get_user_chat_history(user_identifier):
    """Fallback route for flat history."""
    if not check_admin_auth():
        return jsonify({"error": "Unauthorized"}), 401
    try:
        coll = _col("history")
        historyList = list(coll.find({
            "$or": [
                {"user_id": user_identifier},
                {"user_id": ObjectId(user_identifier) if ObjectId.is_valid(user_identifier) else None},
                {"session_id": user_identifier}
            ]
        }).sort("timestamp", -1))
        
        for msg in historyList:
            msg["_id"] = str(msg["_id"])
            if "timestamp" in msg and hasattr(msg["timestamp"], "isoformat"):
                msg["timestamp"] = msg["timestamp"].isoformat()
            
        return jsonify({"history": historyList}), 200
    except Exception as e:
        logger.error("get_user_chat_history error: %s", e)
        return jsonify({"error": str(e)}), 500
