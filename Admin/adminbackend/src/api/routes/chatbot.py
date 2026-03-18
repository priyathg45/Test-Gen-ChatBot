"""Admin chatbot routes — powered by Ollama (Llama 4 Scout / llama3.2) with full system context."""
import json
import logging
import re
import urllib.request
from datetime import datetime, timezone
from flask import Blueprint, request, jsonify
from bson import ObjectId

from src.config import Config
from src.utils.mongo import get_collection
from .auth import verify_token

logger = logging.getLogger(__name__)
chatbot_bp = Blueprint('chatbot', __name__)

OLLAMA_BASE = Config.OLLAMA_BASE_URL
OLLAMA_MODEL = Config.OLLAMA_MODEL


def check_admin_auth():
    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        return False
    token = auth_header.split(" ", 1)[1]
    return verify_token(token) is not None


def _col(name):
    return get_collection(Config.MONGO_URI, Config.MONGO_DB, name)


def _ollama_available():
    """Check if Ollama server and the specified model are available."""
    try:
        # Check if server is up
        req = urllib.request.Request(f"{OLLAMA_BASE.rstrip('/')}/api/tags", method="GET")
        with urllib.request.urlopen(req, timeout=2) as resp:
            if resp.status != 200:
                return False
            
            # Optional: Check if the specific model is pulled
            tags = json.loads(resp.read().decode())
            models = [m.get("name") for m in tags.get("models", [])]
            if OLLAMA_MODEL not in models and f"{OLLAMA_MODEL}:latest" not in models:
                logger.warning(f"Ollama is running but model '{OLLAMA_MODEL}' is not found.")
                # We still return True if server is up, Ollama might auto-pull or handle it
            return True
    except Exception as e:
        logger.debug(f"Ollama check failed: {e}")
        return False


def _call_ollama(system_prompt: str, user_message: str, context: str = "") -> str:
    """Call Ollama and return the response string."""
    full_prompt = f"{system_prompt}\n\n{f'CONTEXT:{chr(10)}{context}' if context else ''}\n\nAdmin: {user_message}\nAssistant:"
    body = json.dumps({
        "model": OLLAMA_MODEL,
        "prompt": full_prompt,
        "stream": False,
        "options": {"temperature": 0.3, "num_predict": 1024},
    }).encode()
    req = urllib.request.Request(
        f"{OLLAMA_BASE.rstrip('/')}/api/generate",
        data=body,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=120) as resp:
        raw = json.loads(resp.read().decode())
        return (raw.get("response") or "").strip()


def _gather_system_context() -> dict:
    """Gather live system data to inject into the LLM prompt."""
    ctx = {}
    try:
        users_col = _col("users")
        ctx["total_users"] = users_col.count_documents({})
        ctx["active_users"] = users_col.count_documents({"is_active": {"$ne": False}})
        ctx["inactive_users"] = users_col.count_documents({"is_active": False})
        recent_users = list(users_col.find({}, {"username": 1, "email": 1, "is_active": 1, "created_at": 1})
                            .sort("created_at", -1).limit(5))
        ctx["recent_users"] = [
            {"username": u.get("username"), "email": u.get("email"),
             "is_active": u.get("is_active", True), "id": str(u.get("_id", ""))}
            for u in recent_users
        ]
    except Exception as e:
        ctx["user_error"] = str(e)

    try:
        jobs_col = _col("jobs")
        ctx["total_jobs"] = jobs_col.count_documents({})
        ctx["pending_jobs"] = jobs_col.count_documents({"status": "pending"})
        ctx["accepted_jobs"] = jobs_col.count_documents({"status": {"$in": ["accepted", "confirmed"]}})
        ctx["completed_jobs"] = jobs_col.count_documents({"status": "completed"})
        recent_jobs = list(jobs_col.find({}, {"title": 1, "client_name": 1, "status": 1, "user_id": 1, "job_id": 1, "created_at": 1})
                           .sort("created_at", -1).limit(5))
        ctx["recent_jobs"] = [
            {"job_id": j.get("job_id"), "title": j.get("title"),
             "client": j.get("client_name"), "status": j.get("status")}
            for j in recent_jobs
        ]
    except Exception as e:
        ctx["job_error"] = str(e)

    try:
        history_col = _col("history")
        ctx["total_sessions"] = history_col.count_documents({})
    except Exception:
        ctx["total_sessions"] = "unknown"

    return ctx


