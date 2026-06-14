"""
server/whatsapp/handlers/base_handler.py — Base handler with shared utilities
Matches the JS commandHandler.js state management and utility functions.
"""
from __future__ import annotations

import re
import time
from datetime import datetime
from typing import Any, Dict, Optional

from server.config.settings import settings
from server.utils.helpers import get_user_number, sanitize_text, format_number
from server.whatsapp.connection import send_text, get_text, jid_to_str, print_msg


class BaseHandler:
    """Base class for all WhatsApp handlers."""

    # Class-level caches (shared across instances)
    _session_settings_cache: Dict[str, Dict[str, Any]] = {}
    _group_settings_cache: Dict[str, Dict[str, Any]] = {}
    _anti_link_settings: Dict[str, dict] = {}
    _anti_status_mention: Dict[str, dict] = {}
    _only_admin_settings: Dict[str, bool] = {}
    _muted_users: Dict[str, Dict[str, dict]] = {}
    _warning_users: Dict[str, Dict[str, dict]] = {}
    _bad_words_cache: Dict[str, set] = {}
    _member_stats_cache: Dict[str, dict] = {}
    _active_attacks: Dict[str, dict] = {}
    _bug_logs_cache: Dict[str, list] = {}
    _pairing_codes: Dict[str, dict] = {}
    _menu_sessions: Dict[str, dict] = {}

    def __init__(self, session_id: str = "default"):
        self.session_id = session_id

    @staticmethod
    def get_user_number(jid: str) -> str:
        return get_user_number(jid)

    @staticmethod
    def format_number(number: str) -> str:
        return format_number(number)

    @staticmethod
    def jid_to_str(jid) -> str:
        return jid_to_str(jid)

    @staticmethod
    def get_text(msg) -> str:
        return get_text(msg)

    @staticmethod
    def ts() -> str:
        return datetime.now().strftime("%H:%M:%S")

    async def send_reply(self, client, jid, text: str):
        safe = sanitize_text(str(text))
        footer = await self.get_session_setting("footerText")
        if footer and footer not in safe:
            safe += f"\n\n_{footer}_"
        send_text(client, jid, safe)

    def is_owner(self, jid: str) -> bool:
        num = self.get_user_number(jid)
        return num == settings.OWNER_NUMBER or num == settings.BOT_OWNER_NUMBER

    async def is_admin(self, jid: str) -> bool:
        num = self.get_user_number(jid)
        if self.is_owner(jid):
            return True
        if num in settings.ADMIN_NUMBERS:
            return True
        super_admins = await self.get_session_setting("superAdmins", [])
        if num in super_admins:
            return True
        bot_admins = await self.get_session_setting("botAdmins", [])
        return num in bot_admins

    async def is_super_admin(self, jid: str) -> bool:
        if self.is_owner(jid):
            return True
        num = self.get_user_number(jid)
        super_admins = await self.get_session_setting("superAdmins", [])
        return num in super_admins

    async def is_user_allowed_for_bug(self, jid: str) -> bool:
        num = self.get_user_number(jid)
        if num in settings.BUG_ALLOWED_USERS:
            return True
        if await self.is_admin(jid):
            return True
        bug_users = await self.get_session_setting("bugUsers", [])
        return num in bug_users

    async def get_prefix(self) -> str:
        return await self.get_session_setting("commandPrefix", settings.BOT_PREFIX)

    async def get_session_setting(self, key: str, default: Any = None) -> Any:
        cache_key = f"{self.session_id}:{key}"
        cached = self._session_settings_cache.get(cache_key)
        if cached and (time.time() * 1000) - cached["timestamp"] < settings.SESSION_SETTINGS_CACHE_TTL:
            return cached["value"]

        try:
            from server.models.bot_setting import BotSetting
            value = await BotSetting.get_value(self.session_id, key)
            if value is None:
                value = settings.DEFAULT_SETTINGS.get(key, default)
        except Exception:
            value = settings.DEFAULT_SETTINGS.get(key, default)

        self._session_settings_cache[cache_key] = {"value": value, "timestamp": time.time() * 1000}
        return value

    async def set_session_setting(self, key: str, value: Any) -> bool:
        try:
            from server.models.bot_setting import BotSetting
            ok = await BotSetting.upsert(self.session_id, key, value)
            if ok:
                cache_key = f"{self.session_id}:{key}"
                self._session_settings_cache[cache_key] = {"value": value, "timestamp": time.time() * 1000}
            return ok
        except Exception:
            return False

    async def get_group_setting(self, group_id: str, key: str, default: Any = None) -> Any:
        cache_key = f"{group_id}:{key}"
        cached = self._group_settings_cache.get(cache_key)
        if cached and (time.time() * 1000) - cached["timestamp"] < settings.GROUP_SETTINGS_CACHE_TTL:
            return cached["value"]

        try:
            from server.models.bot_setting import BotSetting
            value = await BotSetting.get_value(group_id, key, default)
        except Exception:
            value = default

        self._group_settings_cache[cache_key] = {"value": value, "timestamp": time.time() * 1000}
        return value

    async def set_group_setting(self, group_id: str, key: str, value: Any) -> bool:
        try:
            from server.models.bot_setting import BotSetting
            ok = await BotSetting.upsert(group_id, key, value)
            if ok:
                cache_key = f"{group_id}:{key}"
                self._group_settings_cache[cache_key] = {"value": value, "timestamp": time.time() * 1000}
            return ok
        except Exception:
            return False

    def clear_menu_session(self, user_id: str):
        user_num = self.get_user_number(user_id)
        session = self._menu_sessions.get(user_num)
        if session and session.get("timer"):
            try:
                session["timer"].cancel()
            except Exception:
                pass
        self._menu_sessions.pop(user_num, None)

    def start_menu_session(self, user_id: str, items: list, message_id: str, timeout_ms: int = 60000):
        import threading
        user_num = self.get_user_number(user_id)
        self.clear_menu_session(user_id)

        timer = threading.Timer(timeout_ms / 1000, lambda: self._menu_sessions.pop(user_num, None))
        timer.daemon = True
        timer.start()

        self._menu_sessions[user_num] = {
            "items": items,
            "message_id": message_id,
            "expires": time.time() + timeout_ms / 1000,
            "timer": timer,
        }

    def get_menu_session(self, user_id: str) -> Optional[dict]:
        user_num = self.get_user_number(user_id)
        session = self._menu_sessions.get(user_num)
        if session and time.time() > session.get("expires", 0):
            self.clear_menu_session(user_id)
            return None
        return session