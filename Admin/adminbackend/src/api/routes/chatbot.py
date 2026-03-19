"""Admin chatbot routes — powered by Ollama (Llama 4 Scout / llama3.2) with full system context."""
import json
import logging
import re
import base64
import io
import urllib.request
from datetime import datetime, timezone
from flask import Blueprint, request, jsonify, Response, stream_with_context
from bson import ObjectId

from src.config import Config
from src.utils.mongo import get_collection
from .auth import verify_token

logger = logging.getLogger(__name__)
chatbot_bp = Blueprint('chatbot', __name__)

OLLAMA_BASE = Config.OLLAMA_BASE_URL
OLLAMA_MODEL = Config.OLLAMA_MODEL
OLLAMA_VISION_MODEL = Config.OLLAMA_VISION_MODEL


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
        with urllib.request.urlopen(req, timeout=10) as resp:
            if resp.status != 200:
                print("DEBUG: Ollama server is DOWN (status != 200)")
                return False
            
            tags = json.loads(resp.read().decode())
            models = [m.get("name") for m in tags.get("models", [])]
            print(f"DEBUG: Ollama server is UP. Available models: {', '.join(models)}")
            
            if OLLAMA_MODEL not in models and f"{OLLAMA_MODEL}:latest" not in models:
                print(f"WARNING: Model '{OLLAMA_MODEL}' not found in Ollama!")
                logger.warning(f"Ollama is running but model '{OLLAMA_MODEL}' is not found.")
            return True
    except Exception as e:
        print(f"DEBUG: Ollama check failed (Connection Error): {e}")
        logger.debug(f"Ollama check failed: {e}")
    return False


def _call_vision_llm_single(base_url: str, model: str, image_b64: str, page_num: int, filename: str) -> str:
    """Call the Ollama vision LLM for a single page/image. Returns extracted text for that page."""
    print(f"DEBUG: [Vision LLM: {model}] Reading {filename} - Page {page_num}...")
    prompt = (
        f"YOU ARE A HIGH-PRECISION DOCUMENT EXTRACTION ENGINE. Extract all informative content from page {page_num} of {filename}.\n"
        "1. Capture EVERY line of text exactly as written.\n"
        "2. For tables, use markdown format.\n"
        "3. For images/charts, provide a detailed textual description.\n"
        "4. DO NOT SUMMARIZE. DO NOT ADD COMMENTARY. OUTPUT ONLY THE EXTRACTED DATA."
    )
    body = json.dumps({
        "model": model,
        "prompt": prompt,
        "images": [image_b64],
        "stream": False,
        "options": {"temperature": 0.05, "num_predict": 1500},
    }).encode()
    req = urllib.request.Request(
        f"{base_url.rstrip('/')}/api/generate",
        data=body,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=300) as resp:
            data = json.loads(resp.read().decode())
            return (data.get("response") or "").strip()
    except urllib.error.HTTPError as he:
        err_body = he.read().decode(errors='ignore')
        print(f"ERROR: [Vision] Ollama HTTP {he.code}: {err_body}")
        logger.warning(f"Vision call failed: {he.code} {err_body}")
        raise


