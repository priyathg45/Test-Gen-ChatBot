"""Store and retrieve chat attachments (PDFs, images) in MongoDB with GridFS."""
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from gridfs import GridFS
from pymongo import ASCENDING
from pymongo.database import Database

from src.document.processor import (
    chunk_text,
    extract_text_from_image,
    extract_text_from_pdf,
)

logger = logging.getLogger(__name__)

# Allowed MIME types / extensions
ALLOWED_EXTENSIONS = {"pdf", "png", "jpg", "jpeg", "gif", "webp"}
ALLOWED_CONTENT_TYPES = {
    "application/pdf",
    "image/png",
    "image/jpeg",
    "image/gif",
    "image/webp",
}


def get_gridfs_bucket(database: Database, bucket_name: str = "attachments") -> GridFS:
    """Return a GridFS bucket for the given database."""
    return GridFS(database, bucket_name)


def ensure_attachments_indexes(collection):
    """Create indexes on the attachments metadata collection."""
    try:
        collection.create_index([("session_id", ASCENDING), ("created_at", ASCENDING)], background=True)
        collection.create_index("session_id", background=True)
    except Exception:
        pass


def save_attachment(
    *,
    database: Database,
    attachments_collection_name: str,
    session_id: str,
    filename: str,
    content_type: str,
    file_bytes: bytes,
    user_id: Optional[str] = None,
) -> Optional[Dict[str, Any]]:
    """
    Save a file to GridFS and store metadata (including extracted text) in the attachments collection.
    Text is extracted at upload time so the chatbot can read document content immediately.


    Returns:
        Document with _id, session_id, filename, content_type, file_id (GridFS), extracted_text, created_at
        or None on failure.
    """
    try:
        fs = get_gridfs_bucket(database)
        # Store file in GridFS first
        file_id = fs.put(file_bytes, filename=filename, content_type=content_type)

        # Extract text at upload time so chatbot can read PDF/image content
        extracted_text = ""
        ctype = (content_type or "").lower()
        try:
            if ctype == "application/pdf":
                extracted_text = extract_text_from_pdf(
                    file_bytes,
                    filename,
                    timeout=60,
                    max_pages=200,
                )
            elif ctype.startswith("image/"):
                extracted_text = extract_text_from_image(file_bytes, filename)
        except Exception as e:
            logger.warning("Text extraction failed for %s: %s", filename, e)

        attachments_coll = database[attachments_collection_name]
        ensure_attachments_indexes(attachments_coll)

        doc = {
            "session_id": session_id,
            "filename": filename,
            "content_type": content_type,
            "file_id": file_id,
            "extracted_text": extracted_text or "",
            "created_at": datetime.utcnow().isoformat(),
        }
        if user_id:
            doc["user_id"] = user_id
            
        result = attachments_coll.insert_one(doc)
        doc["_id"] = result.inserted_id
        logger.info(
            "Saved attachment %s for session %s (extracted %d chars)",
            filename,
            session_id,
            len(extracted_text),
        )
        return doc
    except Exception as e:
        logger.error("Failed to save attachment %s: %s", filename, e)
        return None


def get_attachments_for_session(
    database: Database,
    attachments_collection_name: str,
    session_id: str,
) -> List[Dict[str, Any]]:
    """
    Return attachment metadata (including extracted_text) for a session.
    Does not load file binary from GridFS.
    """
    try:
        coll = database[attachments_collection_name]
        cursor = coll.find({"session_id": session_id}).sort("created_at", ASCENDING)
        return list(cursor)
    except Exception as e:
        logger.error("Failed to get attachments for session %s: %s", session_id, e)
        return []


def get_attachment_file(
    database: Database,
    attachment_doc: Dict[str, Any],
    bucket_name: str = "attachments",
) -> Optional[bytes]:
    """Load raw file bytes from GridFS for an attachment document."""
    try:
        fs = get_gridfs_bucket(database, bucket_name)
        file_id = attachment_doc.get("file_id")
        if file_id is None:
            return None
        grid_out = fs.get(file_id)
        return grid_out.read()
    except Exception as e:
        logger.error("Failed to get file for attachment: %s", e)
        return None


def content_type_from_filename(filename: str) -> str:
    """Infer content type from filename extension."""
    ext = (filename or "").split(".")[-1].lower()
    mapping = {
        "pdf": "application/pdf",
        "png": "image/png",
        "jpg": "image/jpeg",
        "jpeg": "image/jpeg",
        "gif": "image/gif",
        "webp": "image/webp",
    }
    return mapping.get(ext, "application/octet-stream")


def is_allowed_file(filename: str, content_type: Optional[str] = None) -> bool:
    """Check if file type is allowed for upload."""
    ext = (filename or "").split(".")[-1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        return False
    if content_type and content_type.lower() not in ALLOWED_CONTENT_TYPES:
        return False
    return True


def delete_attachments_for_session(
    database: Database,
    attachments_collection_name: str,
    session_id: str,
    bucket_name: str = "attachments",
) -> int:
    """Delete all attachments for a session (metadata and GridFS files). Returns count deleted."""
    try:
        coll = database[attachments_collection_name]
        attachments = list(coll.find({"session_id": session_id}))
        if not attachments:
            return 0
        fs = get_gridfs_bucket(database, bucket_name)
        for att in attachments:
            file_id = att.get("file_id")
            if file_id is not None:
                try:
                    fs.delete(file_id)
                except Exception as e:
                    logger.warning("Could not delete GridFS file %s: %s", file_id, e)
        result = coll.delete_many({"session_id": session_id})
        logger.info("Deleted %d attachments for session %s", result.deleted_count, session_id)
        return result.deleted_count
    except Exception as e:
        logger.error("Failed to delete attachments for session %s: %s", session_id, e)
        return 0


def delete_attachment(
    database: Database,
    attachments_collection_name: str,
    attachment_id,
    bucket_name: str = "attachments",
) -> int:
    """Delete a single attachment (metadata + GridFS file). Returns 1 if deleted, 0 otherwise."""
    from bson import ObjectId

    try:
        coll = database[attachments_collection_name]
        try:
            oid = ObjectId(attachment_id)
        except Exception:
            logger.error("Invalid attachment id: %s", attachment_id)
            return 0

        doc = coll.find_one({"_id": oid})
        if not doc:
            return 0

        fs = get_gridfs_bucket(database, bucket_name)
        file_id = doc.get("file_id")
        if file_id is not None:
            try:
                fs.delete(file_id)
            except Exception as e:
                logger.warning("Could not delete GridFS file %s: %s", file_id, e)

        result = coll.delete_one({"_id": oid})
        logger.info("Deleted attachment %s", attachment_id)
        return result.deleted_count or 0
    except Exception as e:
        logger.error("Failed to delete attachment %s: %s", attachment_id, e)
        return 0
