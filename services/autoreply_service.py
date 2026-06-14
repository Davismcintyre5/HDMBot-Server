"""
server/services/autoreply_service.py — Auto-reply rules CRUD service
"""
import logging
from typing import Optional
from models.auto_reply import AutoReply

logger = logging.getLogger(__name__)


class AutoReplyService:

    @staticmethod
    def get_all(session_id: str = "global") -> list[dict]:
        return [r.to_dict() for r in AutoReply.find_all(session_id)]

    @staticmethod
    def get(rule_id: str) -> Optional[dict]:
        rule = AutoReply.find_by_id(rule_id)
        return rule.to_dict() if rule else None

    @staticmethod
    def create(data: dict) -> Optional[dict]:
        rule = AutoReply(
            name=data["name"], trigger=data["trigger"], response=data["response"],
            match_type=data.get("match_type", "contains"),
            cooldown=data.get("cooldown", 10),
            session_id=data.get("session_id", "global"),
            group_only=data.get("group_only", False),
            pm_only=data.get("pm_only", False),
        )
        rule.save()
        return rule.to_dict()

    @staticmethod
    def update(rule_id: str, data: dict) -> Optional[dict]:
        rule = AutoReply.find_by_id(rule_id)
        if not rule: return None
        for key in ["name", "trigger", "response", "match_type", "cooldown", "enabled", "group_only", "pm_only"]:
            if key in data: setattr(rule, key, data[key])
        rule.updated_at = datetime.utcnow()
        rule.save()
        return rule.to_dict()

    @staticmethod
    def delete(rule_id: str) -> bool:
        rule = AutoReply.find_by_id(rule_id)
        if rule: return rule.delete()
        return False

    @staticmethod
    def toggle(rule_id: str) -> Optional[dict]:
        rule = AutoReply.find_by_id(rule_id)
        if not rule: return None
        rule.enabled = not rule.enabled
        rule.save()
        return rule.to_dict()


from datetime import datetime
autoreply_service = AutoReplyService()