def extract_content_with_vision_llm(content: bytes, filename: str, is_pdf: bool) -> str:
    """Uses Ollama Vision LLM to extract text page-by-page using images."""
    try:
        if not Config.USE_VISION_LLM_FOR_EXTRACTION:
            return ""

        base_url = Config.OLLAMA_BASE_URL
        model = Config.OLLAMA_VISION_MODEL

        # Check if Ollama is reachable
        if not _ollama_available():
            return ""

        if is_pdf:
            try:
                from pdf2image import convert_from_bytes
            except ImportError:
                logger.warning("Vision LLM: pdf2image not installed.")
                return ""
            
            try:
                # Process first 5 pages for vision if scanned, to keep it faster
                pdf_images = convert_from_bytes(content, first_page=1, last_page=5, dpi=120)
            except Exception as e:
                logger.warning("Vision LLM PDF conversion failed: %s", e)
                return ""

            page_texts = []
            for page_num, img in enumerate(pdf_images, start=1):
                try:
                    buffered = io.BytesIO()
                    img.save(buffered, format="JPEG", quality=85)
                    image_b64 = base64.b64encode(buffered.getvalue()).decode("utf-8")
                    logger.info(f"Vision LLM: processing page {page_num}/{len(pdf_images)} of {filename}")
                    page_text = _call_vision_llm_single(base_url, model, image_b64, page_num, filename)
                    if page_text:
                        page_texts.append(f"[Page {page_num}]\n{page_text}")
                    else:
                        page_texts.append(f"[Page {page_num}]\n(No text extracted)")
                except Exception as e:
                    logger.warning(f"Vision LLM failed on page {page_num}: {e}")
                    page_texts.append(f"[Page {page_num}]\n(Extraction failed)")

            return "\n\n".join(page_texts) if page_texts else ""
        else:
            # Single image
            image_b64 = base64.b64encode(content).decode("utf-8")
            return _call_vision_llm_single(base_url, model, image_b64, 1, filename)

    except Exception as e:
        logger.warning(f"Vision LLM extraction failed for {filename}: {e}")
        return ""


def _call_ollama_stream(system_prompt: str, user_message: str, context: str = "", history: list = None):
    """Call Ollama and yield the response chunks for streaming."""
    import requests
    print(f"DEBUG: Calling Ollama Model [{OLLAMA_MODEL}] (Streaming)...")
    
    # Format history
    hist_str = ""
    if history:
        for msg in history:
            role = "Admin" if msg.get("role") == "user" else "Assistant"
            content = msg.get('content', '')
            if len(content) > 400: # Slightly tighter truncation for speed
                content = content[:400] + "..."
            hist_str += f"{role}: {content}\n"
    
    full_prompt = f"{system_prompt}\n\n{f'CONTEXT:{chr(10)}{context}' if context else ''}\n\n{hist_str}\nAdmin: {user_message}\nAssistant:"
    
    payload = {
        "model": OLLAMA_MODEL,
        "prompt": full_prompt,
        "stream": True, # ENABLE STREAMING
        "options": {
            "temperature": 0.2, 
            "num_predict": 1024,
            "num_ctx": 12288 # Support larger contexts for PDF
        },
    }

    try:
        url = f"{OLLAMA_BASE.rstrip('/')}/api/generate"
        response = requests.post(url, json=payload, stream=True, timeout=300)
        response.raise_for_status()

        for line in response.iter_lines():
            if line:
                chunk = json.loads(line.decode())
                token = chunk.get("response", "")
                if token:
                    yield token
                if chunk.get("done"):
                    break
    except Exception as e:
        logger.error(f"Ollama stream failed: {e}")
        yield f"⚠️ Error: {str(e)}"


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

## SYSTEM CONTEXT
You have real-time access to the following system data:
- Total users: {ctx.get('total_users', 'N/A')} (Active: {ctx.get('active_users', 'N/A')}, Inactive: {ctx.get('inactive_users', 'N/A')})
- Total jobs: {ctx.get('total_jobs', 'N/A')} (Pending: {ctx.get('pending_jobs', 'N/A')}, Accepted: {ctx.get('accepted_jobs', 'N/A')}, Completed: {ctx.get('completed_jobs', 'N/A')})
- Total chat sessions: {ctx.get('total_sessions', 'N/A')}

Recent users: {"- " + (", ".join([f"{u['username']} ({u['email']})" for u in ctx.get('recent_users', [])])) if ctx.get('recent_users') else "No recent users."}
Recent jobs: {"- " + (", ".join([f"{j['job_id']}: {j['title']} ({j['status']})" for j in ctx.get('recent_jobs', [])])) if ctx.get('recent_jobs') else "No recent jobs."}

