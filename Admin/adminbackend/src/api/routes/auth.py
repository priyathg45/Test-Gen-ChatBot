"""Authentication routes for admin."""
import datetime
import logging
import jwt
from flask import Blueprint, request, jsonify
from passlib.hash import bcrypt

from src.config import Config
from src.utils.mongo import get_collection

logger = logging.getLogger(__name__)

auth_bp = Blueprint('auth', __name__)

def verify_token(token: str) -> dict:
    """Verify JWT token."""
    try:
        payload = jwt.decode(token, Config.JWT_SECRET_KEY, algorithms=["HS256"])
        return payload
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None

@auth_bp.route('/login', methods=['POST'])
def login():
    """Admin login endpoint."""
    try:
        data = request.get_json()
        if not data or 'username' not in data or 'password' not in data:
            return jsonify({"error": "Missing username or password"}), 400

        username = data['username']
        password = data['password']

        admins_collection = get_collection(Config.MONGO_URI, Config.MONGO_DB, "admins")
        
        # In a real app we'd verify against DB. For now, we optionally verify 
        # against env config OR DB. Let's start with Config for fallback:
        admin_user = None
        if admins_collection is not None:
            admin_user = admins_collection.find_one({"username": username})

        if admin_user:
            # check db user
            if not bcrypt.verify(password, admin_user['password']):
                return jsonify({"error": "Invalid credentials"}), 401
        else:
            # check config user
            if username != Config.ADMIN_USERNAME or password != Config.ADMIN_PASSWORD:
                return jsonify({"error": "Invalid credentials"}), 401
                
            # If Config user matched, optionally seed DB or just proceed
            if admins_collection is not None:
                # Store the default admin for future
                try:
                    hashed = bcrypt.hash(password)
                    admins_collection.insert_one({
                        "username": username,
                        "password": hashed,
                        "role": "superadmin"
                    })
                except Exception as e:
                    logger.warning(f"Could not seed admin user to db: {e}")

        # Create JWT token
        expiration = datetime.datetime.utcnow() + datetime.timedelta(hours=24)
        token = jwt.encode(
            {
                "username": username,
                "role": "admin",
                "exp": expiration
            },
            Config.JWT_SECRET_KEY,
            algorithm="HS256"
        )

        return jsonify({
            "token": token,
            "username": username,
            "expires_in": 24 * 3600
        }), 200

    except Exception as e:
        logger.error(f"Login error: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500

@auth_bp.route('/me', methods=['GET'])
def get_me():
    """Get current admin context with full details."""
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        return jsonify({"error": "Missing authorization"}), 401
    
    token = auth_header.split(" ")[1]
    payload = verify_token(token)
    if not payload:
        return jsonify({"error": "Invalid or expired token"}), 401
    
    username = payload["username"]
    admins_collection = get_collection(Config.MONGO_URI, Config.MONGO_DB, "admins")
    
    admin_data = {"username": username, "role": payload.get("role", "admin")}
    
    if admins_collection is not None:
        db_user = admins_collection.find_one({"username": username}, {"password": 0})
        if db_user:
            db_user["_id"] = str(db_user["_id"])
            admin_data = db_user

    return jsonify(admin_data), 200

@auth_bp.route('/profile', methods=['PUT'])
def update_profile():
    """Update current admin profile details."""
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        return jsonify({"error": "Missing authorization"}), 401
    
    token = auth_header.split(" ")[1]
    payload = verify_token(token)
    if not payload:
        return jsonify({"error": "Invalid or expired token"}), 401
        
    username = payload["username"]
    data = request.get_json()
    if not data:
        return jsonify({"error": "No data provided"}), 400
        
    # Allowed fields to update
    allowed_fields = ["full_name", "email", "phone", "bio"]
    updates = {k: v for k, v in data.items() if k in allowed_fields}
    
    if not updates:
        return jsonify({"error": "No valid fields to update"}), 400
        
    admins_collection = get_collection(Config.MONGO_URI, Config.MONGO_DB, "admins")
    if admins_collection is None:
        return jsonify({"error": "Database connection error"}), 500
        
    result = admins_collection.update_one(
        {"username": username},
        {"$set": updates}
    )
    
    if result.matched_count == 0:
        return jsonify({"error": "Admin user not found in database"}), 404
        
    return jsonify({"success": True, "message": "Profile updated successfully"}), 200
