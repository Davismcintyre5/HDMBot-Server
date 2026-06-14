"""
server/services/session_service.py — Session management service (Sync)
"""
import os
import logging
from typing import Optional
from datetime import datetime
from server.models.session import Session
from server.config.settings import settings

logger = logging.getLogger(__name__)


class SessionService:

    @staticmethod
    def get_all() -> list[dict]:
        sessions = Session.find_all()
        return [s.to_dict() for s in sessions]

    @staticmethod
    def get(session_id: str) -> Optional[dict]:
        session = Session.find_by_id(session_id)
        return session.to_dict() if session else None

    @staticmethod
    def create(data: dict) -> Optional[dict]:
        existing = Session.find_by_id(data.get("session_id", ""))
        if existing:
            return None
        session_id = data["session_id"]
        session = Session(
            session_id=session_id,
            session_name=data.get("session_name", session_id),
            phone_number=data.get("phone_number", ""),
            pairing_enabled=data.get("pairing_enabled", False),
            pairing_phone=data.get("pairing_phone", ""),
            db_path=data.get("db_path", f"whatsapp/sessions/store_{session_id}.db"),
            status="disconnected",
            is_default=data.get("is_default", False),
        )
        session.save()
        logger.info(f"Session created: {session.session_id}")
        return session.to_dict()

    @staticmethod
    def update(session_id: str, data: dict) -> Optional[dict]:
        session = Session.find_by_id(session_id)
        if not session:
            return None
        for key in ["session_name", "phone_number", "pairing_enabled", "pairing_phone", "db_path"]:
            if key in data:
                setattr(session, key, data[key])
        session.updated_at = datetime.utcnow()
        session.save()
        return session.to_dict()

    @staticmethod
    def delete(session_id: str) -> bool:
        session = Session.find_by_id(session_id)
        if not session:
            return False
        if session.is_default:
            return False
        db_path = session.db_path
        if db_path:
            paths_to_try = [
                db_path,
                os.path.join(os.path.dirname(__file__), "..", db_path),
            ]
            for path in paths_to_try:
                abs_path = os.path.abspath(path)
                if os.path.exists(abs_path):
                    try:
                        os.remove(abs_path)
                        logger.info(f"Deleted session file: {abs_path}")
                    except Exception as e:
                        logger.warning(f"Failed to delete {abs_path}: {e}")
                    break
        session.delete()
        logger.info(f"Session deleted: {session_id}")
        return True

    @staticmethod
    def update_status(session_id: str, status: str) -> bool:
        return Session.update_status(session_id, status)

    @staticmethod
    def update_qr(session_id: str, qr_string: str) -> bool:
        return Session.update_qr(session_id, qr_string)

    @staticmethod
    def ensure_default_session():
        default_id = settings.SESSION_NAME
        existing = Session.find_by_id(default_id)
        if not existing:
            session = Session(
                session_id=default_id,
                session_name=f"{settings.BOT_NAME} (Default)",
                phone_number=settings.PAIRING_PHONE,
                pairing_enabled=settings.PAIRING_ENABLED,
                pairing_phone=settings.PAIRING_PHONE,
                db_path=settings.DB_PATH,
                status="disconnected",
                is_default=True,
            )
            session.save()
            logger.info(f"Default session created: {default_id}")
        return True


session_service = SessionService()