"""Flask API for the Aluminum Products Chatbot."""
import io
import os
import sys
import logging
from flask import Flask, request, jsonify, send_file, g, Response
from flask_cors import CORS
from datetime import datetime

# Ensure 'src' is in the Python path regardless of how the script is run
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

# Configure logging
from src.utils.logger import setup_logging
setup_logging()
logger = logging.getLogger(__name__)

from src.config import Config, DevelopmentConfig, ProductionConfig
from src.data.loader import DataLoader
from src.data.preprocessor import DataPreprocessor
from src.chatbot.embeddings import EmbeddingsManager
from src.chatbot.retriever import Retriever
from src.chatbot.chatbot import AluminiumChatBot
from src.utils.mongo import (
    get_collection,
    get_database,
    ensure_history_collection,
    ensure_users_collection,
    ensure_activity_logs_collection,
)
from src.document.attachments import (
    save_attachment,
    get_attachments_for_session,
    delete_attachments_for_session,
    delete_attachment,
    get_attachment_file,
    is_allowed_file,
    content_type_from_filename,
)
from src.auth import (
    create_user,
    find_user_by_email,
    find_user_by_id,
    list_users,
    update_user_profile,
    set_user_role,
    hash_password,
    check_password,
    create_access_token,
    decode_token,
    log_activity,
    get_activity_logs,
    ROLE_ADMIN,
    ROLE_USER,
)
from src.auth.activity import (
    ACTION_LOGIN,
    ACTION_LOGOUT,
    ACTION_CHAT,
    ACTION_REGISTER,
    ACTION_ADMIN_VIEW_USERS,
    ACTION_ADMIN_VIEW_USER,
    ACTION_ADMIN_VIEW_HISTORY,
    ACTION_ADMIN_VIEW_LOGS,
    ACTION_ADMIN_UPDATE_USER,
)

# Initialize Flask app
app = Flask(__name__)
_flask_env = os.getenv('FLASK_ENV', 'development').lower()
app.config.from_object(DevelopmentConfig if _flask_env != 'production' else ProductionConfig)
app.config["JSONIFY_PRETTYPRINT_REGULAR"] = True
app.json.sort_keys = False  # type: ignore
app.json.ensure_ascii = False  # type: ignore
app.json.compact = False  # type: ignore
CORS(
    app,
    resources={r"/*": {"origins": app.config['CORS_ORIGINS']}},
    allow_headers=["Content-Type", "Authorization"],
    methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    supports_credentials=False,
)

# Global variables for the chatbot
from typing import Optional, Any
chatbot: Optional[Any] = None
data_loader: Optional[Any] = None
embeddings_manager: Optional[Any] = None
retriever: Optional[Any] = None
mongo_db: Optional[Any] = None


def _get_users_coll():
    """Return users collection or None."""
    if mongo_db is None:
        return None
    return mongo_db[app.config.get('MONGO_USERS_COLLECTION', 'users')]


def _get_logs_coll():
    """Return activity logs collection or None."""
    if mongo_db is None:
        return None
    return mongo_db[app.config.get('MONGO_ACTIVITY_LOGS_COLLECTION', 'activity_logs')]


def _current_user():
    """Parse Authorization Bearer token and return payload dict (sub, email, role) or None."""
    auth = request.headers.get('Authorization')
    if not auth or not auth.startswith('Bearer '):
        return None
    token = auth[7:].strip()
    if not token:
        return None
    payload = decode_token(token, app.config.get('JWT_SECRET_KEY', ''))
    return payload


def _require_admin():
    """Return (payload, None) if admin else (None, error_response)."""
    payload = _current_user()
    if not payload:
        return None, (jsonify({'success': False, 'error': 'Authentication required'}), 401)
    if payload.get('role') != ROLE_ADMIN:
        return None, (jsonify({'success': False, 'error': 'Admin access required'}), 403)
    return payload, None


def _ensure_bootstrap_admin():
    """If INIT_ADMIN_EMAIL and INIT_ADMIN_PASSWORD are set and no admin exists, create one."""
    email = (app.config.get('INIT_ADMIN_EMAIL') or '').strip()
    password = app.config.get('INIT_ADMIN_PASSWORD') or ''
    if not email or not password:
        return
    users_coll = mongo_db[app.config.get('MONGO_USERS_COLLECTION', 'users')] if mongo_db else None
    if users_coll is None:
        return
    if users_coll.find_one({'role': ROLE_ADMIN}):
        return
    if users_coll.find_one({'email': email.lower()}):
        return
    password_hash = hash_password(password)
    create_user(users_coll, email, password_hash, full_name='Admin', role=ROLE_ADMIN)
    logger.info("Bootstrap admin user created for %s", email)


