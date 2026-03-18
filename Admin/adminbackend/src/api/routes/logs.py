"""System logging routes for admin."""
import logging
import os
from flask import Blueprint, jsonify, request

from .auth import verify_token

logger = logging.getLogger(__name__)

logs_bp = Blueprint('logs', __name__)

def check_admin_auth():
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        return False
    token = auth_header.split(" ")[1]
    return verify_token(token) is not None

def log_activity(level, message, user_email="system", source="admin", action=None, details=None):
    """Log an activity to the database."""
    from src.utils.mongo import get_collection
    from src.config import Config
    from datetime import datetime
    
    try:
        logs_col = get_collection(Config.MONGO_URI, Config.MONGO_DB, Config.MONGO_ACTIVITY_LOGS_COLLECTION)
        if logs_col is not None:
            logs_col.insert_one({
                "timestamp": datetime.utcnow().isoformat() + 'Z',
                "source": source,
                "level": level.upper(),
                "action": action or (level.upper() if source == 'admin' else 'activity'),
                "message": message,
                "user_email": user_email,
                "details": details or {}
            })
    except Exception as e:
        logger.error(f"Failed to log activity: {e}")

@logs_bp.route('/', methods=['GET'])
def get_system_logs():
    """Get real activity logs from the database, filtered by source and level."""
    logger.info("Fetching system logs requested")
    if not check_admin_auth():
        return jsonify({"error": "Unauthorized"}), 401
    
    from src.utils.mongo import get_collection
    from src.config import Config
    
    source_filter = request.args.get('source', 'admin').lower()
    level_filter = request.args.get('level', 'ALL').upper()
    search_query = request.args.get('search', '').strip()
    start_date = request.args.get('startDate')
    end_date = request.args.get('endDate')
    limit = int(request.args.get('limit', 100))
    
    logs_col = get_collection(Config.MONGO_URI, Config.MONGO_DB, Config.MONGO_ACTIVITY_LOGS_COLLECTION)
    
    query = {}
    if source_filter != 'all':
        if source_filter == 'admin':
            query['$or'] = [{'source': 'admin'}, {'source': {'$exists': False}}]
        else:
            query['source'] = source_filter

    if level_filter != 'ALL':
        query['level'] = level_filter

    if search_query:
        query['$or'] = [
            {'message': {'$regex': search_query, '$options': 'i'}},
            {'user_email': {'$regex': search_query, '$options': 'i'}},
            {'user_id': {'$regex': search_query, '$options': 'i'}},
            {'action': {'$regex': search_query, '$options': 'i'}}
        ]

    if start_date or end_date:
        query['timestamp'] = {}
        if start_date: query['timestamp']['$gte'] = start_date
        if end_date: query['timestamp']['$lte'] = end_date
        
    try:
        results = list(logs_col.find(query).sort("timestamp", -1).limit(limit))
        
        formatted_logs = []
        for log in results:
            # Map user side fields (action, details) to admin view
            # User side logs might not have 'message' but have 'action'
            msg = log.get("message")
            if not msg:
                action = log.get("action", "activity")
                details = log.get("details", {})
                if action == 'login': msg = f"User logged in from {log.get('ip', 'unknown IP')}"
                elif action == 'chat': msg = f"User started a chat session"
                elif action == 'register': msg = f"New user registered: {details.get('email', 'Unknown')}"
                else: msg = f"Action: {action}"

            formatted_logs.append({
                "id": str(log.get("_id")),
                "timestamp": log.get("timestamp"),
                "source": log.get("source", "admin"),
                "level": log.get("level", "INFO"),
                "action": log.get("action", log.get("level", "INFO")),
                "message": msg,
                "user": log.get("user_email") or log.get("user_id") or "system",
                "details": log.get("details", {})
            })
            
        return jsonify({"logs": formatted_logs}), 200
    except Exception as e:
        logger.error(f"Error fetching logs: {e}")
        return jsonify({"error": "Failed to fetch logs"}), 500

@logs_bp.route('/stats', methods=['GET'])
def get_log_stats():
    """Get log counts by level for the selected source."""
    if not check_admin_auth():
        return jsonify({"error": "Unauthorized"}), 401
        
    from src.utils.mongo import get_collection
    from src.config import Config
    
    source = request.args.get('source', 'admin').lower()
    logs_col = get_collection(Config.MONGO_URI, Config.MONGO_DB, Config.MONGO_ACTIVITY_LOGS_COLLECTION)
    
    query = {}
    if source != 'all':
        if source == 'admin':
            query['$or'] = [{'source': 'admin'}, {'source': {'$exists': False}}]
        else:
            query['source'] = source
            
    try:
        # Aggregation to get counts by level
        pipeline = [
            {'$match': query},
            {'$group': {'_id': '$level', 'count': {'$sum': 1}}}
        ]
        results = list(logs_col.aggregate(pipeline))
        logger.debug(f"Stats raw results: {results}")
        
        stats = {}
        for res in results:
            lvl = res.get('_id')
            if lvl is None:
                lvl = 'UNKNOWN'
            stats[str(lvl)] = res.get('count', 0)
            
        # Ensure common levels are present
        for level in ['INFO', 'WARNING', 'ERROR']:
            if level not in stats: stats[level] = 0
            
        return jsonify(stats), 200
    except Exception as e:
        logger.error(f"Error fetching log stats: {e}", exc_info=True)
        return jsonify({"error": str(e)}), 500

@logs_bp.route('/clear', methods=['DELETE'])
def clear_logs():
    """Clear logs based on source or level."""
    if not check_admin_auth():
        return jsonify({"error": "Unauthorized"}), 401
        
    from src.utils.mongo import get_collection
    from src.config import Config
    
    source = request.args.get('source')
    level = request.args.get('level')
    
    logs_col = get_collection(Config.MONGO_URI, Config.MONGO_DB, Config.MONGO_ACTIVITY_LOGS_COLLECTION)
    
    query = {}
    if source: query['source'] = source
    if level: query['level'] = level
    
    try:
        result = logs_col.delete_many(query)
        log_activity("WARNING", f"Logs cleared by admin. Deleted {result.deleted_count} entries.", user_email="admin")
        return jsonify({"message": f"Successfully deleted {result.deleted_count} logs"}), 200
    except Exception as e:
        logger.error(f"Error clearing logs: {e}")
        return jsonify({"error": "Failed to clear logs"}), 500
