"""
server/models/command.py — Dynamic Command model (Sync PyMongo)
"""
from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional
from config.database import commands_col
from bson import ObjectId


@dataclass
class Command:
    name: str
    description: str = "No description"
    response: str = ""
    category: str = "general"
    admin_only: bool = False
    aliases: List[str] = field(default_factory=list)
    enabled: bool = True
    times_used: int = 0
    session_id: str = "global"
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    _id: Optional[str] = None

    @classmethod
    def from_dict(cls, data: dict) -> "Command":
        return cls(
            name=data.get("name", ""),
            description=data.get("description", "No description"),
            response=data.get("response", ""),
            category=data.get("category", "general"),
            admin_only=data.get("adminOnly", False) or data.get("admin_only", False),
            aliases=data.get("aliases", []),
            enabled=data.get("enabled", True),
            times_used=data.get("timesUsed", 0) or data.get("times_used", 0),
            session_id=data.get("session_id", "global"),
            created_at=data.get("created_at", datetime.utcnow()),
            updated_at=data.get("updated_at", datetime.utcnow()),
            _id=str(data.get("_id", "")),
        )

    def to_dict(self) -> dict:
        return {
            "name": self.name, "description": self.description,
            "response": self.response, "category": self.category,
            "adminOnly": self.admin_only, "aliases": self.aliases,
            "enabled": self.enabled, "timesUsed": self.times_used,
            "session_id": self.session_id,
            "created_at": self.created_at, "updated_at": self.updated_at,
        }

    def save(self) -> bool:
        data = self.to_dict()
        if self._id:
            result = commands_col().update_one({"_id": ObjectId(self._id)}, {"$set": data})
        else:
            result = commands_col().insert_one(data)
            self._id = str(result.inserted_id)
        return result.acknowledged if hasattr(result, "acknowledged") else bool(result.inserted_id)

    def delete(self) -> bool:
        if self._id:
            result = commands_col().delete_one({"_id": ObjectId(self._id)})
            return result.deleted_count > 0
        return False

    @staticmethod
    def find_all(session_id: str = "global") -> list["Command"]:
        docs = commands_col().find({"session_id": {"$in": [session_id, "global"]}})
        return [Command.from_dict(doc) for doc in docs]

    @staticmethod
    def find_by_id(oid: str) -> Optional["Command"]:
        doc = commands_col().find_one({"_id": ObjectId(oid)})
        return Command.from_dict(doc) if doc else None

    @staticmethod
    def find_by_name(name: str, session_id: str = "global") -> Optional["Command"]:
        doc = commands_col().find_one({"name": name, "session_id": {"$in": [session_id, "global"]}})
        return Command.from_dict(doc) if doc else None

    @staticmethod
    def increment_usage(oid: str):
        commands_col().update_one({"_id": ObjectId(oid)}, {"$inc": {"timesUsed": 1}})