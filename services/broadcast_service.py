"""
server/services/broadcast_service.py — Broadcast CRUD service
"""
import logging
from typing import Optional
from server.models.broadcast import Broadcast

logger = logging.getLogger(__name__)


class BroadcastService:

    @staticmethod
    def get_all(session_id: str = "global") -> list[dict]:
        return [b.to_dict() for b in Broadcast.find_all(session_id)]

    @staticmethod
    def get(broadcast_id: str) -> Optional[dict]:
        b = Broadcast.find_by_id(broadcast_id)
        return b.to_dict() if b else None

    @staticmethod
    def create(data: dict) -> Optional[dict]:
        broadcast = Broadcast(
            name=data["name"], message=data["message"],
            session_id=data.get("session_id", "global"),
            target_type=data.get("target_type", "all"),
            target_jids=data.get("target_jids", []),
            scheduled_at=data.get("scheduled_at"),
        )
        broadcast.total_targets = len(broadcast.target_jids) if broadcast.target_type == "specific" else 0
        broadcast.save()
        return broadcast.to_dict()

    @staticmethod
    def update(broadcast_id: str, data: dict) -> Optional[dict]:
        b = Broadcast.find_by_id(broadcast_id)
        if not b: return None
        for key in ["name", "message", "target_type", "target_jids", "scheduled_at", "status"]:
            if key in data: setattr(b, key, data[key])
        b.updated_at = datetime.utcnow()
        b.save()
        return b.to_dict()

    @staticmethod
    def delete(broadcast_id: str) -> bool:
        b = Broadcast.find_by_id(broadcast_id)
        if b: return b.delete()
        return False

    @staticmethod
    def get_stats(session_id: str = "global") -> dict:
        all_b = Broadcast.find_all(session_id)
        stats = {"total": len(all_b), "draft": 0, "sending": 0, "completed": 0, "failed": 0}
        for b in all_b:
            if b.status in stats: stats[b.status] += 1
        return stats


from datetime import datetime
broadcast_service = BroadcastService()