import logging
import sys
import os
from flask import Flask, jsonify
from flask_cors import CORS
from dotenv import load_dotenv

# Ensure 'src' is in the Python path regardless of how the script is run
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from src.config import Config

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def create_app():
    """Create and configure the Flask application."""
    app = Flask(__name__)
    
    # Configure CORS - allow specific origins or all (*)
    CORS(app, resources={
        r"/*": {
            "origins": Config.CORS_ORIGINS,
            "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
            "allow_headers": ["Content-Type", "Authorization"]
        }
    })

    from .routes.auth import auth_bp
    from .routes.users import users_bp
    from .routes.chat import chat_bp
    from .routes.logs import logs_bp
    from .routes.chatbot import chatbot_bp
    from .routes.knowledge import knowledge_bp
    from .routes.jobs import jobs_bp
    from .routes.health import health_bp

    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(users_bp, url_prefix='/users')
    app.register_blueprint(chat_bp, url_prefix='/chat')
    app.register_blueprint(logs_bp, url_prefix='/logs')
    app.register_blueprint(chatbot_bp, url_prefix='/admin-bot')
    app.register_blueprint(knowledge_bp, url_prefix='/knowledge')
    app.register_blueprint(jobs_bp, url_prefix='/jobs')
    app.register_blueprint(health_bp, url_prefix='/health')

    return app

if __name__ == '__main__':
    app = create_app()
    port = int(os.environ.get('PORT', 5001))
    # Run on 0.0.0.0 to allow external connections (like Docker or local network)
    logger.info(f"Starting development server on port {port}")
    app.run(host='0.0.0.0', port=port, debug=True)
