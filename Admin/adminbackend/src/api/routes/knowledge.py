import logging
import os
import uuid
from flask import Blueprint, request, jsonify
from datetime import datetime
from bson import ObjectId

from src.config import Config
from src.utils.mongo import get_collection
from .auth import verify_token
# Reusing extraction logic from chatbot.py if possible, or implementing local version
try:
    from .chatbot import extract_content_with_vision_llm, _col as chatbot_col
except ImportError:
    pass

logger = logging.getLogger(__name__)

knowledge_bp = Blueprint('knowledge', __name__)

def check_admin_auth():
    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        return False
    token = auth_header.split(" ", 1)[1]
    return verify_token(token) is not None

def _col():
    return get_collection(Config.MONGO_URI, Config.MONGO_DB, Config.MONGO_KNOWLEDGE_COLLECTION)

def chunk_text(text, chunk_size=500, overlap=50):
    """
    Granular text chunker. Splits by double newlines (paragraphs) 
    first to keep context together, then by chunk_size if needed.
    """
    if not text:
        return []
        
    # Standard split by paragraphs (like free-chatbot-main)
    raw_paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
    
    final_chunks = []
    for p in raw_paragraphs:
        if len(p) <= chunk_size * 1.5: # Allow slightly larger if it's one paragraph
            final_chunks.append(p)
        else:
            # Fallback to character splitting for very long paragraphs
            start = 0
            while start < len(p):
                end = start + chunk_size
                final_chunks.append(p[start:end])
                start += (chunk_size - overlap)
                
    return [c for c in final_chunks if len(c) > 20] # Filter garbage short ones

@knowledge_bp.route('/upload', methods=['POST'])
def upload_knowledge_pdf():
    if not check_admin_auth():
        return jsonify({"success": False, "error": "Unauthorized"}), 401
    
    if 'file' not in request.files:
        return jsonify({"success": False, "error": "No file part"}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({"success": False, "error": "No selected file"}), 400

    try:
        filename = file.filename
        file_bytes = file.read()
        
        # Extract text - we'll use a simplified version of the chatbot extraction logic here
        # to avoid circular imports or complex dependencies for now.
        extracted_text = ""
        
        # Check if it's a PDF
        if filename.lower().endswith('.pdf'):
            import fitz # PyMuPDF
            doc = fitz.open(stream=file_bytes, filetype="pdf")
            for page_num, page in enumerate(doc):
                page_text = page.get_text()
                if page_text.strip():
                    extracted_text += f"\n[PAGE_{page_num + 1}]\n{page_text}"
            doc.close()
        elif filename.lower().endswith(('.png', '.jpg', '.jpeg')):
            # For images, we would normally use OCR or Vision LLM
            # For now, let's stick to PDF as per the primary request
            pass
        else:
            # Assume text/plain
            extracted_text = file_bytes.decode('utf-8', errors='ignore')

        if not extracted_text.strip():
            return jsonify({"success": False, "error": "Could not extract text from file"}), 400

        # Chunk the text
        chunks = chunk_text(extracted_text)
        
        # Save to MongoDB
        coll = _col()
        doc_id = str(uuid.uuid4())
        
        chunk_docs = []
        for i, chunk_content in enumerate(chunks, 1): # Changed 'content' to 'chunk_content' for clarity
            chunk_docs.append({
                "document_id": doc_id,
                "filename": filename,
                "content": chunk_content,
                "chunk_index": i,
                "total_chunks": len(chunks), # Added total_chunks
                "created_at": datetime.now(),
                "metadata": {
                    "source": filename,
                    "type": "global_knowledge"
                }
            })
        
        if chunk_docs:
            coll.insert_many(chunk_docs)
            
        return jsonify({
            "success": True, 
            "message": f"Uploaded and indexed {len(chunks)} chunks from {filename}",
            "document_id": doc_id,
            "chunks_count": len(chunks)
        }), 200

    except Exception as e:
        logger.error(f"Error in knowledge upload: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 500

@knowledge_bp.route('/chunks', methods=['GET'])
def get_knowledge_chunks():
    if not check_admin_auth():
        return jsonify({"success": False, "error": "Unauthorized"}), 401
    
    try:
        coll = _col()
        # Return unique documents (by filename) or all chunks? 
        # User asked for "Document Catalogs same as the free-chatbot-main project Product catalog feature"
        # Product catalog shows all products. So we'll show all chunks or unique documents?
        # Let's show all chunks but grouped by filename in frontend.
        cursor = coll.find().sort("created_at", -1)
        chunks = []
        for doc in cursor:
            doc["_id"] = str(doc["_id"])
            if "created_at" in doc:
                doc["created_at"] = doc["created_at"].isoformat()
            chunks.append(doc)
            
        return jsonify({"success": True, "chunks": chunks}), 200
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@knowledge_bp.route('/chunks/<chunk_id>', methods=['DELETE'])
def delete_chunk(chunk_id):
    if not check_admin_auth():
        return jsonify({"success": False, "error": "Unauthorized"}), 401
    
    try:
        coll = _col()
        result = coll.delete_one({"_id": ObjectId(chunk_id)})
        if result.deleted_count:
            return jsonify({"success": True, "message": "Chunk deleted"}), 200
        return jsonify({"success": False, "error": "Chunk not found"}), 404
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@knowledge_bp.route('/documents/<document_id>', methods=['DELETE'])
def delete_document(document_id):
    if not check_admin_auth():
        return jsonify({"success": False, "error": "Unauthorized"}), 401
    
    try:
        coll = _col()
        result = coll.delete_many({"document_id": document_id})
        return jsonify({"success": True, "message": f"Deleted {result.deleted_count} chunks"}), 200
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500