## DOCUMENT HANDLING
If a "CONTEXT:" block is provided below, it contains text extracted from an uploaded PDF or image, often with [Page X] markers.
- **Accuracy is Critical**: Always cite the exact page number (e.g., "[Page 5]") where you found the information.
- **Top-to-Bottom Reading**: Read the entire provided context carefully. If the context is focused (prefixed with "--- FOCUSING ON PAGE X ---"), that is your primary source.
- **Page-Specific Queries**: If the user asks for a specific page, look for that [Page X] marker and provide the most detailed answer possible for that section.
- **Summarization**: Summarize the document clearly if requested. If no specific page is mentioned, synthesize a high-level overview of all provided pages.

## ADMIN ACTIONS
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
        print(f"DEBUG: Received Admin Request: '{user_message[:50]}...'")
        file_context = (data.get('file_context') or '').strip()
        attachments = data.get('attachments') or []
        session_id = data.get('session_id') or f"admin_{int(datetime.now(timezone.utc).timestamp())}"
        
        if not user_message:
            return jsonify({"error": "Missing message"}), 400

        # Persist user message
        try:
            col = _col(Config.MONGO_ADMIN_HISTORY_COLLECTION)
            col.insert_one({
                "session_id": session_id,
                "role": "user",
                "content": user_message,
                "attachments": attachments,
                "timestamp": datetime.now(timezone.utc).isoformat()
            })
        except Exception as e:
            logger.warning(f"Could not persist user message: {e}")

        ctx = _gather_system_context()
        system_prompt = _build_system_prompt(ctx)

        logger.info(f"Admin Chatbot: User Message: {user_message}")
        if file_context:
            logger.info(f"Admin Chatbot: File Context Length: {len(file_context)} chars")
            logger.debug(f"Admin Chatbot: File Context (first 500 chars): {file_context[:500]}")
        else:
            logger.info("Admin Chatbot: No File Context provided.")

        # Fetch last 5 messages for context (excluding the one we just inserted)
        history = []
        try:
            h_col = _col(Config.MONGO_ADMIN_HISTORY_COLLECTION)
            # Find 6 to account for the one we just inserted
            raw_h = list(h_col.find({"session_id": session_id}).sort("timestamp", -1).limit(6))
            raw_h.reverse()
            # If the last one is the current user message, remove it
            if raw_h and raw_h[-1].get("role") == "user" and raw_h[-1].get("content") == user_message:
                raw_h.pop()
            history = raw_h
        except Exception as e:
            logger.warning(f"Could not fetch chat history: {e}")

        action_result = ""
        bot_response = ""

        # Logic for Page-Specific Focusing (Speed & Accuracy)
        focused_context = file_context
        page_match = re.search(r'(?:page|pg|p\.?)\s*(\d+)', user_message, re.IGNORECASE)
        if page_match and file_context:
            page_num = page_match.group(1)
            marker = f"[Page {page_num}]"
            if marker in file_context:
                logger.info(f"Admin Chatbot: Focusing context on {marker}")
                # Extract this page and a bit of surrounding for context
                parts = file_context.split("[Page ")
                current_page_text = ""
                for p in parts:
                    if p.startswith(f"{page_num}]"):
                        current_page_text = "[Page " + p
                        break
                if current_page_text:
                    focused_context = f"--- FOCUSING ON PAGE {page_num} ---\n{current_page_text}\n--- END FOCUS ---"
        
        # Limit global context to prevent token overflows/slowness
        final_context = focused_context[:7000]

        if not _ollama_available():
            # Fallback (Lite Intelligence mode) - Not streamed for simplicity in fallback
            bot_response = "I am currently in **Lite Mode** because Ollama is not reachable."
            # (Simplifying fallback for brevity, assuming standard non-streamed return is fine here or I'll stream a single chunk)
            def generate_fallback():
                yield bot_response
            return Response(stream_with_context(generate_fallback()), mimetype='text/event-stream')

        def generate_response():
            full_bot_response = ""
            try:
                # Log actual prompt context
                logger.info(f"Admin Chatbot: Starting stream for {session_id}")
                
                for chunk in _call_ollama_stream(system_prompt, user_message, final_context, history):
                    full_bot_response += chunk
                    yield chunk

                # After stream finishes, persist to DB
                try:
                    col = _col(Config.MONGO_ADMIN_HISTORY_COLLECTION)
                    col.insert_one({
                        "session_id": session_id,
                        "role": "assistant",
                        "content": full_bot_response,
                        "timestamp": datetime.now(timezone.utc).isoformat()
                    })
                except Exception as db_err:
                    logger.warning(f"Failed to persist streamed response: {db_err}")

            except Exception as e:
                logger.error(f"Stream generation error: {e}")
                yield f"\n\n❌ Connection lost: {str(e)}"

        return Response(stream_with_context(generate_response()), mimetype='text/event-stream')

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
        is_pdf = filename.lower().endswith('.pdf')

        extracted_text = ""
        
        # 1. Try PyMuPDF (fitz) - FASTEST, TEXT-BASED
        if is_pdf:
            try:
                import fitz
                print(f"DEBUG: [Extraction] Trying PyMuPDF for {filename}...")
                doc = fitz.open(stream=file_bytes, filetype="pdf")
                pages = [doc[i].get_text() for i in range(min(len(doc), 100))]
                extracted_text = "\n\n".join(f"[Page {i+1}]\n{t}" for i, t in enumerate(pages) if t.strip())
                if extracted_text.strip():
                    print(f"DEBUG: [Extraction] PyMuPDF successful for {filename}")
            except Exception as fitz_err:
                logger.warning(f"PyMuPDF failed for {filename}: {fitz_err}")

        # 2. Fallback to PyPDF2 - SECONDARY TEXT-BASED
        if not extracted_text.strip() and is_pdf:
            try:
                import PyPDF2
                print(f"DEBUG: [Extraction] Trying PyPDF2 fallback for {filename}...")
                reader = PyPDF2.PdfReader(io.BytesIO(file_bytes))
                parts = []
                for i in range(min(len(reader.pages), 100)):
                    try:
                        page = reader.pages[i]
                        parts.append(f"[Page {i+1}]\n" + (page.extract_text() or "").strip())
                    except Exception:
                        pass
                extracted_text = "\n\n".join(p for p in parts if p.strip())
                if extracted_text.strip():
                    print(f"DEBUG: [Extraction] PyPDF2 successful for {filename}")
            except Exception as pypdf_err:
                logger.warning(f"PyPDF2 extraction failed for {filename}: {pypdf_err}")

        # 3. Try Vision LLM ONLY IF text extraction is very short (Scanned/Image PDF)
        if len(extracted_text.strip()) < 100 and Config.USE_VISION_LLM_FOR_EXTRACTION:
            try:
                print(f"DEBUG: [Extraction] Text extraction too short ({len(extracted_text.strip())} chars). Trying Vision LLM ({OLLAMA_VISION_MODEL}) for {filename}...")
                vision_result = extract_content_with_vision_llm(file_bytes, filename, is_pdf)
                if vision_result.strip():
                    extracted_text = vision_result
                    logger.info(f"Successfully extracted text from {filename} using Vision LLM")
            except Exception as vision_err:
                logger.warning(f"Vision extraction failed for {filename}: {vision_err}")

        # 4. Fallback to image OCR if it's an image and vision failed
        if len(extracted_text.strip()) < 100 and not is_pdf:
            try:
                from PIL import Image
                import pytesseract
                img = Image.open(io.BytesIO(file_bytes))
                extracted_text = pytesseract.image_to_string(img).strip()
            except Exception as ocr_err:
                logger.warning(f"OCR extraction failed for {filename}: {ocr_err}")

        # 4. Final Fallback: plain text / decode
        if not extracted_text.strip():
            try:
                extracted_text = file_bytes.decode('utf-8', errors='ignore')[:10000]
            except Exception:
                extracted_text = ""

        if not extracted_text.strip():
            print(f"ERROR: [Upload: {filename}] Extraction failed (final fallback empty).")
            return jsonify({"error": "Could not extract text from file"}), 422

        print(f"SUCCESS: [Upload: {filename}] Extracted {len(extracted_text)} characters.")

        return jsonify({
            "success": True,
            "filename": filename,
            "text": extracted_text[:15000],  # Increased context for high accuracy & multiple pages
            "chars": len(extracted_text),
        }), 200

    except Exception as e:
        logger.error("upload_file error: %s", e)
        return jsonify({"error": str(e)}), 500


