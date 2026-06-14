"""
server/config/database.py — MongoDB connection manager
"""
from pymongo import MongoClient
from pymongo.database import Database
from pymongo.collection import Collection
from .settings import settings
import logging

logger = logging.getLogger(__name__)

_client: MongoClient | None = None
_db: Database | None = None


def get_client() -> MongoClient:
    """Get or create MongoDB client."""
    global _client
    if _client is None:
        _client = MongoClient(settings.MONGODB_URI)
        logger.info("MongoDB client created")
    return _client


def get_db() -> Database:
    """Get the HDM Bot database."""
    global _db
    if _db is None:
        client = get_client()
        db_name = settings.MONGODB_URI.split("/")[-1].split("?")[0] or "hdm_bot"
        _db = client[db_name]
        logger.info(f"Connected to database: {db_name}")
    return _db


def get_collection(name: str) -> Collection:
    """Get a specific collection."""
    return get_db()[name]


def close_connection():
    """Close the MongoDB connection."""
    global _client, _db
    if _client:
        _client.close()
        _client = None
        _db = None
        logger.info("MongoDB connection closed")


# Convenience collections
def users_col() -> Collection:
    return get_collection("users")

def commands_col() -> Collection:
    return get_collection("commands")

def bot_settings_col() -> Collection:
    return get_collection("bot_settings")

def messages_col() -> Collection:
    return get_collection("messages")

def autoreplies_col() -> Collection:
    return get_collection("autoreplies")

def broadcasts_col() -> Collection:
    return get_collection("broadcasts")

def sessions_col() -> Collection:
    return get_collection("sessions")