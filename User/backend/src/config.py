"""Configuration module for the chatbot application."""
import os
from dotenv import load_dotenv  # type: ignore[import-untyped]

# Load environment variables from .env file
load_dotenv()

class Config:
    """Base configuration."""
    
    # Flask settings
    DEBUG = os.getenv('FLASK_DEBUG', False)
    TESTING = False
    # Eagerly initialize chatbot (load data, embeddings, Mongo) on process start instead of first request
    EAGER_INIT = os.getenv('EAGER_INIT', 'true').lower() == 'true'
    
    # Data settings
    DATA_PATH = os.getenv('DATA_PATH', 'data/aluminum_products.csv')
    # When set, prefer loading aluminum_products_preprocessed.csv for embeddings (more accurate)
    PREFER_PREPROCESSED_CSV = os.getenv('PREFER_PREPROCESSED_CSV', 'true').lower() == 'true'

    # Database / Mongo settings
    # Default to provided Atlas cluster if no env override is supplied.
    DEFAULT_MONGO_URI = os.getenv(
        'MONGO_URI',
        'mongodb+srv://priyathg45:gen%40chatbot123@cluster0.fg7ph9d.mongodb.net/',
    )
    _raw_use_mongo = os.getenv('USE_MONGO')
    # Auto-enable Mongo when a URI is provided unless explicitly disabled via USE_MONGO=false
    USE_MONGO = (_raw_use_mongo.lower() == 'true') if _raw_use_mongo else bool(DEFAULT_MONGO_URI)
    MONGO_URI = DEFAULT_MONGO_URI
    MONGO_DB = os.getenv('MONGO_DB', 'chatbot')
    MONGO_PRODUCTS_COLLECTION = os.getenv('MONGO_PRODUCTS_COLLECTION', 'products')
    MONGO_HISTORY_COLLECTION = os.getenv('MONGO_HISTORY_COLLECTION', 'history')
    MONGO_ATTACHMENTS_COLLECTION = os.getenv('MONGO_ATTACHMENTS_COLLECTION', 'chat_attachments')
    MONGO_USERS_COLLECTION = os.getenv('MONGO_USERS_COLLECTION', 'users')
    MONGO_ACTIVITY_LOGS_COLLECTION = os.getenv('MONGO_ACTIVITY_LOGS_COLLECTION', 'activity_logs')
    # Max size for uploaded files (bytes) – 10 MB
    MAX_UPLOAD_SIZE = int(os.getenv('MAX_UPLOAD_SIZE', 10 * 1024 * 1024))
    # SRV URIs require TLS; allow override via env
    _default_tls = 'true' if DEFAULT_MONGO_URI.startswith('mongodb+srv://') else 'false'
    MONGO_TLS = os.getenv('MONGO_TLS', _default_tls).lower() == 'true'
    MONGO_REPLICA_SET = os.getenv('MONGO_REPLICA_SET')
    MONGO_APP_NAME = os.getenv('MONGO_APP_NAME', 'genesis-chatbot')
    MONGO_CONNECT_TIMEOUT_MS = int(os.getenv('MONGO_CONNECT_TIMEOUT_MS', 5000))
    MONGO_COMPRESSORS = os.getenv('MONGO_COMPRESSORS')

    # Normalized client kwargs passed to pymongo
    _mongo_kwargs = {
        'serverSelectionTimeoutMS': MONGO_CONNECT_TIMEOUT_MS,
        'appname': MONGO_APP_NAME,
    }
    if MONGO_TLS:
        _mongo_kwargs['tls'] = True
    if MONGO_REPLICA_SET:
        _mongo_kwargs['replicaSet'] = MONGO_REPLICA_SET
    if MONGO_COMPRESSORS:
        _mongo_kwargs['compressors'] = MONGO_COMPRESSORS
    MONGO_CLIENT_KWARGS = _mongo_kwargs
    
    # Model settings (semantic search / embeddings)
    # Default to a higher-accuracy model than all-MiniLM-L6-v2.
    # You can override via MODEL_NAME env if needed.
    MODEL_NAME = os.getenv('MODEL_NAME', 'all-mpnet-base-v2')
    TOP_K_RESULTS = int(os.getenv('TOP_K_RESULTS', 3))
    SIMILARITY_THRESHOLD = float(os.getenv('SIMILARITY_THRESHOLD', 0.3))
    
    # Local LLM settings (for answer generation, optional)
    # Disabled by default so document QA returns quickly using extracted text (CPU-friendly).
    # Set to 'true' to use local model (slow on CPU; use GPU or Ollama for better speed).
    LOCAL_LLM_ENABLED = os.getenv('LOCAL_LLM_ENABLED', 'false').lower() == 'true'
    # Example: "Qwen/Qwen2.5-3B-Instruct" or "meta-llama/Llama-3.1-8B-Instruct"
    LOCAL_LLM_MODEL_NAME = os.getenv('LOCAL_LLM_MODEL_NAME', 'Qwen/Qwen2.5-3B-Instruct')
    # Use 'cpu' to force CPU; 'cuda' for GPU; 'auto' picks best available.
    LOCAL_LLM_DEVICE = os.getenv('LOCAL_LLM_DEVICE', 'cpu')
    LOCAL_LLM_MAX_NEW_TOKENS = int(os.getenv('LOCAL_LLM_MAX_NEW_TOKENS', 256))
    LOCAL_LLM_TEMPERATURE = float(os.getenv('LOCAL_LLM_TEMPERATURE', 0.2))
    
    # API settings
    CORS_ORIGINS = ["*"]
    JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY', 'change-me-in-production-use-long-random-string')
    JWT_ACCESS_EXPIRES_HOURS = float(os.getenv('JWT_ACCESS_EXPIRES_HOURS', 24))
    # Optional: set to create first admin user on startup if no admin exists
    INIT_ADMIN_EMAIL = os.getenv('INIT_ADMIN_EMAIL', '')
    INIT_ADMIN_PASSWORD = os.getenv('INIT_ADMIN_PASSWORD', '')
    
    # Chat settings
    MAX_CHAT_HISTORY = 10
    MAX_TOKENS_IN_CONTEXT = 2000
    TEMPERATURE = 0.7
    # Document RAG (uploaded PDFs/images) – smaller/fewer chunks = faster on CPU
    DOC_CHUNK_SIZE = int(os.getenv('DOC_CHUNK_SIZE', 400))
    DOC_CHUNK_OVERLAP = int(os.getenv('DOC_CHUNK_OVERLAP', 50))
    TOP_K_DOC_CHUNKS = int(os.getenv('TOP_K_DOC_CHUNKS', 6))
    # PDF extraction limits to avoid UI hangs
    DOC_MAX_PAGES = int(os.getenv('DOC_MAX_PAGES', 50))
    DOC_PDF_TIMEOUT = int(os.getenv('DOC_PDF_TIMEOUT', 20))
    # If text extraction yields fewer than this many chars, try OCR (scanned PDFs)
    PDF_MIN_TEXT_CHARS = int(os.getenv('PDF_MIN_TEXT_CHARS', 100))
    PDF_OCR_MAX_PAGES = int(os.getenv('PDF_OCR_MAX_PAGES', 50))

    # Ollama (local LLM server) for document QA. Default false = use fast template from extracted text (CPU-friendly).
    # Set true only if Ollama is running (e.g. ollama run llama3.2) for LLM-powered document answers.
    USE_OLLAMA_FOR_DOCUMENTS = os.getenv('USE_OLLAMA_FOR_DOCUMENTS', 'false').lower() == 'true'
    OLLAMA_BASE_URL = os.getenv('OLLAMA_BASE_URL', 'http://localhost:11434')
    OLLAMA_MODEL = os.getenv('OLLAMA_MODEL', 'llama3.2')
    # Max tokens for document summaries/answers when using Ollama/local LLM (lower = faster on CPU)
    DOC_LLM_MAX_TOKENS = int(os.getenv('DOC_LLM_MAX_TOKENS', 512))

class DevelopmentConfig(Config):
    """Development configuration."""
    DEBUG = True
    TESTING = False

class TestingConfig(Config):
    """Testing configuration."""
    DEBUG = True
    TESTING = True

class ProductionConfig(Config):
    """Production configuration."""
    DEBUG = False
    TESTING = False

# Select configuration based on environment
config = DevelopmentConfig()