def initialize_chatbot():
    """Initialize the chatbot system."""
    global chatbot, data_loader, embeddings_manager, retriever, mongo_db

    try:
        logger.info("Initializing chatbot system...")

        mongo_products_collection = None
        history_collection = None
        mongo_db = None

        if app.config['USE_MONGO'] and app.config['MONGO_URI']:
            try:
                mongo_db = get_database(
                    app.config['MONGO_URI'],
                    app.config['MONGO_DB'],
                    **app.config.get('MONGO_CLIENT_KWARGS', {}),
                )
                mongo_products_collection = mongo_db[app.config['MONGO_PRODUCTS_COLLECTION']]
                history_collection = ensure_history_collection(
                    app.config['MONGO_URI'],
                    app.config['MONGO_DB'],
                    app.config['MONGO_HISTORY_COLLECTION'],
                    **app.config.get('MONGO_CLIENT_KWARGS', {}),
                )
                mongo_products_collection.database.client.admin.command("ping")
                ensure_users_collection(mongo_db, app.config.get('MONGO_USERS_COLLECTION', 'users'))
                ensure_activity_logs_collection(mongo_db, app.config.get('MONGO_ACTIVITY_LOGS_COLLECTION', 'activity_logs'))
                logger.info(
                    "MongoDB connected: %s/%s (products) | %s (history) | %s (users) | %s (activity_logs)",
                    app.config['MONGO_URI'],
                    app.config['MONGO_DB'],
                    app.config['MONGO_HISTORY_COLLECTION'],
                    app.config.get('MONGO_USERS_COLLECTION', 'users'),
                    app.config.get('MONGO_ACTIVITY_LOGS_COLLECTION', 'activity_logs'),
                )
            except Exception as mongo_exc:
                mongo_products_collection = None
                history_collection = None
                mongo_db = None
                logger.error("MongoDB connection failed; falling back to CSV/memory: %s", mongo_exc)

        # Load data
        data_loader = DataLoader(
            app.config['DATA_PATH'],
            use_mongo=app.config['USE_MONGO'] and mongo_products_collection is not None,
            mongo_uri=app.config['MONGO_URI'],
            mongo_db=app.config['MONGO_DB'],
            mongo_collection=app.config['MONGO_PRODUCTS_COLLECTION'],
        )
        df = data_loader.load()

        # If Mongo was requested but loading failed, fall back to CSV (keep history connection intact)
        if df is None and app.config['USE_MONGO']:
            logger.warning("MongoDB products not available; retrying with CSV at %s", app.config['DATA_PATH'])
            mongo_products_collection = None
            data_loader = DataLoader(
                app.config['DATA_PATH'],
                use_mongo=False,
            )
            df = data_loader.load()
        
        if df is None:
            logger.error("Startup aborted: no product data available after Mongo/CSV attempts")
            raise Exception("Failed to load data from MongoDB and CSV")
        
        # Preprocess data
        preprocessor = DataPreprocessor(df)
        df = preprocessor.preprocess_all().get_processed_data()
        logger.info(f"Data preprocessed: {len(df)} products")
        
        # Initialize embeddings
        embeddings_manager = EmbeddingsManager(model_name=app.config['MODEL_NAME'])
        
        # Prepare texts for embedding
        if 'combined_text' in df.columns:
            texts = df['combined_text'].tolist()
        else:
            texts = (df['product_name'] + ' ' + df['category'] + ' ' + df['description']).tolist()
        
        # Create embeddings
        embeddings_manager.create_embeddings(texts)
        logger.info(f"Embeddings created: {len(texts)} products")
        
        # Initialize retriever
        retriever = Retriever(
            embeddings_manager,
            df,
            top_k=app.config['TOP_K_RESULTS'],
            similarity_threshold=app.config['SIMILARITY_THRESHOLD']
        )
        
        # Initialize chatbot
        chatbot = AluminiumChatBot(
            retriever,
            embeddings_manager,
            app.config,
            history_collection=history_collection,
            database=mongo_db,
            attachments_collection_name=app.config.get('MONGO_ATTACHMENTS_COLLECTION', 'chat_attachments'),
        )
        if history_collection is not None:
            logger.info("Chat history persistence: MongoDB (%s)", app.config['MONGO_HISTORY_COLLECTION'])
        else:
            logger.warning("Chat history persistence: in-memory (Mongo disabled or unreachable)")

        # Optional: bootstrap first admin if env set and no admin exists
        _ensure_bootstrap_admin()

        logger.info("Chatbot system initialized successfully")
        
    except Exception as e:
        logger.error(f"Error initializing chatbot: {str(e)}")
        raise

@app.before_request
def before_request():
    """Log incoming request, handle CORS preflight, and initialize chatbot lazily if needed."""
    path = request.path or "/"
    method = request.method
    print(f">>> API {method} {path}", flush=True)
    logger.info("API request: %s %s", method, path)
    if request.method == "OPTIONS":
        # CORS preflight: respond 200 so browser sends the actual request (CORS adds headers in after_request)
        return "", 200
    g._request_start = datetime.now()
    if chatbot is None:
        logger.info("Lazy initialization triggered by first request")
        initialize_chatbot()


@app.after_request
def after_request(response):
    """Log response status so API activity is visible in the terminal."""
    path = request.path or "/"
    method = request.method
    status = response.status_code
    logger.info("API response: %s %s -> %s", method, path, status)
    print(f"<<< API {method} {path} -> {status}", flush=True)  # Always visible in terminal
    return response


def _maybe_eager_init():
    """Eagerly initialize chatbot at startup when enabled."""
    if app.config.get('EAGER_INIT', True):
        if chatbot is None:
            logger.info("Eager initialization enabled; booting chatbot now...")
            try:
                initialize_chatbot()
            except Exception as exc:
                logger.error("Eager initialization failed: %s", exc)
        else:
            logger.info("Chatbot already initialized before eager init")


# Perform eager init on module import if configured
_maybe_eager_init()

