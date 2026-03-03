"""
MongoDB connection and collections for lawagents tools and integrations.
"""
import os
from typing import Any

try:
    from pymongo import MongoClient
    from pymongo.database import Database
    from pymongo.collection import Collection
except ImportError:
    MongoClient = None
    Database = None
    Collection = None


def get_mongo_uri() -> str | None:
    """Get MongoDB URI from env (OPENAI_KEY fallback for OPENAI_API_KEY)."""
    return os.environ.get("MONGODB_URI") or os.environ.get("MONGO_URI")


def get_client() -> "MongoClient | None":
    """Return MongoDB client or None if not configured."""
    if MongoClient is None:
        return None
    uri = get_mongo_uri()
    if not uri:
        return None
    return MongoClient(uri)


def get_db() -> "Database | None":
    """Return lawagents database."""
    client = get_client()
    if not client:
        return None
    return client["lawagents"]


def get_tools_collection() -> "Collection | None":
    """Return tools collection for tool catalog."""
    db = get_db()
    return db["tools"] if db is not None else None


def get_integrations_collection() -> "Collection | None":
    """Return integrations collection for MCP/API connectors."""
    db = get_db()
    return db["integrations"] if db is not None else None


def ensure_indexes() -> None:
    """Create indexes on tools and integrations."""
    tools = get_tools_collection()
    if tools is not None:
        tools.create_index("slug", unique=True)
        tools.create_index("category")
        tools.create_index("score")
        tools.create_index("last_synced")
        tools.create_index("has_mcp")

    integrations = get_integrations_collection()
    if integrations is not None:
        integrations.create_index("slug", unique=True)
        integrations.create_index("tool_slug")
        integrations.create_index("type")
