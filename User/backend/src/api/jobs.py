"""Jobs CRUD helpers for MongoDB."""
import uuid
from datetime import datetime, timezone
from typing import Optional, Dict, List, Any


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def create_job(coll, data: Dict[str, Any], user_id: Optional[str] = None) -> Dict:
    """Insert a new job document and return it."""
    job = {
        "job_id": str(uuid.uuid4()),
        "user_id": user_id,
        "session_id": data.get("session_id", ""),
        "title": data.get("title", ""),
        "client_name": data.get("client_name", ""),
        "client_contact": data.get("client_contact", ""),
        "site_address": data.get("site_address", ""),
        "start_date": data.get("start_date", ""),
        "end_date": data.get("end_date", ""),
        "window_door_type": data.get("window_door_type", ""),
        "quantity": data.get("quantity", ""),
        "description": data.get("description", ""),
        "notes": data.get("notes", ""),
        "status": data.get("status", "pending"),
        "created_at": _now(),
        "updated_at": _now(),
    }
    coll.insert_one(job)
    job.pop("_id", None)
    return job


def get_jobs(coll, user_id: Optional[str] = None) -> List[Dict]:
    """Return all jobs for the given user (or all if no user_id)."""
    query = {"user_id": user_id} if user_id else {}
    docs = list(coll.find(query, {"_id": 0}).sort("created_at", -1))
    return docs


def get_job(coll, job_id: str) -> Optional[Dict]:
    """Return a single job by job_id."""
    doc = coll.find_one({"job_id": job_id}, {"_id": 0})
    return doc


def update_job(coll, job_id: str, data: Dict[str, Any]) -> Optional[Dict]:
    """Update fields of a job and return the updated document."""
    allowed = {
        "title", "client_name", "client_contact", "site_address",
        "start_date", "end_date", "window_door_type", "quantity",
        "description", "notes", "status",
    }
    updates = {k: v for k, v in data.items() if k in allowed}
    updates["updated_at"] = _now()
    coll.update_one({"job_id": job_id}, {"$set": updates})
    return get_job(coll, job_id)


def delete_job(coll, job_id: str) -> int:
    """Delete a job. Returns number of deleted docs."""
    result = coll.delete_one({"job_id": job_id})
    return result.deleted_count
