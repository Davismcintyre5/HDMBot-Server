"""
server/models/broadcast.py — Broadcast messages model (Sync PyMongo)
"""
from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional
from server.config.database import broadcasts_col
from bson import ObjectId


@dataclass
class Broadcast:
    name: str
    message: str
    session_id: str = "global"
    target_type: str = "all"
    target_jids: List[str] = field(default_factory=list)
    status: str = "draft"
    sent_count: int = 0
    failed_count: int = 0
    total_targets: int = 0
    scheduled_at: Optional[datetime] = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None
    _id: Optional[str] = None

    @classmethod
    def from_dict(cls, data: dict) -> "Broadcast":
        return cls(
            name=data.get("name", ""), message=data.get("message", ""),
            session_id=data.get("session_id", "global"),
            target_type=data.get("target_type", "all"),
            target_jids=data.get("target_jids", []),
            status=data.get("status", "draft"),
            sent_count=data.get("sent_count", 0),
            failed_count=data.get("failed_count", 0),
            total_targets=data.get("total_targets", 0),
            scheduled_at=data.get("scheduled_at"),
            created_at=data.get("created_at", datetime.utcnow()),
            completed_at=data.get("completed_at"),
            _id=str(data.get("_id", "")),
        )

    def to_dict(self) -> dict:
        return {
            "name": self.name, "message": self.message, "session_id": self.session_id,
            "target_type": self.target_type, "target_jids": self.target_jids,
            "status": self.status, "sent_count": self.sent_count,
            "failed_count": self.failed_count, "total_targets": self.total_targets,
            "scheduled_at": self.scheduled_at,
            "created_at": self.created_at, "completed_at": self.completed_at,
        }

    def save(self) -> bool:
        data = self.to_dict()
        if self._id:
            result = broadcasts_col().update_one({"_id": ObjectId(self._id)}, {"$set": data})
        else:
            result = broadcasts_col().insert_one(data)
            self._id = str(result.inserted_id)
        return result.acknowledged if hasattr(result, "acknowledged") else bool(result.inserted_id)

    def delete(self) -> bool:
        if self._id:
            result = broadcasts_col().delete_one({"_id": ObjectId(self._id)})
            return result.deleted_count > 0
        return False

    @staticmethod
    def find_all(session_id: str = "global") -> list["Broadcast"]:
        docs = broadcasts_col().find({"session_id": session_id}).sort("created_at", -1)
        return [Broadcast.from_dict(doc) for doc in docs]

    @staticmethod
    def find_by_id(oid: str) -> Optional["Broadcast"]:
        doc = broadcasts_col().find_one({"_id": ObjectId(oid)})
        return Broadcast.from_dict(doc) if doc else None