# ----- Auth routes -----
@app.route('/auth/register', methods=['POST'])
def register():
    """Register a new user (role=user by default)."""
    try:
        if mongo_db is None:
            return jsonify({'success': False, 'error': 'Registration unavailable (database not connected)'}), 503
        data = request.get_json() or {}
        email = (data.get('email') or '').strip()
        password = data.get('password')
        full_name = (data.get('full_name') or '').strip()
        if not email:
            return jsonify({'success': False, 'error': 'Email is required'}), 400
        if not password or len(password) < 6:
            return jsonify({'success': False, 'error': 'Password must be at least 6 characters'}), 400
        users_coll = _get_users_coll()
        if users_coll is None:
            return jsonify({'success': False, 'error': 'Registration unavailable'}), 503
        password_hash = hash_password(password)
        user = create_user(users_coll, email, password_hash, full_name=full_name, role=ROLE_USER)
        if user is None:
            return jsonify({'success': False, 'error': 'Email already registered'}), 409
        log_activity(
            _get_logs_coll(),
            user_id=user['id'],
            action=ACTION_REGISTER,
            resource='auth',
            ip=request.remote_addr,
        )
        token = create_access_token(
            user['id'],
            user['email'],
            user['role'],
            app.config['JWT_SECRET_KEY'],
            app.config.get('JWT_ACCESS_EXPIRES_HOURS', 24),
        )
        return jsonify({
            'success': True,
            'user': user,
            'access_token': token,
        }), 201
    except Exception as e:
        logger.exception("Register failed")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/auth/login', methods=['POST'])
def login():
    """Login: returns user + access_token."""
    try:
        if mongo_db is None:
            return jsonify({'success': False, 'error': 'Login unavailable (database not connected)'}), 503
        data = request.get_json() or {}
        email = (data.get('email') or '').strip()
        password = data.get('password') or ''
        if not email:
            return jsonify({'success': False, 'error': 'Email is required'}), 400
        users_coll = _get_users_coll()
        if users_coll is None:
            return jsonify({'success': False, 'error': 'Login unavailable'}), 503
        doc = find_user_by_email(users_coll, email)
        if not doc or not check_password(password, doc.get('password_hash', '')):
            return jsonify({'success': False, 'error': 'Invalid email or password'}), 401
        user = {
            'id': str(doc['_id']),
            'email': doc.get('email'),
            'full_name': doc.get('full_name', ''),
            'role': doc.get('role', ROLE_USER),
            'created_at': doc.get('created_at'),
            'updated_at': doc.get('updated_at'),
        }
        log_activity(
            _get_logs_coll(),
            user_id=user['id'],
            action=ACTION_LOGIN,
            resource='auth',
            ip=request.remote_addr,
        )
        token = create_access_token(
            user['id'],
            user['email'],
            user['role'],
            app.config['JWT_SECRET_KEY'],
            app.config.get('JWT_ACCESS_EXPIRES_HOURS', 24),
        )
        return jsonify({
            'success': True,
            'user': user,
            'access_token': token,
        }), 200
    except Exception as e:
        logger.exception("Login failed")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/auth/logout', methods=['POST'])
def logout():
    """Optional: log logout activity. Client should clear token regardless."""
    payload = _current_user()
    if payload:
        log_activity(
            _get_logs_coll(),
            user_id=payload['sub'],
            action=ACTION_LOGOUT,
            resource='auth',
            ip=request.remote_addr,
        )
    return jsonify({'success': True}), 200


@app.route('/me', methods=['GET', 'PUT'])
def me():
    """Get or update current user profile (requires valid token)."""
    payload = _current_user()
    if not payload:
        return jsonify({'success': False, 'error': 'Authentication required'}), 401
    users_coll = _get_users_coll()
    if users_coll is None:
        return jsonify({'success': False, 'error': 'Service unavailable'}), 503
    if request.method == 'PUT':
        data = request.get_json() or {}
        full_name = (data.get('full_name') or '').strip()
        update_user_profile(users_coll, payload['sub'], full_name=full_name if full_name != '' else None)
    doc = find_user_by_id(users_coll, payload['sub'])
    if not doc:
        return jsonify({'success': False, 'error': 'User not found'}), 404
    user = {
        'id': str(doc['_id']),
        'email': doc.get('email'),
        'full_name': doc.get('full_name', ''),
        'role': doc.get('role', ROLE_USER),
        'created_at': doc.get('created_at'),
        'updated_at': doc.get('updated_at'),
    }
    return jsonify({'success': True, 'user': user}), 200


# Routes
@app.route('/', methods=['GET'])
def home():
    """Home endpoint."""
    return jsonify({
        'message': 'Welcome to Aluminum Products Chatbot API',
        'version': '1.0.0',
        'endpoints': {
            'POST /chat': 'Send a message to the chatbot',
            'POST /upload': 'Upload PDF or image (multipart: file, session_id)',
            'GET /sessions/<session_id>/attachments': 'List attachments for a session',
            'GET /history': 'Get conversation history',
            'POST /clear-history': 'Clear conversation history',
            'GET /stats': 'Get chatbot statistics',
            'GET /products': 'Get all products',
            'GET /health': 'Health check'
        }
    })

