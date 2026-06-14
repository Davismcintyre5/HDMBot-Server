"""
server/services/command_service.py — Command CRUD service
"""
import logging
from typing import Optional
from server.models.command import Command

logger = logging.getLogger(__name__)


class CommandService:

    @staticmethod
    def get_all(session_id: str = "global") -> list[dict]:
        return [c.to_dict() for c in Command.find_all(session_id)]

    @staticmethod
    def get(command_id: str) -> Optional[dict]:
        cmd = Command.find_by_id(command_id)
        return cmd.to_dict() if cmd else None

    @staticmethod
    def create(data: dict) -> Optional[dict]:
        if Command.find_by_name(data["name"], data.get("session_id", "global")):
            return None
        cmd = Command(
            name=data["name"],
            description=data.get("description", "No description"),
            response=data.get("response", ""),
            category=data.get("category", "general"),
            admin_only=data.get("admin_only", False),
            aliases=data.get("aliases", []),
            session_id=data.get("session_id", "global"),
        )
        cmd.save()
        return cmd.to_dict()

    @staticmethod
    def update(command_id: str, data: dict) -> Optional[dict]:
        cmd = Command.find_by_id(command_id)
        if not cmd: return None
        for key in ["name", "description", "response", "category", "admin_only", "aliases", "enabled"]:
            if key in data: setattr(cmd, key, data[key])
        cmd.updated_at = datetime.utcnow()
        cmd.save()
        return cmd.to_dict()

    @staticmethod
    def delete(command_id: str) -> bool:
        cmd = Command.find_by_id(command_id)
        if cmd: return cmd.delete()
        return False

    @staticmethod
    def toggle(command_id: str, enabled: bool = None) -> Optional[dict]:
        cmd = Command.find_by_id(command_id)
        if not cmd: return None
        cmd.enabled = enabled if enabled is not None else not cmd.enabled
        cmd.save()
        return cmd.to_dict()


from datetime import datetime
command_service = CommandService()