def _build_system_prompt(ctx: dict) -> str:
    return f"""You are the Genesis Admin Intelligence — a powerful AI assistant for the Genesis IT Lab admin panel.

You have real-time access to the following system data:
- Total users: {ctx.get('total_users', 'N/A')} (Active: {ctx.get('active_users', 'N/A')}, Inactive: {ctx.get('inactive_users', 'N/A')})
- Total jobs: {ctx.get('total_jobs', 'N/A')} (Pending: {ctx.get('pending_jobs', 'N/A')}, Accepted: {ctx.get('accepted_jobs', 'N/A')}, Completed: {ctx.get('completed_jobs', 'N/A')})
- Total chat sessions: {ctx.get('total_sessions', 'N/A')}

Recent users: {json.dumps(ctx.get('recent_users', []), indent=2)}
Recent jobs: {json.dumps(ctx.get('recent_jobs', []), indent=2)}

You can perform these admin ACTIONS by outputting specific JSON at the start of your response:
- Deactivate user: {{"action": "deactivate_user", "user_id": "<id>"}}
- Activate user: {{"action": "activate_user", "user_id": "<id>"}}
- Delete user: {{"action": "delete_user", "user_id": "<id>"}}
- Accept job: {{"action": "accept_job", "job_id": "<job_id>"}}
- Reject job: {{"action": "reject_job", "job_id": "<job_id>"}}

RULES:
- Be concise but comprehensive
- Use structured markdown (bullet points, headers, tables) for lists
- Always cite actual numbers from the system data above
- For user management actions, ask for confirmation if the request is destructive
- Format dates as human-readable strings
- Respond ONLY in English
"""


def _execute_action(action_data: dict) -> str:
    """Execute an admin action and return a result message."""
    action = action_data.get("action", "")
    try:
        if action in ("activate_user", "deactivate_user"):
            user_id = action_data.get("user_id")
            is_active = action == "activate_user"
            users_col = _col("users")
            result = users_col.update_one(
                {"_id": ObjectId(user_id)},
                {"$set": {"is_active": is_active, "updated_at": datetime.now(timezone.utc).isoformat()}}
            )
            status = "activated" if is_active else "deactivated"
            return f"\n\n✅ **Action completed:** User {status} successfully." if result.matched_count else "\n\n⚠️ User not found."

        elif action == "delete_user":
            user_id = action_data.get("user_id")
            users_col = _col("users")
            result = users_col.delete_one({"_id": ObjectId(user_id)})
            return "\n\n✅ **Action completed:** User deleted." if result.deleted_count else "\n\n⚠️ User not found."

        elif action in ("accept_job", "reject_job"):
            job_id = action_data.get("job_id")
            new_status = "accepted" if action == "accept_job" else "rejected"
            jobs_col = _col("jobs")
            result = jobs_col.update_one(
                {"job_id": job_id},
                {"$set": {"status": new_status, "updated_at": datetime.now(timezone.utc).isoformat()}}
            )
            return f"\n\n✅ **Action completed:** Job {new_status}." if result.matched_count else "\n\n⚠️ Job not found."
    except Exception as e:
        return f"\n\n❌ Action failed: {e}"
    return ""


