"""
MongoDB connection and collections for lawagents tools and integrations.
"""
from __future__ import annotations

import os
from typing import TYPE_CHECKING

from pymongo import MongoClient, ASCENDING
from pymongo.collection import Collection
from pymongo.database import Database

if TYPE_CHECKING:
    pass

_DB: Database | None = None
_CLIENT: MongoClient | None = None


def get_client() -> MongoClient:
    """Get or create MongoDB client."""
    global _CLIENT
    if _CLIENT is None:
        uri = os.environ.get("MONGODB_URI", "mongodb://localhost:27017")
        _CLIENT = MongoClient(uri)
    return _CLIENT


def get_db() -> Database:
    """Get lawagents database."""
    global _DB
    if _DB is None:
        db_name = os.environ.get("MONGODB_DB", "lawagents")
        _DB = get_client()[db_name]
    return _DB


def get_tools_collection() -> Collection:
    """Get tools collection (legal software catalog)."""
    return get_db()["tools"]


def get_integrations_collection() -> Collection:
    """Get integrations collection (MCP/API connectors)."""
    return get_db()["integrations"]


def get_findings_collection() -> Collection:
    """Get findings collection (raw search/crawl results)."""
    return get_db()["findings"]


def ensure_indexes() -> None:
    """Create indexes for tools, integrations, findings."""
    tools = get_tools_collection()
    tools.create_index("slug", unique=True)
    tools.create_index("category")
    tools.create_index("score")
    tools.create_index("last_synced")
    tools.create_index("source")  # e.g. "datarade", "catalog"

    integrations = get_integrations_collection()
    integrations.create_index("slug", unique=True)
    integrations.create_index("tool_slug")
    integrations.create_index("type")

    findings = get_findings_collection()
    findings.create_index("source")
    findings.create_index("crawled_at")
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
