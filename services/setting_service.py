"""
server/services/setting_service.py — Bot settings management
"""
import logging
from typing import Any, Optional
from server.models.bot_setting import BotSetting
from server.config.settings import settings as app_settings

logger = logging.getLogger(__name__)


class SettingService:
    """Service for getting/setting bot settings."""

    @staticmethod
    async def get(session_id: str, key: str, default: Any = None) -> Any:
        return await BotSetting.get_value(session_id, key, default)

    @staticmethod
    async def set(session_id: str, key: str, value: Any) -> bool:
        return await BotSetting.upsert(session_id, key, value)

    @staticmethod
    async def get_all(session_id: str) -> dict:
        from server.config.database import bot_settings_col
        cursor = bot_settings_col().find({"session_id": session_id})
        settings = {}
        async for doc in cursor:
            settings[doc["key"]] = doc["value"]
        
        # Fill in defaults for missing keys
        for key, default in app_settings.DEFAULT_SETTINGS.items():
            if key not in settings:
                settings[key] = default
        
        return settings

    @staticmethod
    async def reset(session_id: str, key: str) -> bool:
        default = app_settings.DEFAULT_SETTINGS.get(key)
        if default is not None:
            return await BotSetting.upsert(session_id, key, default)
        return False


setting_service = SettingService()