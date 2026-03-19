"""Health check routes for the admin backend."""
import logging
import urllib.request
import json
from flask import Blueprint, jsonify
from src.config import Config
from src.utils.mongo import get_mongo_client

logger = logging.getLogger(__name__)
health_bp = Blueprint('health', __name__)

@health_bp.route('/', methods=['GET'])
def health_check():
    """Verify connectivity to all backend dependencies."""
    status = {
        "overall": "healthy",
        "mongodb": "unknown",
        "ollama": "unknown",
        "api": "operational"
    }

    # Check MongoDB
    try:
        client = get_mongo_client(Config.MONGO_URI)
        if client:
            # The is_master command is cheap and checks connectivity
            client.admin.command('ismaster')
            status["mongodb"] = "connected"
        else:
            status["mongodb"] = "failed"
            status["overall"] = "degraded"
    except Exception as e:
        logger.error(f"Health check MongoDB error: {e}")
        status["mongodb"] = "error"
        status["overall"] = "degraded"

    # Check Ollama
    try:
        ollama_base = Config.OLLAMA_BASE_URL.rstrip('/')
        req = urllib.request.Request(f"{ollama_base}/api/tags", method="GET")
        with urllib.request.urlopen(req, timeout=2) as resp:
            if resp.status == 200:
                status["ollama"] = "online"
            else:
                status["ollama"] = f"offline (status {resp.status})"
                status["overall"] = "degraded"
    except Exception:
        status["ollama"] = "offline"
        # We don't mark overall as degraded just because Ollama is off, 
        # as it's an optional AI enhancement.
    
    return jsonify(status), 200
