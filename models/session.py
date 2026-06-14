"""
server/models/session.py — WhatsApp session model (Sync PyMongo)
"""
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional
from config.database import sessions_col
from bson import ObjectId


@dataclass
class Session:
    session_id: str
    session_name: str = ""
    phone_number: str = ""
    status: str = "disconnected"
    pairing_enabled: bool = False
    pairing_phone: str = ""
    db_path: str = ""
    qr_string: Optional[str] = None
    last_connected: Optional[datetime] = None
    is_default: bool = False
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    _id: Optional[str] = None

    @classmethod
    def from_dict(cls, data: dict) -> "Session":
        return cls(
            session_id=data.get("session_id", ""),
            session_name=data.get("session_name", ""),
            phone_number=data.get("phone_number", ""),
            status=data.get("status", "disconnected"),
            pairing_enabled=data.get("pairing_enabled", False),
            pairing_phone=data.get("pairing_phone", ""),
            db_path=data.get("db_path", ""),
            qr_string=data.get("qr_string"),
            last_connected=data.get("last_connected"),
            is_default=data.get("is_default", False),
            created_at=data.get("created_at", datetime.utcnow()),
            updated_at=data.get("updated_at", datetime.utcnow()),
            _id=str(data.get("_id", "")),
        )

    def to_dict(self) -> dict:
        return {
            "session_id": self.session_id, "session_name": self.session_name,
            "phone_number": self.phone_number, "status": self.status,
            "pairing_enabled": self.pairing_enabled, "pairing_phone": self.pairing_phone,
            "db_path": self.db_path, "qr_string": self.qr_string,
            "last_connected": self.last_connected, "is_default": self.is_default,
            "created_at": self.created_at, "updated_at": self.updated_at,
        }

    def save(self) -> bool:
        data = self.to_dict()
        if self._id:
            result = sessions_col().update_one({"_id": ObjectId(self._id)}, {"$set": data})
        else:
            result = sessions_col().insert_one(data)
            self._id = str(result.inserted_id)
        return result.acknowledged if hasattr(result, "acknowledged") else bool(result.inserted_id)

    def delete(self) -> bool:
        if self._id:
            result = sessions_col().delete_one({"_id": ObjectId(self._id)})
            return result.deleted_count > 0
        return False

    @staticmethod
    def find_all() -> list["Session"]:
        docs = sessions_col().find().sort("is_default", -1).sort("created_at", 1)
        return [Session.from_dict(doc) for doc in docs]

    @staticmethod
    def find_by_id(session_id: str) -> Optional["Session"]:
        doc = sessions_col().find_one({"session_id": session_id})
        return Session.from_dict(doc) if doc else None

    @staticmethod
    def update_status(session_id: str, status: str, **extra) -> bool:
        update = {"status": status, "updated_at": datetime.utcnow(), **extra}
        if status == "connected":
            update["last_connected"] = datetime.utcnow()
        result = sessions_col().update_one({"session_id": session_id}, {"$set": update})
        return result.modified_count > 0 or result.matched_count > 0

    @staticmethod
    def update_qr(session_id: str, qr_string: str) -> bool:
        result = sessions_col().update_one(
            {"session_id": session_id},
            {"$set": {"qr_string": qr_string, "updated_at": datetime.utcnow()}}
        )
        return result.modified_count > 0

    @staticmethod
    def delete_by_id(session_id: str) -> bool:
        result = sessions_col().delete_one({"session_id": session_id})
        return result.deleted_count > 0