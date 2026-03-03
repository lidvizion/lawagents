"""
MongoDB connection and collections for lawagents tools, integrations, and findings.

Requires MONGODB_URI or MONGO_URI for database access. Optional MONGODB_DB selects
the database name when the URI has no default database.
"""

from __future__ import annotations

import os

try:
    from pymongo import MongoClient
    from pymongo.collection import Collection
    from pymongo.database import Database
except ImportError:
    MongoClient = None  # type: ignore[misc, assignment]
    Collection = None  # type: ignore[misc, assignment]
    Database = None  # type: ignore[misc, assignment]

_CLIENT: object | None = None


def get_mongo_uri() -> str | None:
    return os.environ.get("MONGODB_URI") or os.environ.get("MONGO_URI")


def get_client():
    """Return a singleton MongoDB client, or None if pymongo or URI is missing."""
    global _CLIENT
    if MongoClient is None:
        return None
    uri = get_mongo_uri()
    if not uri:
        return None
    if _CLIENT is None:
        _CLIENT = MongoClient(uri)
    return _CLIENT


def get_db() -> Database | None:
    """Return the lawagents database, or None if not configured."""
    client = get_client()
    if client is None:
        return None
    db_name = os.environ.get("MONGODB_DB")
    if db_name:
        return client[db_name]
    default_db = client.get_default_database()
    if default_db is not None:
        return default_db
    return client["lawagents"]


def get_tools_collection() -> Collection | None:
    """Tools collection (legal software / API catalog)."""
    db = get_db()
    return db["tools"] if db is not None else None


def get_integrations_collection() -> Collection | None:
    """Integrations collection (MCP/API connectors)."""
    db = get_db()
    return db["integrations"] if db is not None else None


def get_findings_collection() -> Collection | None:
    """Findings collection (raw crawl/search results)."""
    db = get_db()
    return db["findings"] if db is not None else None


def ensure_indexes() -> None:
    """Create indexes on tools, integrations, and findings."""
    tools = get_tools_collection()
    if tools is not None:
        tools.create_index("slug", unique=True)
        tools.create_index("category")
        tools.create_index("score")
        tools.create_index("last_synced")
        tools.create_index("source")
        tools.create_index("has_mcp")

    integrations = get_integrations_collection()
    if integrations is not None:
        integrations.create_index("slug", unique=True)
        integrations.create_index("tool_slug")
        integrations.create_index("type")

    findings = get_findings_collection()
    if findings is not None:
        findings.create_index("source")
        findings.create_index("crawled_at")
