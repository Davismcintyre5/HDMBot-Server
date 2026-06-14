"""
server/models/contact.py — Saved contacts model (Sync PyMongo)
"""
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional
from config.database import get_collection
from bson import ObjectId

CONTACTS = "contacts"


@dataclass
class Contact:
    jid: str
    name: str
    contact_type: str = "individual"
    phone_number: str = ""
    session_id: str = "global"
    is_blocked: bool = False
    is_favorite: bool = False
    tags: list = field(default_factory=list)
    notes: str = ""
    member_count: int = 0
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    _id: Optional[str] = None

    @classmethod
    def from_dict(cls, data: dict) -> "Contact":
        return cls(
            jid=data.get("jid", ""), name=data.get("name", ""),
            contact_type=data.get("contact_type", "individual"),
            phone_number=data.get("phone_number", ""),
            session_id=data.get("session_id", "global"),
            is_blocked=data.get("is_blocked", False),
            is_favorite=data.get("is_favorite", False),
            tags=data.get("tags", []), notes=data.get("notes", ""),
            member_count=data.get("member_count", 0),
            created_at=data.get("created_at", datetime.utcnow()),
            updated_at=data.get("updated_at", datetime.utcnow()),
            _id=str(data.get("_id", "")),
        )

    def to_dict(self) -> dict:
        return {
            "jid": self.jid, "name": self.name, "contact_type": self.contact_type,
            "phone_number": self.phone_number, "session_id": self.session_id,
            "is_blocked": self.is_blocked, "is_favorite": self.is_favorite,
            "tags": self.tags, "notes": self.notes, "member_count": self.member_count,
            "created_at": self.created_at, "updated_at": self.updated_at,
        }

    def save(self) -> bool:
        data = self.to_dict()
        col = get_collection(CONTACTS)
        if self._id:
            result = col.update_one({"_id": ObjectId(self._id)}, {"$set": data})
        else:
            result = col.insert_one(data)
            self._id = str(result.inserted_id)
        return result.acknowledged if hasattr(result, "acknowledged") else bool(result.inserted_id)

    def delete(self) -> bool:
        if self._id:
            result = get_collection(CONTACTS).delete_one({"_id": ObjectId(self._id)})
            return result.deleted_count > 0
        return False

    @staticmethod
    def find_all(session_id: str = "global") -> list["Contact"]:
        docs = get_collection(CONTACTS).find({"session_id": session_id}).sort("name", 1)
        return [Contact.from_dict(doc) for doc in docs]

    @staticmethod
    def find_by_id(oid: str) -> Optional["Contact"]:
        doc = get_collection(CONTACTS).find_one({"_id": ObjectId(oid)})
        return Contact.from_dict(doc) if doc else None