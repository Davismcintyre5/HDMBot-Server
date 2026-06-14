"""
server/services/contact_service.py — Contact CRUD service
"""
import logging
from typing import Optional
from server.models.contact import Contact

logger = logging.getLogger(__name__)


class ContactService:

    @staticmethod
    def get_all(session_id: str = "global") -> list[dict]:
        return [c.to_dict() for c in Contact.find_all(session_id)]

    @staticmethod
    def get(contact_id: str) -> Optional[dict]:
        contact = Contact.find_by_id(contact_id)
        return contact.to_dict() if contact else None

    @staticmethod
    def create(data: dict) -> Optional[dict]:
        contact = Contact(
            jid=data["jid"], name=data["name"],
            contact_type=data.get("contact_type", "individual"),
            phone_number=data.get("phone_number", ""),
            session_id=data.get("session_id", "global"),
            notes=data.get("notes", ""), tags=data.get("tags", []),
        )
        contact.save()
        return contact.to_dict()

    @staticmethod
    def update(contact_id: str, data: dict) -> Optional[dict]:
        contact = Contact.find_by_id(contact_id)
        if not contact: return None
        for key in ["name", "contact_type", "phone_number", "is_blocked", "is_favorite", "tags", "notes"]:
            if key in data: setattr(contact, key, data[key])
        contact.updated_at = datetime.utcnow()
        contact.save()
        return contact.to_dict()

    @staticmethod
    def delete(contact_id: str) -> bool:
        contact = Contact.find_by_id(contact_id)
        if contact: return contact.delete()
        return False


from datetime import datetime
contact_service = ContactService()