@chatbot_bp.route('/ask', methods=['POST'])
def ask_admin_bot():
    """Endpoint for admin chatbot queries with real Ollama LLM and system context."""
    if not check_admin_auth():
        return jsonify({"error": "Unauthorized"}), 401
    try:
        data = request.get_json() or {}
        user_message = (data.get('message') or '').strip()
        file_context = (data.get('file_context') or '').strip()
        if not user_message:
            return jsonify({"error": "Missing message"}), 400

        ctx = _gather_system_context()
        system_prompt = _build_system_prompt(ctx)

        action_result = ""
        bot_response = ""

        if _ollama_available():
            try:
                bot_response = _call_ollama(system_prompt, user_message, file_context)
                # Check if the response contains an action JSON at the start
                action_match = re.search(r'\{[^}]+"action"[^}]+\}', bot_response)
                if action_match:
                    try:
                        action_data = json.loads(action_match.group(0))
                        action_result = _execute_action(action_data)
                        bot_response = bot_response.replace(action_match.group(0), '').strip()
                    except json.JSONDecodeError:
                        pass
            except Exception as ex:
                logger.warning("Ollama call failed, using fallback: %s", ex)
                bot_response = ""

        # Fallback (Lite Intelligence mode)
        if not bot_response:
            msg_lower = user_message.lower()
            
            # Helper for summary
            total_u = ctx.get('total_users', 0)
            active_u = ctx.get('active_users', 0)
            total_j = ctx.get('total_jobs', 0)
            pending_j = ctx.get('pending_jobs', 0)
            
            if any(k in msg_lower for k in ["how many user", "total user", "user count", "user stats", "summary"]):
                bot_response = (
                    f"## 📊 Genesis System Summary (Lite Mode)\n\n"
                    f"Currently operating in **Fallback Mode** (Ollama unavailable).\n\n"
                    f"### 👥 Users\n"
                    f"- **Total:** {total_u}\n"
                    f"- **Active:** {active_u}\n"
                    f"- **Inactive:** {ctx.get('inactive_users', 0)}\n\n"
                    f"### 💼 Jobs\n"
                    f"- **Total:** {total_j}\n"
                    f"- **Pending Approval:** {pending_j}\n"
                    f"- **Completed:** {ctx.get('completed_jobs', 0)}\n\n"
                    f"### 💬 sessions\n"
                    f"- **Total Chat Sessions:** {ctx.get('total_sessions', 0)}\n\n"
                    f"⚠️ *Start Ollama (`ollama run {OLLAMA_MODEL}`) for full AI capabilities.*"
                )
            elif any(k in msg_lower for k in ["job", "pending", "placed", "list jobs"]):
                rj = ctx.get('recent_jobs', [])
                lines = "\n".join(f"- **{j['title']}** (Client: {j['client']}) — Status: `{j['status']}`" for j in rj) if rj else "No recent jobs found."
                bot_response = (
                    f"## 💼 Jobs Overview (Lite Mode)\n\n"
                    f"Showing recent activity from the database:\n\n"
                    f"{lines}\n\n"
                    f"**Quick Stats:**\n"
                    f"- Pending: {pending_j}\n"
                    f"- Accepted: {ctx.get('accepted_jobs', 0)}\n"
                    f"- Completed: {ctx.get('completed_jobs', 0)}"
                )
            elif any(k in msg_lower for k in ["status", "health", "system", "check"]):
                bot_response = (
                    f"## ✅ System Health Check\n\n"
                    f"- **Database (MongoDB):** Connected\n"
                    f"- **Admin Backend:** Operational\n"
                    f"- **AI Engine (Ollama):** ⚠️ Offline (Fallback active)\n\n"
                    f"The system remains functional, but complex reasoning and natural language processing are limited."
                )
            else:
                bot_response = (
                    f"I am currently in **Lite Mode** because Ollama is not reachable. I can still provide system data and perform basic actions.\n\n"
                    f"**System Snapshot:**\n"
                    f"- Users: {total_u} ({active_u} active)\n"
                    f"- Jobs: {total_j} ({pending_j} pending)\n\n"
                    f"**Available Actions:**\n"
                    f"- To manage users or jobs, please use the sidebar or ask specifically about 'users' or 'jobs'.\n\n"
                    f"⚠️ *Tip: Ask 'System summary' for a full look at the current state.*"
                )

        return jsonify({"response": bot_response + action_result}), 200

    except Exception as e:
        logger.error("Error in admin chatbot: %s", e)
        return jsonify({"error": "Failed to process query"}), 500


@chatbot_bp.route('/upload', methods=['POST'])
def upload_file_for_context():
    """Accept a file, extract text, and return it for use as chat context."""
    if not check_admin_auth():
        return jsonify({"error": "Unauthorized"}), 401
    try:
        if 'file' not in request.files:
            return jsonify({"error": "No file provided"}), 400
        file = request.files['file']
        file_bytes = file.read()
        filename = file.filename or 'document'

        extracted_text = ""
        # Try PyMuPDF for PDFs
        try:
            import fitz
            doc = fitz.open(stream=file_bytes, filetype="pdf")
            pages = [doc[i].get_text() for i in range(min(len(doc), 10))]
            extracted_text = "\n\n".join(f"[Page {i+1}]\n{t}" for i, t in enumerate(pages) if t.strip())
        except Exception:
            # Fallback: plain text files
            try:
                extracted_text = file_bytes.decode('utf-8', errors='ignore')[:4000]
            except Exception:
                extracted_text = ""

        if not extracted_text.strip():
            return jsonify({"error": "Could not extract text from file"}), 422

        return jsonify({
            "success": True,
            "filename": filename,
            "text": extracted_text[:5000],
            "chars": len(extracted_text),
        }), 200

    except Exception as e:
        logger.error("upload_file error: %s", e)
        return jsonify({"error": str(e)}), 500
