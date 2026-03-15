import logging
from typing import Optional
from pymongo import MongoClient

logger = logging.getLogger(__name__)

# Cache for MongoDB client
_client: Optional[MongoClient] = None

def get_mongo_client(uri: str) -> Optional[MongoClient]:
    """Get or create singleton MongoDB client."""
    global _client
    try:
        if _client is None:
            logger.info("Initializing MongoDB client...")
            kwargs = {
                "serverSelectionTimeoutMS": 5000,
                "connectTimeoutMS": 5000
            }
            if uri.startswith("mongodb+srv://"):
                kwargs["tls"] = True
                
            _client = MongoClient(uri, **kwargs)
            # Test connection
            _client.admin.command('ping')
            logger.info("Successfully connected to MongoDB")
        return _client
    except Exception as e:
        logger.error(f"Failed to connect to MongoDB: {e}")
        _client = None
        return None

def get_collection(uri: str, db_name: str, collection_name: str):
    """Get specific collection from MongoDB."""
    client = get_mongo_client(uri)
    if not client:
        return None
    return client[db_name][collection_name]