@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint."""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'chatbot_initialized': chatbot is not None
    })

@app.route('/chat', methods=['POST'])
def chat():
    """Chat endpoint. If Authorization header present, links messages to user and logs activity."""
    try:
        data = request.get_json()
        
        if not data or 'message' not in data:
            return jsonify({
                'success': False,
                'error': 'No message provided'
            }), 400
        
        user_message = data['message'].strip()
        session_id = data.get('session_id')
        if not user_message:
            return jsonify({
                'success': False,
                'error': 'Empty message'
            }), 400

        payload = _current_user()
        user_id = payload['sub'] if payload else None
        if user_id:
            log_activity(
                _get_logs_coll(),
                user_id=user_id,
                action=ACTION_CHAT,
                resource='chat',
                details={'session_id': session_id},
                ip=request.remote_addr,
            )
        
        response = chatbot.chat(user_message, session_id=session_id, user_id=user_id)
        
        return jsonify(response), 200
    
    except Exception as e:
        logger.error(f"Error in chat endpoint: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/chat/stream', methods=['POST'])
def chat_stream_route():
    """Streaming chat endpoint using Server-Sent Events (SSE)."""
    try:
        data = request.get_json()
        if not data or 'message' not in data:
            return jsonify({'success': False, 'error': 'No message provided'}), 400
        
        user_message = data['message'].strip()
        session_id = data.get('session_id')
        payload = _current_user()
        user_id = payload['sub'] if payload else None

        if user_id:
            log_activity(
                _get_logs_coll(),
                user_id=user_id,
                action=ACTION_CHAT,
                resource='chat/stream',
                details={'session_id': session_id},
                ip=request.remote_addr,
            )

        def generate():
            for chunk in chatbot.chat_stream(user_message, session_id=session_id, user_id=user_id):
                # SSE format: data: <content>\n\n
                import json
                yield f"data: {json.dumps({'chunk': chunk})}\n\n"
            yield "data: [DONE]\n\n"

        return Response(generate(), mimetype='text/event-stream')

    except Exception as e:
        logger.error(f"Error in chat_stream endpoint: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/history', methods=['GET'])
def get_history():
    """Get conversation history."""
    try:
        payload = _current_user()
        user_id = payload['sub'] if payload else None
        session_id = request.args.get('session_id')
        history = chatbot.get_history(session_id=session_id, user_id=user_id)
        return jsonify({
            'success': True,
            'history': history,
            'total_messages': len(history)
        }), 200
    except Exception as e:
        logger.error(f"Error getting history: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/clear-history', methods=['POST'])
def clear_history():
    """Clear conversation history."""
    try:
        chatbot.clear_history()
        return jsonify({
            'success': True,
            'message': 'Conversation history cleared'
        }), 200
    except Exception as e:
        logger.error(f"Error clearing history: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/stats', methods=['GET'])
def get_stats():
    """Get chatbot statistics."""
    try:
        stats = chatbot.get_stats()
        return jsonify({
            'success': True,
            'stats': stats,
            'storage': 'mongo' if chatbot.history_collection is not None else 'memory'
        }), 200
    except Exception as e:
        logger.error(f"Error getting stats: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/sessions', methods=['GET'])
def list_sessions():
    """List chat sessions."""
    try:
        payload = _current_user()
        user_id = payload['sub'] if payload else None
        sessions = chatbot.get_sessions(user_id=user_id)
        return jsonify({
            'success': True,
            'sessions': sessions,
            'total_sessions': len(sessions)
        }), 200
    except Exception as e:
        logger.error(f"Error listing sessions: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/sessions/<string:session_id>', methods=['GET'])
def get_session_history(session_id):
    """Get history for a specific session."""
    try:
        payload = _current_user()
        user_id = payload['sub'] if payload else None
        history = chatbot.get_history(session_id=session_id, user_id=user_id)
        return jsonify({
            'success': True,
            'session_id': session_id,
            'history': history,
            'total_messages': len(history)
        }), 200
    except Exception as e:
        logger.error(f"Error getting session history: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/sessions/<string:session_id>', methods=['DELETE'])
def delete_session(session_id):
    """Delete a specific session and its attachments."""
    try:
        deleted = chatbot.delete_session(session_id)
        if mongo_db is not None:
            delete_attachments_for_session(
                mongo_db,
                app.config.get('MONGO_ATTACHMENTS_COLLECTION', 'chat_attachments'),
                session_id,
            )
        return jsonify({
            'success': True,
            'session_id': session_id,
            'deleted_messages': deleted
        }), 200
    except Exception as e:
        logger.error("Error deleting session: %s", e)
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/jobs', methods=['GET'])
def list_jobs():
    """List all jobs for the current user."""
    try:
        from src.api.jobs import get_jobs
        payload = _current_user()
        user_id = payload['sub'] if payload else None
        jobs_coll = mongo_db['jobs'] if mongo_db is not None else None
        if jobs_coll is None:
            return jsonify({'success': False, 'error': 'Storage unavailable'}), 503
        jobs = get_jobs(jobs_coll, user_id=user_id)
        return jsonify({'success': True, 'jobs': jobs, 'total': len(jobs)}), 200
    except Exception as e:
        logger.error("list_jobs error: %s", e)
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/jobs', methods=['POST'])
def create_job_route():
    """Create a new job."""
    try:
        from src.api.jobs import create_job
        payload = _current_user()
        user_id = payload['sub'] if payload else None
        data = request.get_json() or {}
        jobs_coll = mongo_db['jobs'] if mongo_db is not None else None
        if jobs_coll is None:
            return jsonify({'success': False, 'error': 'Storage unavailable'}), 503
        job = create_job(jobs_coll, data, user_id=user_id)
        return jsonify({'success': True, 'job': job}), 201
    except Exception as e:
        logger.error("create_job error: %s", e)
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/jobs/<string:job_id>', methods=['GET'])
def get_job_route(job_id):
    """Get a single job by ID."""
    try:
        from src.api.jobs import get_job
        jobs_coll = mongo_db['jobs'] if mongo_db is not None else None
        if jobs_coll is None:
            return jsonify({'success': False, 'error': 'Storage unavailable'}), 503
        job = get_job(jobs_coll, job_id)
        if not job:
            return jsonify({'success': False, 'error': 'Job not found'}), 404
        return jsonify({'success': True, 'job': job}), 200
    except Exception as e:
        logger.error("get_job error: %s", e)
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/jobs/<string:job_id>', methods=['PUT'])
def update_job_route(job_id):
    """Update a job."""
    try:
        from src.api.jobs import update_job
        data = request.get_json() or {}
        jobs_coll = mongo_db['jobs'] if mongo_db is not None else None
        if jobs_coll is None:
            return jsonify({'success': False, 'error': 'Storage unavailable'}), 503
        job = update_job(jobs_coll, job_id, data)
        if not job:
            return jsonify({'success': False, 'error': 'Job not found'}), 404
        return jsonify({'success': True, 'job': job}), 200
    except Exception as e:
        logger.error("update_job error: %s", e)
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/jobs/<string:job_id>', methods=['DELETE'])
def delete_job_route(job_id):
    """Delete a job."""
    try:
        from src.api.jobs import delete_job
        jobs_coll = mongo_db['jobs'] if mongo_db is not None else None
        if jobs_coll is None:
            return jsonify({'success': False, 'error': 'Storage unavailable'}), 503
        deleted = delete_job(jobs_coll, job_id)
        return jsonify({'success': True, 'deleted': deleted}), 200
    except Exception as e:
        logger.error("delete_job error: %s", e)
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/jobs/extract-from-pdf', methods=['POST'])
def extract_job_from_pdf():
    """Use the LLM to extract job fields from session PDFs."""
    try:
        data = request.get_json() or {}
        session_id = (data.get('session_id') or '').strip()
        if not session_id or mongo_db is None:
            return jsonify({'success': False, 'error': 'session_id and MongoDB required'}), 400

        # Collect all extracted text from this session's attachments
        attachments = get_attachments_for_session(
            mongo_db,
            app.config.get('MONGO_ATTACHMENTS_COLLECTION', 'chat_attachments'),
            session_id,
        )
        all_text = "\n\n".join(
            att.get('extracted_text', '') for att in attachments if att.get('extracted_text')
        ).strip()

        if not all_text:
            return jsonify({'success': False, 'error': 'No text could be extracted from attached PDFs'}), 422

        # Limit text to avoid huge prompts
        truncated = all_text[:6000]

        ollama_base = getattr(chatbot.config, 'OLLAMA_BASE_URL', 'http://localhost:11434')
        ollama_model = getattr(chatbot.config, 'OLLAMA_MODEL', 'llama3.2')
        use_ollama = getattr(chatbot.config, 'USE_OLLAMA_FOR_DOCUMENTS', False)

        prompt = f"""You are a job intake assistant for an aluminium window/door installation company.