@chatbot_bp.route('/sessions', methods=['GET'])
def get_admin_sessions():
    """List all unique admin chat sessions."""
    if not check_admin_auth():
        return jsonify({"error": "Unauthorized"}), 401
    
    try:
        col = _col(Config.MONGO_ADMIN_HISTORY_COLLECTION)
        # Group by session_id and get metadata
        pipeline = [
            {"$sort": {"timestamp": 1}},
            {"$group": {
                "_id": "$session_id",
                "last_message_at": {"$last": "$timestamp"},
                "first_content": {"$first": "$content"},
                "last_content": {"$last": "$content"},
                "message_count": {"$sum": 1}
            }},
            {"$sort": {"last_message_at": -1}}
        ]
        results = list(col.aggregate(pipeline))
        
        sessions = []
        for res in results:
            sid = res["_id"]
            # Title is first user message if possible
            title = res.get("first_content", "New Conversation")[:60]
            if len(res.get("first_content", "")) > 60: title += "..."
            
            # Preview is the last message
            preview = res.get("last_content", "")[:100]
            if len(res.get("last_content", "")) > 100: preview += "..."
            
            sessions.append({
                "session_id": sid,
                "title": title,
                "preview": preview,
                "last_message_at": res["last_message_at"],
                "message_count": res["message_count"]
            })
            
        return jsonify({"success": True, "sessions": sessions}), 200
    except Exception as e:
        logger.error(f"Error fetching admin sessions: {e}")
        return jsonify({"error": str(e)}), 500


