"""Admin chatbot routes."""
import logging
from flask import Blueprint, request, jsonify

from .auth import verify_token

logger = logging.getLogger(__name__)

chatbot_bp = Blueprint('chatbot', __name__)

def check_admin_auth():
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        return False
    token = auth_header.split(" ")[1]
    return verify_token(token) is not None

@chatbot_bp.route('/ask', methods=['POST'])
def ask_admin_bot():
    """Endpoint for admin chatbot queries."""
    if not check_admin_auth():
        return jsonify({"error": "Unauthorized"}), 401

    try:
        data = request.get_json()
        if not data or 'message' not in data:
            return jsonify({"error": "Missing message"}), 400

        user_message = data['message']
        
        # Here we could integrate with an LLM focused on admin tasks.
        # For now, we will provide a mocked functional response.
        bot_response = f"Admin Bot: I received your query about '{user_message}'. Currently, I am a placeholder for admin operational tasks."
        
        # Add basic logic to simulate checking system status
        if "status" in user_message.lower() or "health" in user_message.lower():
            bot_response = "Admin Bot: All backend systems and MongoDB clusters are operating normally. Total active users today: 5."
        elif "users" in user_message.lower():
            bot_response = "Admin Bot: You can manage users in the 'Users' tab of the dashboard."

        return jsonify({
            "response": bot_response
        }), 200

    except Exception as e:
        logger.error(f"Error in admin chatbot: {str(e)}")
        return jsonify({"error": "Failed to process query"}), 500