Read the document content below and extract relevant job details.
Return ONLY a valid JSON object with these exact keys (leave empty string if not found):
{{
  "title": "brief job title",
  "client_name": "client full name",
  "client_contact": "email or phone",
  "site_address": "full site address",
  "start_date": "YYYY-MM-DD or empty",
  "end_date": "YYYY-MM-DD or empty",
  "window_door_type": "type of windows/doors",
  "quantity": "number or description",
  "description": "brief job description",
  "notes": "any special notes or requirements"
}}

DOCUMENT CONTENT:
{truncated}

Respond ONLY with the JSON object, no other text."""

        import json as _json
        extracted = {}

        if use_ollama:
            try:
                from src.chatbot.ollama_llm import is_ollama_available
                import urllib.request as _req
                if is_ollama_available(ollama_base):
                    body = {
                        "model": ollama_model,
                        "prompt": prompt,
                        "stream": False,
                        "options": {"temperature": 0.1, "num_predict": 512},
                    }
                    req = _req.Request(
                        f"{ollama_base.rstrip('/')}/api/generate",
                        data=_json.dumps(body).encode(),
                        headers={"Content-Type": "application/json"},
                        method="POST",
                    )
                    with _req.urlopen(req, timeout=60) as resp:
                        raw = _json.loads(resp.read().decode())
                        text = (raw.get("response") or "").strip()
                        # Extract JSON from response
                        import re as _re
                        m = _re.search(r'\{[\s\S]*\}', text)
                        if m:
                            extracted = _json.loads(m.group(0))
            except Exception as ex:
                logger.warning("Ollama extraction failed: %s", ex)

        return jsonify({'success': True, 'fields': extracted}), 200

    except Exception as e:
        logger.error("extract_job_from_pdf error: %s", e)
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/upload-multiple', methods=['POST'])
def upload_multiple_files():
    """Upload multiple PDFs or images for a session."""
    try:
        files = request.files.getlist('files')
        if not files:
            return jsonify({'success': False, 'error': 'No files in request'}), 400

        session_id = request.form.get('session_id', '').strip()
        if not session_id:
            return jsonify({'success': False, 'error': 'session_id is required'}), 400

        if mongo_db is None:
            return jsonify({'success': False, 'error': 'File storage not available'}), 503

        payload = _current_user()
        user_id = payload['sub'] if payload else None
        max_size = app.config.get('MAX_UPLOAD_SIZE', 10 * 1024 * 1024)

        results = []
        errors = []
        for file in files:
            if not file or not file.filename:
                continue
            filename = file.filename
            content_type = file.content_type or content_type_from_filename(filename)
            if not is_allowed_file(filename, content_type):
                errors.append(f"{filename}: file type not allowed")
                continue
            file_bytes = file.read()
            if len(file_bytes) > max_size:
                errors.append(f"{filename}: too large (max {max_size // (1024*1024)} MB)")
                continue
            doc = save_attachment(
                database=mongo_db,
                attachments_collection_name=app.config.get('MONGO_ATTACHMENTS_COLLECTION', 'chat_attachments'),
                session_id=session_id,
                filename=filename,
                content_type=content_type,
                file_bytes=file_bytes,
                user_id=user_id,
            )
            if doc:
                results.append({
                    'id': str(doc['_id']),
                    'filename': doc['filename'],
                    'content_type': doc['content_type'],
                    'extracted_length': len(doc.get('extracted_text', '')),
                })
            else:
                errors.append(f"{filename}: save failed")

        return jsonify({
            'success': True,
            'uploaded': results,
            'errors': errors,
            'total_uploaded': len(results),
        }), 201
    except Exception as e:
        logger.error("upload_multiple error: %s", e)
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/products', methods=['GET'])
def get_products():
    """Get all products."""
    try:
        limit = request.args.get('limit', default=None, type=int)
        category = request.args.get('category', default=None, type=str)
        
        df = data_loader.get_data()
        
        if category:
            df = df[df['category'].str.lower().str.contains(category.lower(), na=False)]
        
        if limit:
            df = df.head(limit)
        
        products = df.to_dict('records')
        
        return jsonify({
            'success': True,
            'total_products': len(products),
            'products': products
        }), 200
    except Exception as e:
        logger.error(f"Error getting products: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/products/<int:product_id>', methods=['GET'])
def get_product(product_id):
    """Get a specific product by ID."""
    try:
        product = data_loader.get_product_by_id(product_id)

        if product is None:
            return jsonify({
                'success': False,
                'error': 'Product not found'
            }), 404

        return jsonify({
            'success': True,
            'product': product
        }), 200
    except Exception as e:
        logger.error(f"Error getting product: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/upload', methods=['POST'])
def upload_file():
    """Upload a PDF or image; store in GridFS and extract text for chat context."""
    try:
        if 'file' not in request.files:
            return jsonify({'success': False, 'error': 'No file in request'}), 400
        file = request.files['file']
        if not file or not file.filename:
            return jsonify({'success': False, 'error': 'No file selected'}), 400

        session_id = request.form.get('session_id', '').strip()
        if not session_id:
            return jsonify({'success': False, 'error': 'session_id is required'}), 400

        filename = file.filename or 'document'
        content_type = file.content_type or content_type_from_filename(filename)
        if not is_allowed_file(filename, content_type):
            return jsonify({
                'success': False,
                'error': 'File type not allowed. Use PDF or image (PNG, JPG, GIF, WebP).'
            }), 400

        file_bytes = file.read()
        max_size = app.config.get('MAX_UPLOAD_SIZE', 10 * 1024 * 1024)
        if len(file_bytes) > max_size:
            return jsonify({
                'success': False,
                'error': f'File too large. Max size: {max_size // (1024 * 1024)} MB'
            }), 400

        if mongo_db is None:
            return jsonify({'success': False, 'error': 'File storage not available (MongoDB required)'}), 503

        payload = _current_user()
        user_id = payload['sub'] if payload else None

        doc = save_attachment(
            database=mongo_db,
            attachments_collection_name=app.config.get('MONGO_ATTACHMENTS_COLLECTION', 'chat_attachments'),
            session_id=session_id,
            filename=filename,
            content_type=content_type,
            file_bytes=file_bytes,
            user_id=user_id,
        )
        if doc is None:
            return jsonify({'success': False, 'error': 'Failed to save attachment'}), 500

        # Return serializable attachment metadata (ObjectId to str)
        return jsonify({
            'success': True,
            'attachment': {
                'id': str(doc['_id']),
                'session_id': doc['session_id'],
                'filename': doc['filename'],
                'content_type': doc['content_type'],
                'extracted_length': len(doc.get('extracted_text', '')),
                'created_at': doc.get('created_at'),
            }
        }), 201
    except Exception as e:
        logger.error("Error in upload: %s", e)
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/sessions/<string:session_id>/attachments', methods=['GET'])
def list_session_attachments(session_id):
    """List attachment metadata for a chat session."""
    try:
        if mongo_db is None:
            return jsonify({'success': False, 'error': 'Attachments not available'}), 503
        attachments = get_attachments_for_session(
            mongo_db,
            app.config.get('MONGO_ATTACHMENTS_COLLECTION', 'chat_attachments'),
            session_id,
        )
        out = []
        for att in attachments:
            out.append({
                'id': str(att['_id']),
                'filename': att.get('filename'),
                'content_type': att.get('content_type'),
                'extracted_length': len(att.get('extracted_text', '')),
                'created_at': att.get('created_at'),
            })
        return jsonify({'success': True, 'attachments': out}), 200
    except Exception as e:
        logger.error("Error listing attachments: %s", e)
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/attachments/<string:attachment_id>', methods=['DELETE'])
def delete_single_attachment(attachment_id):
    """Delete one uploaded attachment (metadata + file)."""
    try:
        if mongo_db is None:
            return jsonify({'success': False, 'error': 'Attachments not available'}), 503
        deleted = delete_attachment(
            mongo_db,
            app.config.get('MONGO_ATTACHMENTS_COLLECTION', 'chat_attachments'),
            attachment_id,
        )
        return jsonify({'success': True, 'deleted': deleted}), 200
    except Exception as e:
        logger.error("Error deleting attachment: %s", e)
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/attachments/<string:attachment_id>/file', methods=['GET'])
def download_attachment_file(attachment_id):
    """Stream a previously uploaded attachment file back to the client."""
    try:
        if mongo_db is None:
            return jsonify({'success': False, 'error': 'Attachments not available'}), 503
        from bson import ObjectId

        coll = mongo_db[app.config.get('MONGO_ATTACHMENTS_COLLECTION', 'chat_attachments')]
        try:
            oid = ObjectId(attachment_id)
        except Exception:
            return jsonify({'success': False, 'error': 'Invalid attachment id'}), 400

        doc = coll.find_one({'_id': oid})
        if not doc:
            return jsonify({'success': False, 'error': 'Attachment not found'}), 404

        file_bytes = get_attachment_file(mongo_db, doc)
        if not file_bytes:
            return jsonify({'success': False, 'error': 'File data missing'}), 404

        return send_file(
            io.BytesIO(file_bytes),
            download_name=doc.get('filename') or 'attachment',
            mimetype=doc.get('content_type') or 'application/octet-stream',
        )
    except Exception as e:
        logger.error("Error streaming attachment: %s", e)
        return jsonify({'success': False, 'error': str(e)}), 500


# ----- Admin routes (require Admin role) -----
@app.route('/admin/users', methods=['GET'])
def admin_list_users():
    """List all users (admin only)."""
    admin, err = _require_admin()
    if err:
        return err
    log_activity(
        _get_logs_coll(),
        user_id=admin['sub'],
        action=ACTION_ADMIN_VIEW_USERS,
        resource='admin/users',
        ip=request.remote_addr,
    )
    users_coll = _get_users_coll()
    if users_coll is None:
        return jsonify({'success': False, 'error': 'Service unavailable'}), 503
    skip = request.args.get('skip', default=0, type=int)
    limit = min(request.args.get('limit', default=100, type=int), 200)
    users = list_users(users_coll, skip=skip, limit=limit)
    return jsonify({'success': True, 'users': users, 'total': len(users)}), 200


@app.route('/admin/users/<string:user_id>', methods=['GET'])
def admin_get_user(user_id):
    """Get one user profile (admin only)."""
    admin, err = _require_admin()
    if err:
        return err
    log_activity(
        _get_logs_coll(),
        user_id=admin['sub'],
        action=ACTION_ADMIN_VIEW_USER,
        resource=f'admin/users/{user_id}',
        details={'target_user_id': user_id},
        ip=request.remote_addr,
    )
    users_coll = _get_users_coll()
    if users_coll is None:
        return jsonify({'success': False, 'error': 'Service unavailable'}), 503
    doc = find_user_by_id(users_coll, user_id)
    if not doc:
        return jsonify({'success': False, 'error': 'User not found'}), 404
    user = {
        'id': str(doc['_id']),
        'email': doc.get('email'),
        'full_name': doc.get('full_name', ''),
        'role': doc.get('role', ROLE_USER),
        'created_at': doc.get('created_at'),
        'updated_at': doc.get('updated_at'),
    }
    return jsonify({'success': True, 'user': user}), 200


@app.route('/admin/users/<string:user_id>', methods=['PUT'])
def admin_update_user(user_id):
    """Update user (role and/or full_name) (admin only)."""
    admin, err = _require_admin()
    if err:
        return err
    users_coll = _get_users_coll()
    if users_coll is None:
        return jsonify({'success': False, 'error': 'Service unavailable'}), 503
    data = request.get_json() or {}
    full_name = data.get('full_name')
    if full_name is not None:
        update_user_profile(users_coll, user_id, full_name=(full_name or '').strip())
    role = data.get('role')
    if role is not None and role in (ROLE_USER, ROLE_ADMIN):
        set_user_role(users_coll, user_id, role)
    log_activity(
        _get_logs_coll(),
        user_id=admin['sub'],
        action=ACTION_ADMIN_UPDATE_USER,
        resource=f'admin/users/{user_id}',
        details={'target_user_id': user_id, 'updates': data},
        ip=request.remote_addr,
    )
    doc = find_user_by_id(users_coll, user_id)
    if not doc:
        return jsonify({'success': False, 'error': 'User not found'}), 404
    user = {
        'id': str(doc['_id']),
        'email': doc.get('email'),
        'full_name': doc.get('full_name', ''),
        'role': doc.get('role', ROLE_USER),
        'created_at': doc.get('created_at'),
        'updated_at': doc.get('updated_at'),
    }
    return jsonify({'success': True, 'user': user}), 200


@app.route('/admin/users/<string:user_id>/sessions', methods=['GET'])
def admin_user_sessions(user_id):
    """List chat sessions for a user (admin only)."""
    admin, err = _require_admin()
    if err:
        return err
    log_activity(
        _get_logs_coll(),
        user_id=admin['sub'],
        action=ACTION_ADMIN_VIEW_HISTORY,
        resource=f'admin/users/{user_id}/sessions',
        details={'target_user_id': user_id},
        ip=request.remote_addr,
    )
    sessions = chatbot.get_sessions(user_id=user_id)
    return jsonify({'success': True, 'sessions': sessions, 'user_id': user_id}), 200


@app.route('/admin/users/<string:user_id>/sessions/<string:session_id>', methods=['GET'])
def admin_user_session_history(user_id, session_id):
    """Get chat history for a user's session (admin only)."""
    admin, err = _require_admin()
    if err:
        return err
    log_activity(
        _get_logs_coll(),
        user_id=admin['sub'],
        action=ACTION_ADMIN_VIEW_HISTORY,
        resource=f'admin/users/{user_id}/sessions/{session_id}',
        details={'target_user_id': user_id, 'session_id': session_id},
        ip=request.remote_addr,
    )
    history = chatbot.get_history(session_id=session_id, user_id=user_id)
    return jsonify({
        'success': True,
        'session_id': session_id,
        'user_id': user_id,
        'history': history,
        'total_messages': len(history),
    }), 200