@chatbot_bp.route('/history', methods=['GET'])
def get_admin_chat_history():
    """Fetch all messages for a specific session."""
    if not check_admin_auth():
        return jsonify({"error": "Unauthorized"}), 401
    
    session_id = request.args.get('session_id')
    if not session_id:
        return jsonify({"error": "session_id required"}), 400
        
    try:
        col = _col(Config.MONGO_ADMIN_HISTORY_COLLECTION)
        history = list(col.find({"session_id": session_id}).sort("timestamp", 1))
        
        formatted = []
        for m in history:
            formatted.append({
                "role": m.get("role"),
                "content": m.get("content"),
                "attachments": m.get("attachments", []),
                "timestamp": m.get("timestamp")
            })
            
        return jsonify({"success": True, "history": formatted}), 200
    except Exception as e:
        logger.error(f"Error fetching admin history: {e}")
        return jsonify({"error": str(e)}), 500


@chatbot_bp.route('/sessions/<session_id>', methods=['DELETE'])
def delete_admin_session(session_id):
    """Delete a chat session and its entire history."""
    if not check_admin_auth():
        return jsonify({"error": "Unauthorized"}), 401
        
    try:
        col = _col(Config.MONGO_ADMIN_HISTORY_COLLECTION)
        result = col.delete_many({"session_id": session_id})
        return jsonify({
            "success": True, 
            "message": f"Deleted session {session_id}",
            "deleted_count": result.deleted_count
        }), 200
    except Exception as e:
        logger.error(f"Error deleting admin session: {e}")
        return jsonify({"error": str(e)}), 500
