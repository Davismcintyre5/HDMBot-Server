"""
server/controllers/contact_controller.py — Contact CRUD endpoints
"""
from flask import Blueprint, request, jsonify
from services.contact_service import contact_service

bp = Blueprint("contacts", __name__, url_prefix="/api/contacts")


@bp.get("")
async def list_contacts():
    session_id = request.args.get("session_id", "global")
    contacts = await contact_service.get_all(session_id)
    return jsonify({"ok": True, "contacts": contacts})


@bp.post("")
async def create_contact():
    data = request.get_json() or {}
    jid = data.get("jid", "").strip()
    name = data.get("name", "").strip()

    if not jid or not name:
        return jsonify({"error": "JID and name are required"}), 400

    result = await contact_service.create(data)
    return jsonify({"ok": True, "contact": result}), 201


@bp.put("/<contact_id>")
async def update_contact(contact_id: str):
    data = request.get_json() or {}
    result = await contact_service.update(contact_id, data)
    if result is None:
        return jsonify({"error": "Contact not found"}), 404
    return jsonify({"ok": True, "contact": result})


@bp.delete("/<contact_id>")
async def delete_contact(contact_id: str):
    deleted = await contact_service.delete(contact_id)
    if not deleted:
        return jsonify({"error": "Contact not found"}), 404
    return jsonify({"ok": True})