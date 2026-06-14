"""
server/models/user.py — User model for admin/authentication
"""
from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional
from config.database import users_col


@dataclass
class User:
    """Represents an admin user for the dashboard."""
    username: str
    email: str
    password_hash: str
    role: str = "admin"  # "owner", "super_admin", "admin", "viewer"
    phone_number: str = ""
    is_active: bool = True
    permissions: List[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    last_login: Optional[datetime] = None
    _id: Optional[str] = None

    @classmethod
    def from_dict(cls, data: dict) -> "User":
        return cls(
            username=data.get("username", ""),
            email=data.get("email", ""),
            password_hash=data.get("password_hash", ""),
            role=data.get("role", "admin"),
            phone_number=data.get("phone_number", ""),
            is_active=data.get("is_active", True),
            permissions=data.get("permissions", []),
            created_at=data.get("created_at", datetime.utcnow()),
            updated_at=data.get("updated_at", datetime.utcnow()),
            last_login=data.get("last_login"),
            _id=str(data.get("_id", "")),
        )

    def to_dict(self) -> dict:
        return {
            "username": self.username,
            "email": self.email,
            "password_hash": self.password_hash,
            "role": self.role,
            "phone_number": self.phone_number,
            "is_active": self.is_active,
            "permissions": self.permissions,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "last_login": self.last_login,
        }

    @staticmethod
    async def find_by_email(email: str) -> Optional["User"]:
        doc = await users_col().find_one({"email": email})
        return User.from_dict(doc) if doc else None

    @staticmethod
    async def find_by_username(username: str) -> Optional["User"]:
        doc = await users_col().find_one({"username": username})
        return User.from_dict(doc) if doc else None

    async def save(self) -> bool:
        if self._id:
            from bson import ObjectId
            result = await users_col().update_one(
                {"_id": ObjectId(self._id)},
                {"$set": self.to_dict()},
            )
        else:
            result = await users_col().insert_one(self.to_dict())
            self._id = str(result.inserted_id)
        return result.acknowledged if hasattr(result, "acknowledged") else bool(result.inserted_id)