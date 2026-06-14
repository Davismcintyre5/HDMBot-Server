"""
server/routes/contact_routes.py — Contact CRUD API routes
"""
from flask import Blueprint, request, jsonify
from rich.console import Console

console = Console()
bp = Blueprint("contacts", __name__, url_prefix="/api/contacts")


def _get_service():
    from server.services.contact_service import contact_service
    return contact_service


@bp.get("")
def list_contacts():
    session_id = request.args.get("session_id", "global")
    service = _get_service()
    contacts = service.get_all(session_id)
    return jsonify({"ok": True, "contacts": contacts, "total": len(contacts)})


@bp.post("")
def create_contact():
    data = request.get_json(force=True, silent=True) or {}
    jid = data.get("jid", "").strip()
    name = data.get("name", "").strip()
    if not jid or not name:
        return jsonify({"error": "jid and name are required"}), 400

    service = _get_service()
    result = service.create(data)
    console.print(f"[green][API] Contact created: {name}[/green]")
    return jsonify({"ok": True, "contact": result}), 201


@bp.get("/<contact_id>")
def get_contact(contact_id: str):
    service = _get_service()
    contact = service.get(contact_id)
    if not contact:
        return jsonify({"error": "Contact not found"}), 404
    return jsonify({"ok": True, "contact": contact})


@bp.put("/<contact_id>")
def update_contact(contact_id: str):
    data = request.get_json(force=True, silent=True) or {}
    service = _get_service()
    result = service.update(contact_id, data)
    if result is None:
        return jsonify({"error": "Contact not found"}), 404
    return jsonify({"ok": True, "contact": result})


@bp.delete("/<contact_id>")
def delete_contact(contact_id: str):
    service = _get_service()
    deleted = service.delete(contact_id)
    if not deleted:
        return jsonify({"error": "Contact not found"}), 404
    console.print(f"[yellow][API] Contact deleted: {contact_id}[/yellow]")
    return jsonify({"ok": True, "message": "Contact deleted"})