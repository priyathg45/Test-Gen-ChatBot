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

@logs_bp.route('/', methods=['GET'])
def get_system_logs():
    """Get recent system logs (reads from backend logs dir if available or dummy for now)."""
    if not check_admin_auth():
        return jsonify({"error": "Unauthorized"}), 401
    
    # Ideally, we read from a central logging file like backend/logs/app.log
    # For this implementation, we will mock a few logs or try to read a shared log file if it exists.
    
    logs = []
    # Mocking system logs for now as an example
    logs.append({"timestamp": "2026-03-15T10:00:00", "level": "INFO", "message": "Admin Backend started on port 5001"})
    logs.append({"timestamp": "2026-03-15T10:05:00", "level": "INFO", "message": "MongoDB connection established"})
    logs.append({"timestamp": "2026-03-15T10:15:00", "level": "WARNING", "message": "Failed login attempt for user 'admin' from 192.168.1.5"})
    logs.append({"timestamp": "2026-03-15T10:20:00", "level": "INFO", "message": "Successful login for user 'admin'"})
    logs.append({"timestamp": "2026-03-15T11:00:00", "level": "ERROR", "message": "Missing authorization header on /users endpoint"})

    return jsonify({"logs": logs}), 200
