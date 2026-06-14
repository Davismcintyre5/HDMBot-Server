"""
server/models/auto_reply.py — Auto-reply rules model (Sync PyMongo)
"""
from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional
from config.database import autoreplies_col
from bson import ObjectId


@dataclass
class AutoReply:
    name: str
    trigger: str
    response: str
    match_type: str = "contains"
    category: str = "general"
    enabled: bool = True
    cooldown: int = 10
    session_id: str = "global"
    group_only: bool = False
    pm_only: bool = False
    priority: int = 0
    times_triggered: int = 0
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    _id: Optional[str] = None

    @classmethod
    def from_dict(cls, data: dict) -> "AutoReply":
        return cls(
            name=data.get("name", ""), trigger=data.get("trigger", ""),
            response=data.get("response", ""), match_type=data.get("match_type", "contains"),
            category=data.get("category", "general"), enabled=data.get("enabled", True),
            cooldown=data.get("cooldown", 10), session_id=data.get("session_id", "global"),
            group_only=data.get("group_only", False), pm_only=data.get("pm_only", False),
            priority=data.get("priority", 0), times_triggered=data.get("times_triggered", 0),
            created_at=data.get("created_at", datetime.utcnow()),
            updated_at=data.get("updated_at", datetime.utcnow()),
            _id=str(data.get("_id", "")),
        )

    def to_dict(self) -> dict:
        return {
            "name": self.name, "trigger": self.trigger, "response": self.response,
            "match_type": self.match_type, "category": self.category,
            "enabled": self.enabled, "cooldown": self.cooldown,
            "session_id": self.session_id, "group_only": self.group_only,
            "pm_only": self.pm_only, "priority": self.priority,
            "times_triggered": self.times_triggered,
            "created_at": self.created_at, "updated_at": self.updated_at,
        }

    def save(self) -> bool:
        data = self.to_dict()
        if self._id:
            result = autoreplies_col().update_one({"_id": ObjectId(self._id)}, {"$set": data})
        else:
            result = autoreplies_col().insert_one(data)
            self._id = str(result.inserted_id)
        return result.acknowledged if hasattr(result, "acknowledged") else bool(result.inserted_id)

    def delete(self) -> bool:
        if self._id:
            result = autoreplies_col().delete_one({"_id": ObjectId(self._id)})
            return result.deleted_count > 0
        return False

    @staticmethod
    def find_all(session_id: str = "global") -> list["AutoReply"]:
        docs = autoreplies_col().find({"session_id": {"$in": [session_id, "global"]}}).sort("priority", -1)
        return [AutoReply.from_dict(doc) for doc in docs]

    @staticmethod
    def find_by_id(oid: str) -> Optional["AutoReply"]:
        doc = autoreplies_col().find_one({"_id": ObjectId(oid)})
        return AutoReply.from_dict(doc) if doc else None