@app.route('/admin/activity-logs', methods=['GET'])
def admin_activity_logs():
    """Get activity logs for monitoring (admin only)."""
    admin, err = _require_admin()
    if err:
        return err
    log_activity(
        _get_logs_coll(),
        user_id=admin['sub'],
        action=ACTION_ADMIN_VIEW_LOGS,
        resource='admin/activity-logs',
        ip=request.remote_addr,
    )
    logs_coll = _get_logs_coll()
    if logs_coll is None:
        return jsonify({'success': True, 'logs': [], 'total': 0}), 200
    user_id_filter = request.args.get('user_id')
    action_filter = request.args.get('action')
    skip = request.args.get('skip', default=0, type=int)
    limit = min(request.args.get('limit', default=100, type=int), 500)
    logs = get_activity_logs(logs_coll, user_id=user_id_filter, action=action_filter, skip=skip, limit=limit)
    return jsonify({'success': True, 'logs': logs, 'total': len(logs)}), 200


# ----- Duplicate routes under /api so proxy can send either /api/* or rewritten path -----
def _add_api_routes():
    """Register same views under /api prefix for frontend proxy compatibility."""
    app.add_url_rule('/api/auth/register', view_func=register, methods=['POST'])
    app.add_url_rule('/api/auth/login', view_func=login, methods=['POST'])
    app.add_url_rule('/api/auth/logout', view_func=logout, methods=['POST'])
    app.add_url_rule('/api/me', view_func=me, methods=['GET', 'PUT'])
    app.add_url_rule('/api/health', view_func=health, methods=['GET'])
    app.add_url_rule('/api/chat', view_func=chat, methods=['POST'])
    app.add_url_rule('/api/history', view_func=get_history, methods=['GET'])
    app.add_url_rule('/api/clear-history', view_func=clear_history, methods=['POST'])
    app.add_url_rule('/api/stats', view_func=get_stats, methods=['GET'])
    app.add_url_rule('/api/sessions', view_func=list_sessions, methods=['GET'])
    app.add_url_rule('/api/sessions/<string:session_id>', view_func=get_session_history, methods=['GET'])
    app.add_url_rule('/api/sessions/<string:session_id>', view_func=delete_session, methods=['DELETE'])
    app.add_url_rule('/api/products', view_func=get_products, methods=['GET'])
    app.add_url_rule('/api/products/<int:product_id>', view_func=get_product, methods=['GET'])
    app.add_url_rule('/api/upload', view_func=upload_file, methods=['POST'])
    app.add_url_rule('/api/sessions/<string:session_id>/attachments', view_func=list_session_attachments, methods=['GET'])
    app.add_url_rule('/api/attachments/<string:attachment_id>', view_func=delete_single_attachment, methods=['DELETE'])
    app.add_url_rule('/api/attachments/<string:attachment_id>/file', view_func=download_attachment_file, methods=['GET'])
    app.add_url_rule('/api/admin/users', view_func=admin_list_users, methods=['GET'])
    app.add_url_rule('/api/admin/users/<string:user_id>', view_func=admin_get_user, methods=['GET'])
    app.add_url_rule('/api/admin/users/<string:user_id>', view_func=admin_update_user, methods=['PUT'])
    app.add_url_rule('/api/admin/users/<string:user_id>/sessions', view_func=admin_user_sessions, methods=['GET'])
    app.add_url_rule('/api/admin/users/<string:user_id>/sessions/<string:session_id>', view_func=admin_user_session_history, methods=['GET'])
    app.add_url_rule('/api/admin/activity-logs', view_func=admin_activity_logs, methods=['GET'])


_add_api_routes()


@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors."""
    path = request.path or request.environ.get('PATH_INFO', '')
    method = request.method
    print(f">>> 404 {method} {path!r} (no matching route)", flush=True)
    logger.warning("404 not found: %s %s", method, path)
    return jsonify({
        'success': False,
        'error': 'Endpoint not found'
    }), 404

@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors."""
    return jsonify({
        'success': False,
        'error': 'Internal server error'
    }), 500

if __name__ == '__main__':
    app.run(
        debug=app.config['DEBUG'],
        host='0.0.0.0',
        port=5000,
        use_reloader=False, # Set to False for Windows stability with SSE
    )
