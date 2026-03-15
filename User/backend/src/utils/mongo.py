"""MongoDB utilities for creating clients and accessing collections."""
from functools import lru_cache
from typing import Optional, Tuple
from pymongo import MongoClient, ASCENDING
from pymongo.server_api import ServerApi


def _validate(uri: Optional[str]) -> str:
    if not uri:
        raise ValueError("MONGO_URI is required to use MongoDB")
    return uri


def _make_cache_key(uri: str, client_kwargs: dict) -> Tuple[str, Tuple[Tuple[str, object], ...]]:
    return uri, tuple(sorted(client_kwargs.items()))


@lru_cache(maxsize=4)
def _get_mongo_client_cached(uri: str, kwargs_key: Tuple[Tuple[str, object], ...]) -> MongoClient:
    validated_uri = _validate(uri)
    kwargs = dict(kwargs_key)
    # Ensure server_api remains consistent
    kwargs.setdefault("server_api", ServerApi("1"))
    return MongoClient(validated_uri, **kwargs)


def get_mongo_client(uri: str, **client_kwargs) -> MongoClient:
    """Return a cached MongoClient for the given URI and options."""
    cache_key = _make_cache_key(_validate(uri), client_kwargs)
    return _get_mongo_client_cached(cache_key[0], cache_key[1])


def get_database(uri: str, db_name: str, **client_kwargs):
    """Get a database handle from MongoDB."""
    client = get_mongo_client(uri, **client_kwargs)
    return client[db_name]


def get_collection(uri: str, db_name: str, collection_name: str, **client_kwargs):
    """Get a collection handle from MongoDB."""
    db = get_database(uri, db_name, **client_kwargs)
    return db[collection_name]


def ensure_history_collection(
    uri: str,
    db_name: str,
    collection_name: str,
    **client_kwargs,
):
    """Create/access history collection and ensure helpful indexes exist."""
    collection = get_collection(uri, db_name, collection_name, **client_kwargs)
    try:
        # Index for quick lookups by session_id and ordering by timestamp
        collection.create_index([("session_id", ASCENDING), ("timestamp", ASCENDING)], background=True)
        collection.create_index([("user_id", ASCENDING), ("timestamp", ASCENDING)], background=True)
    except Exception:
        # Non-fatal; collection will still exist even if index creation fails
        pass
    return collection


def ensure_users_collection(db, collection_name: str = "users") -> None:
    """Ensure users collection exists and has unique index on email (for CRUD)."""
    if db is None:
        return
    coll = db[collection_name]
    try:
        coll.create_index("email", unique=True, background=True)
    except Exception:
        pass


def ensure_activity_logs_collection(db, collection_name: str = "activity_logs") -> None:
    """Ensure activity_logs collection exists and has indexes (for admin queries)."""
    if db is None:
        return
    coll = db[collection_name]
    try:
        coll.create_index([("timestamp", ASCENDING)], background=True)
        coll.create_index([("user_id", ASCENDING)], background=True)
        coll.create_index([("action", ASCENDING)], background=True)
    except Exception:
        pass
