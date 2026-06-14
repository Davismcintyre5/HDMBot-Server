"""
server/whatsapp/handlers/autoreply_handler.py — Auto-reply matching engine
"""
from __future__ import annotations

import re
import time
from typing import Dict

from .base_handler import BaseHandler


class AutoReplyHandler(BaseHandler):
    """Matches incoming messages against auto-reply rules."""

    def __init__(self, session_id: str = "default"):
        super().__init__(session_id)
        self._cooldowns: Dict[str, Dict[str, float]] = {}  # chat_id -> {rule_id: last_triggered}

    async def match(self, client, jid, body: str, msg) -> bool:
        """Try to match a message against auto-reply rules.
        
        Returns True if a rule matched and replied.
        """
        try:
            from models.auto_reply import AutoReply
            rules = await AutoReply.find_all_enabled(self.session_id)
        except Exception:
            return False

        chat_str = self.jid_to_str(jid)
        body_lower = body.lower()

        for rule in rules:
            rule_id = rule._id or rule.name

            # Check cooldown
            if not self._check_cooldown(chat_str, rule_id, rule.cooldown):
                continue

            # Check group/PM restrictions
            if rule.group_only or rule.pm_only:
                # Skip if we can't determine chat type
                continue

            # Match
            if self._matches(body_lower, rule.trigger, rule.match_type):
                self.send_reply(client, jid, rule.response)
                self._update_cooldown(chat_str, rule_id)
                return True

        return False

    def _matches(self, text: str, trigger: str, match_type: str) -> bool:
        """Check if text matches a trigger."""
        trigger_lower = trigger.lower()

        if match_type == "exact":
            return text == trigger_lower
        elif match_type == "starts_with":
            return text.startswith(trigger_lower)
        elif match_type == "regex":
            try:
                return bool(re.search(trigger, text, re.IGNORECASE))
            except re.error:
                return False
        else:  # "contains" (default)
            return trigger_lower in text

    def _check_cooldown(self, chat_id: str, rule_id: str, cooldown: int) -> bool:
        """Check if a rule is on cooldown for a chat."""
        if chat_id not in self._cooldowns:
            return True
        last = self._cooldowns[chat_id].get(rule_id, 0)
        return (time.time() - last) >= cooldown

    def _update_cooldown(self, chat_id: str, rule_id: str):
        """Update the cooldown timestamp for a rule in a chat."""
        if chat_id not in self._cooldowns:
            self._cooldowns[chat_id] = {}
        self._cooldowns[chat_id][rule_id] = time.time()