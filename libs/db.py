"""
MongoDB connection and collections for tools and integrations.
Requires MONGODB_URI in environment.
"""
import os
from typing import Any

try:
    from pymongo import MongoClient
    from pymongo.collection import Collection
    from pymongo.database import Database
except ImportError:
    MongoClient = None  # type: ignore
    Collection = Any  # type: ignore
    Database = Any  # type: ignore


def get_client() -> "MongoClient | None":
    """Return MongoDB client or None if not configured."""
    uri = os.environ.get("MONGODB_URI")
    if not uri or not MongoClient:
        return None
    return MongoClient(uri)


def get_db() -> "Database | None":
    """Return lawagents database or None."""
    client = get_client()
    if client is None:
        return None
    db = client.get_default_database()
    if db is not None:
        return db
    return client["lawagents"]


def get_tools_collection() -> "Collection | None":
    """Return tools collection. Schema: slug, name, category, use_when, score, has_mcp, api, etc."""
    db = get_db()
    return db["tools"] if db is not None else None


def get_integrations_collection() -> "Collection | None":
    """Return integrations collection. Schema: slug, name, type, tool_slug, url, auth_type, etc."""
    db = get_db()
    return db["integrations"] if db is not None else None


def ensure_indexes() -> None:
    """Create indexes on tools and integrations."""
    tools = get_tools_collection()
    if tools is not None:
        tools.create_index("slug", unique=True)
        tools.create_index("category")
        tools.create_index("has_mcp")
        tools.create_index("last_synced")
    integrations = get_integrations_collection()
    if integrations is not None:
        integrations.create_index("slug", unique=True)
        integrations.create_index("tool_slug")
        integrations.create_index("type")
