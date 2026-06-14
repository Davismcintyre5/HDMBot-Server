"""
server/services/settings_service.py — Per-user settings service
"""
import logging
from typing import Any, Optional
from server.models.user_settings import UserSettings
from server.config.database import get_collection

logger = logging.getLogger(__name__)


class SettingsService:
    """Service for per-user settings management."""

    @staticmethod
    def get_user_settings(user_number: str) -> Optional[dict]:
        settings = UserSettings.find_by_number(user_number)
        return settings.to_dict() if settings else None

    @staticmethod
    def get_or_create(user_number: str) -> dict:
        settings = UserSettings.get_or_create(user_number)
        return settings.to_dict()

    @staticmethod
    def get_prefix(user_number: str) -> str:
        return UserSettings.get_prefix(user_number)

    @staticmethod
    def set_prefix(user_number: str, prefix: str) -> bool:
        return UserSettings.set_setting(user_number, "prefix", prefix)

    @staticmethod
    def get_mode(user_number: str) -> str:
        return UserSettings.get_mode(user_number)

    @staticmethod
    def set_mode(user_number: str, mode: str) -> bool:
        return UserSettings.set_setting(user_number, "mode", mode)

    @staticmethod
    def get_setting(user_number: str, key: str, default: Any = None) -> Any:
        return UserSettings.get_setting(user_number, key, default)

    @staticmethod
    def set_setting(user_number: str, key: str, value: Any) -> bool:
        return UserSettings.set_setting(user_number, key, value)

    @staticmethod
    def get_all_users() -> list[dict]:
        docs = get_collection("user_settings").find()
        return [UserSettings.from_dict(doc).to_dict() for doc in docs]

    @staticmethod
    def reset_user(user_number: str) -> bool:
        """Reset a user's settings to defaults (delete their settings document)."""
        result = get_collection("user_settings").delete_one({"user_number": user_number})
        return result.deleted_count > 0

    @staticmethod
    def reset_all_users() -> bool:
        """Reset ALL user settings to defaults."""
        result = get_collection("user_settings").delete_many({})
        logger.info(f"Reset {result.deleted_count} user settings")
        return True

    # ============ GROUP SETTINGS (per user) ============

    @staticmethod
    def get_welcome(user_number: str) -> dict:
        settings = UserSettings.find_by_number(user_number)
        if settings:
            return {"enabled": settings.welcome_enabled, "message": settings.welcome_message}
        return {"enabled": False, "message": "👋 Welcome to the group!"}

    @staticmethod
    def set_welcome(user_number: str, enabled: bool = None, message: str = None) -> bool:
        settings = UserSettings.get_or_create(user_number)
        if enabled is not None: settings.welcome_enabled = enabled
        if message is not None: settings.welcome_message = message
        return settings.save()

    @staticmethod
    def get_goodbye(user_number: str) -> dict:
        settings = UserSettings.find_by_number(user_number)
        if settings: return {"enabled": settings.goodbye_enabled, "message": settings.goodbye_message}
        return {"enabled": False, "message": "😢 Goodbye!"}

    @staticmethod
    def set_goodbye(user_number: str, enabled: bool = None, message: str = None) -> bool:
        settings = UserSettings.get_or_create(user_number)
        if enabled is not None: settings.goodbye_enabled = enabled
        if message is not None: settings.goodbye_message = message
        return settings.save()

    @staticmethod
    def get_antilink(user_number: str) -> dict:
        settings = UserSettings.find_by_number(user_number)
        if settings: return {"enabled": settings.antilink_enabled, "action": settings.antilink_action}
        return {"enabled": False, "action": "delete"}

    @staticmethod
    def set_antilink(user_number: str, enabled: bool, action: str) -> bool:
        settings = UserSettings.get_or_create(user_number)
        settings.antilink_enabled = enabled
        settings.antilink_action = action
        return settings.save()

    @staticmethod
    def get_bad_words(user_number: str) -> list:
        settings = UserSettings.find_by_number(user_number)
        return settings.bad_words if settings else []

    @staticmethod
    def add_bad_word(user_number: str, word: str) -> bool:
        settings = UserSettings.get_or_create(user_number)
        if word not in settings.bad_words:
            settings.bad_words.append(word)
            return settings.save()
        return True

    @staticmethod
    def remove_bad_word(user_number: str, word: str) -> bool:
        settings = UserSettings.find_by_number(user_number)
        if settings and word in settings.bad_words:
            settings.bad_words.remove(word)
            return settings.save()
        return False

    @staticmethod
    def get_muted_users(user_number: str) -> dict:
        settings = UserSettings.find_by_number(user_number)
        return settings.muted_users if settings else {}

    @staticmethod
    def set_muted_user(user_number: str, target_jid: str, until: float, by_jid: str) -> bool:
        settings = UserSettings.get_or_create(user_number)
        settings.muted_users[target_jid] = {"until": until, "by": by_jid}
        return settings.save()

    @staticmethod
    def remove_muted_user(user_number: str, target_jid: str) -> bool:
        settings = UserSettings.find_by_number(user_number)
        if settings and target_jid in settings.muted_users:
            del settings.muted_users[target_jid]
            return settings.save()
        return False


settings_service = SettingsService()