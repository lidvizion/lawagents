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
