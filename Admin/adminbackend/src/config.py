import os

class Config:
    """Application configuration."""
    
    # MongoDB settings
    MONGO_URI = os.getenv("MONGO_URI", "mongodb+srv://priyathg45:gen%40chatbot123@cluster0.fg7ph9d.mongodb.net/")
    MONGO_DB = os.getenv("MONGO_DB", "chatbot")
    
    # Security
    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "your-secret-key-here")
    
    # CORS
    CORS_ORIGINS = os.getenv("CORS_ORIGINS", "*").split(",")
    
    # Admin Settings
    ADMIN_USERNAME = os.getenv("ADMIN_USERNAME", "admin")
    ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "admin123")

    MONGO_ACTIVITY_LOGS_COLLECTION = 'activity_logs'
    MONGO_ADMIN_HISTORY_COLLECTION = 'admin_chat_history'
    
    # Ollama Settings
    OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama4-scout")
    OLLAMA_VISION_MODEL = os.getenv("OLLAMA_VISION_MODEL", "moondream")
    USE_VISION_LLM_FOR_EXTRACTION = os.getenv("USE_VISION_LLM_FOR_EXTRACTION", "true").lower() == "true"

