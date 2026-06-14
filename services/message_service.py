"""
server/services/message_service.py — Message log service
"""
import time
import logging
from server.models.message_log import MessageLog

logger = logging.getLogger(__name__)


class MessageService:

    @staticmethod
    def log_message(session_id: str, from_jid: str, chat_jid: str, body: str,
                    direction: str = "in", is_command: bool = False, command_name: str = None):
        """Save a message to the log."""
        try:
            msg = MessageLog(
                session_id=session_id,
                message_id=str(int(time.time() * 1000)),
                from_jid=from_jid,
                chat_jid=chat_jid,
                body=body,
                direction=direction,
                is_command=is_command,
                command_name=command_name,
            )
            msg.save()
        except Exception as e:
            logger.error(f"Failed to log message: {e}")

    @staticmethod
    def get_recent(session_id: str = "global", limit: int = 50) -> list[dict]:
        msgs = MessageLog.get_recent(session_id, limit)
        return [m.to_dict() for m in msgs]

    @staticmethod
    def get_chat(session_id: str, jid: str, limit: int = 100) -> list[dict]:
        msgs = MessageLog.get_by_jid(session_id, jid.split("@")[0], limit)
        return [m.to_dict() for m in msgs]

    @staticmethod
    def get_conversations(session_id: str = "global") -> list[dict]:
        return MessageLog.get_conversations(session_id)

    @staticmethod
    def search(session_id: str, query: str, limit: int = 50) -> list[dict]:
        msgs = MessageLog.search(session_id, query, limit)
        return [m.to_dict() for m in msgs]

    @staticmethod
    def get_stats(session_id: str = "global") -> dict:
        return MessageLog.get_stats(session_id)


message_service = MessageService()