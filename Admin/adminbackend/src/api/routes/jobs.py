"""Admin jobs management routes — view all user-placed jobs and update their status."""
import logging
from flask import Blueprint, request, jsonify
from bson import ObjectId
from datetime import datetime, timezone

from src.config import Config
from src.utils.mongo import get_collection
from .auth import verify_token

from src.api.routes.logs import log_activity

logger = logging.getLogger(__name__)
jobs_bp = Blueprint('jobs', __name__)


def check_admin_auth():
    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        return False
    token = auth_header.split(" ", 1)[1]
    return verify_token(token) is not None


def _jobs_col():
    return get_collection(Config.MONGO_URI, Config.MONGO_DB, "jobs")


def _users_col():
    return get_collection(Config.MONGO_URI, Config.MONGO_DB, "users")


@jobs_bp.route('/', methods=['GET'])
def get_all_jobs():
    """Return all jobs across all users (admin view)."""
    if not check_admin_auth():
        return jsonify({"error": "Unauthorized"}), 401
    try:
        coll = _jobs_col()
        if coll is None:
            return jsonify({"error": "Database error"}), 500

        jobs = list(coll.find({}, {"_id": 0}).sort("created_at", -1))

        # Enrich with user info from users collection
        users_col = _users_col()
        user_cache = {}
        for job in jobs:
            uid = job.get("user_id")
            if uid:
                job["user_id"] = str(uid)
            if uid and uid not in user_cache:
                try:
                    # Map full_name to username for frontend
                    u = users_col.find_one({"_id": ObjectId(uid)}, {"full_name": 1, "email": 1})
                    user_cache[uid] = {
                        "username": u.get("full_name", "Unknown") if u else "Unknown",
                        "email": u.get("email", "") if u else "",
                    }
                except Exception:
                    user_cache[uid] = {"username": "Unknown", "email": ""}
            if uid:
                job["user_info"] = user_cache.get(uid, {"username": "Unknown", "email": ""})

        return jsonify({"success": True, "jobs": jobs, "total": len(jobs)}), 200
    except Exception as e:
        logger.error("get_all_jobs error: %s", e)
        return jsonify({"error": str(e)}), 500


@jobs_bp.route('/user/<user_id>', methods=['GET'])
def get_user_jobs(user_id):
    """Return all jobs for a specific user."""
    if not check_admin_auth():
        return jsonify({"error": "Unauthorized"}), 401
    try:
        coll = _jobs_col()
        # Handle both string and ObjectId user_id
        query = {
            "$or": [
                {"user_id": user_id},
                {"user_id": ObjectId(user_id) if ObjectId.is_valid(user_id) else None}
            ]
        }
        jobs = list(coll.find(query, {"_id": 0}).sort("created_at", -1))
        
        # Ensure user_id is stringified
        for job in jobs:
            if "user_id" in job:
                job["user_id"] = str(job["user_id"])
                
        return jsonify({"success": True, "jobs": jobs}), 200
    except Exception as e:
        logger.error("get_user_jobs error: %s", e)
        return jsonify({"error": str(e)}), 500


@jobs_bp.route('/<job_id>', methods=['GET'])
def get_job(job_id):
    """Get a single job by job_id."""
    if not check_admin_auth():
        return jsonify({"error": "Unauthorized"}), 401
    try:
        coll = _jobs_col()
        job = coll.find_one({"job_id": job_id}, {"_id": 0})
        if not job:
            return jsonify({"error": "Job not found"}), 404
        return jsonify({"success": True, "job": job}), 200
    except Exception as e:
        logger.error("get_job error: %s", e)
        return jsonify({"error": str(e)}), 500


@jobs_bp.route('/<job_id>/status', methods=['PUT'])
def update_job_status(job_id):
    """Update a job's status (accepts, in_progress, completed, rejected, etc.)."""
    if not check_admin_auth():
        return jsonify({"error": "Unauthorized"}), 401
    try:
        data = request.get_json() or {}
        new_status = data.get("status", "").strip()
        allowed = {"pending", "confirmed", "in_progress", "completed", "cancelled", "accepted", "rejected"}
        if new_status not in allowed:
            return jsonify({"error": f"Invalid status. Allowed: {', '.join(allowed)}"}), 400

        coll = _jobs_col()
        now = datetime.now(timezone.utc).isoformat()
        result = coll.update_one(
            {"job_id": job_id},
            {"$set": {"status": new_status, "updated_at": now, "admin_note": data.get("note", "")}}
        )
        if result.matched_count == 0:
            return jsonify({"error": "Job not found"}), 404

        job = coll.find_one({"job_id": job_id}, {"_id": 0})
        return jsonify({"success": True, "job": job}), 200
    except Exception as e:
        logger.error("update_job_status error: %s", e)
        return jsonify({"error": str(e)}), 500


@jobs_bp.route('/stats', methods=['GET'])
def jobs_stats():
    """Return job counts grouped by status."""
    if not check_admin_auth():
        return jsonify({"error": "Unauthorized"}), 401
    try:
        coll = _jobs_col()
        pipeline = [{"$group": {"_id": "$status", "count": {"$sum": 1}}}]
        result = list(coll.aggregate(pipeline))
        stats = {r["_id"]: r["count"] for r in result}
        total = sum(stats.values())
        return jsonify({"success": True, "stats": stats, "total": total}), 200
    except Exception as e:
        logger.error("jobs_stats error: %s", e)
        return jsonify({"error": str(e)}), 500
