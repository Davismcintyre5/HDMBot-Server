"""
server/models/bot_setting.py — BotSetting model for per-session/per-group settings
"""
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Optional
from config.database import bot_settings_col


@dataclass
class BotSetting:
    """Represents a configurable setting for a session or group."""
    session_id: str
    key: str
    value: Any
    updated_at: datetime = field(default_factory=datetime.utcnow)
    _id: Optional[str] = None

    @classmethod
    def from_dict(cls, data: dict) -> "BotSetting":
        return cls(
            session_id=data.get("session_id", ""),
            key=data.get("key", ""),
            value=data.get("value"),
            updated_at=data.get("updated_at", datetime.utcnow()),
            _id=str(data.get("_id", "")),
        )

    def to_dict(self) -> dict:
        return {
            "session_id": self.session_id,
            "key": self.key,
            "value": self.value,
            "updated_at": self.updated_at,
        }

    @staticmethod
    async def find_one(session_id: str, key: str) -> Optional["BotSetting"]:
        """Find a setting by session and key."""
        doc = await bot_settings_col().find_one({"session_id": session_id, "key": key})
        return BotSetting.from_dict(doc) if doc else None

    @staticmethod
    async def upsert(session_id: str, key: str, value: Any) -> bool:
        """Create or update a setting."""
        result = await bot_settings_col().update_one(
            {"session_id": session_id, "key": key},
            {
                "$set": {
                    "session_id": session_id,
                    "key": key,
                    "value": value,
                    "updated_at": datetime.utcnow(),
                }
            },
            upsert=True,
        )
        return result.acknowledged

    @staticmethod
    async def get_value(session_id: str, key: str, default: Any = None) -> Any:
        """Get a setting value with default."""
        setting = await BotSetting.find_one(session_id, key)
        return setting.value if setting else default