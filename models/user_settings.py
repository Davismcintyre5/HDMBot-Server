"""
server/models/user_settings.py — Per-user settings model
All settings stored per WhatsApp user number.
"""
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Optional
from server.config.database import get_collection
from bson import ObjectId


@dataclass
class UserSettings:
    """Per-user settings stored in MongoDB."""
    user_number: str
    prefix: str = "."
    mode: str = "public"
    always_online: bool = False
    anti_delete: bool = True
    anti_bug: bool = False
    auto_view_status: bool = False
    auto_reply: bool = False
    footer_text: str = "🤖 HDM BOT"
    
    # Group settings - all per user
    welcome_enabled: bool = False
    welcome_message: str = "👋 Welcome to the group!"
    goodbye_enabled: bool = False
    goodbye_message: str = "😢 Goodbye!"
    antilink_enabled: bool = False
    antilink_action: str = "delete"
    anti_status_mention_enabled: bool = False
    anti_status_mention_action: str = "warn"
    only_admin: bool = False
    warn_limit: int = 3
    anti_bad_word: bool = False
    bad_word_action: str = "delete"
    bad_words: list = field(default_factory=list)
    muted_users: dict = field(default_factory=dict)
    warning_users: dict = field(default_factory=dict)
    
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    _id: Optional[str] = None

    @classmethod
    def from_dict(cls, data: dict) -> "UserSettings":
        return cls(
            user_number=data.get("user_number", ""),
            prefix=data.get("prefix", "."),
            mode=data.get("mode", "public"),
            always_online=data.get("always_online", False),
            anti_delete=data.get("anti_delete", True),
            anti_bug=data.get("anti_bug", False),
            auto_view_status=data.get("auto_view_status", False),
            auto_reply=data.get("auto_reply", False),
            footer_text=data.get("footer_text", "🤖 HDM BOT"),
            welcome_enabled=data.get("welcome_enabled", False),
            welcome_message=data.get("welcome_message", "👋 Welcome to the group!"),
            goodbye_enabled=data.get("goodbye_enabled", False),
            goodbye_message=data.get("goodbye_message", "😢 Goodbye!"),
            antilink_enabled=data.get("antilink_enabled", False),
            antilink_action=data.get("antilink_action", "delete"),
            anti_status_mention_enabled=data.get("anti_status_mention_enabled", False),
            anti_status_mention_action=data.get("anti_status_mention_action", "warn"),
            only_admin=data.get("only_admin", False),
            warn_limit=data.get("warn_limit", 3),
            anti_bad_word=data.get("anti_bad_word", False),
            bad_word_action=data.get("bad_word_action", "delete"),
            bad_words=data.get("bad_words", []),
            muted_users=data.get("muted_users", {}),
            warning_users=data.get("warning_users", {}),
            created_at=data.get("created_at", datetime.utcnow()),
            updated_at=data.get("updated_at", datetime.utcnow()),
            _id=str(data.get("_id", "")),
        )

    def to_dict(self) -> dict:
        return {
            "user_number": self.user_number,
            "prefix": self.prefix,
            "mode": self.mode,
            "always_online": self.always_online,
            "anti_delete": self.anti_delete,
            "anti_bug": self.anti_bug,
            "auto_view_status": self.auto_view_status,
            "auto_reply": self.auto_reply,
            "footer_text": self.footer_text,
            "welcome_enabled": self.welcome_enabled,
            "welcome_message": self.welcome_message,
            "goodbye_enabled": self.goodbye_enabled,
            "goodbye_message": self.goodbye_message,
            "antilink_enabled": self.antilink_enabled,
            "antilink_action": self.antilink_action,
            "anti_status_mention_enabled": self.anti_status_mention_enabled,
            "anti_status_mention_action": self.anti_status_mention_action,
            "only_admin": self.only_admin,
            "warn_limit": self.warn_limit,
            "anti_bad_word": self.anti_bad_word,
            "bad_word_action": self.bad_word_action,
            "bad_words": self.bad_words,
            "muted_users": self.muted_users,
            "warning_users": self.warning_users,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }

    def save(self) -> bool:
        data = self.to_dict()
        data["updated_at"] = datetime.utcnow()
        if self._id:
            result = get_collection("user_settings").update_one(
                {"_id": ObjectId(self._id)}, {"$set": data}
            )
        else:
            result = get_collection("user_settings").insert_one(data)
            self._id = str(result.inserted_id)
        return result.acknowledged if hasattr(result, "acknowledged") else bool(result.inserted_id)

    @staticmethod
    def find_by_number(user_number: str) -> Optional["UserSettings"]:
        doc = get_collection("user_settings").find_one({"user_number": user_number})
        return UserSettings.from_dict(doc) if doc else None

    @staticmethod
    def get_or_create(user_number: str) -> "UserSettings":
        settings = UserSettings.find_by_number(user_number)
        if settings is None:
            settings = UserSettings(user_number=user_number)
            settings.save()
        return settings

    @staticmethod
    def get_prefix(user_number: str) -> str:
        settings = UserSettings.find_by_number(user_number)
        return settings.prefix if settings else "."

    @staticmethod
    def get_mode(user_number: str) -> str:
        settings = UserSettings.find_by_number(user_number)
        return settings.mode if settings else "public"

    @staticmethod
    def get_setting(user_number: str, key: str, default: Any = None) -> Any:
        settings = UserSettings.find_by_number(user_number)
        if settings is None:
            return default
        return getattr(settings, key, default)

    @staticmethod
    def set_setting(user_number: str, key: str, value: Any) -> bool:
        settings = UserSettings.get_or_create(user_number)
        if hasattr(settings, key):
            setattr(settings, key, value)
            return settings.save()
        return False