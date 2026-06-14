"""
server/routes/broadcast_routes.py — Broadcast CRUD API routes
"""
from flask import Blueprint, request, jsonify
from rich.console import Console

console = Console()
bp = Blueprint("broadcasts", __name__, url_prefix="/api/broadcasts")


def _get_service():
    from services.broadcast_service import broadcast_service
    return broadcast_service


@bp.get("")
def list_broadcasts():
    session_id = request.args.get("session_id", "global")
    service = _get_service()
    broadcasts = service.get_all(session_id)
    return jsonify({"ok": True, "broadcasts": broadcasts, "total": len(broadcasts)})


@bp.post("")
def create_broadcast():
    data = request.get_json(force=True, silent=True) or {}
    name = data.get("name", "").strip()
    message = data.get("message", "").strip()
    if not name or not message:
        return jsonify({"error": "name and message are required"}), 400

    service = _get_service()
    result = service.create(data)
    console.print(f"[green][API] Broadcast created: {name}[/green]")
    return jsonify({"ok": True, "broadcast": result}), 201


@bp.get("/<broadcast_id>")
def get_broadcast(broadcast_id: str):
    service = _get_service()
    broadcast = service.get(broadcast_id)
    if not broadcast:
        return jsonify({"error": "Broadcast not found"}), 404
    return jsonify({"ok": True, "broadcast": broadcast})


@bp.put("/<broadcast_id>")
def update_broadcast(broadcast_id: str):
    data = request.get_json(force=True, silent=True) or {}
    service = _get_service()
    result = service.update(broadcast_id, data)
    if result is None:
        return jsonify({"error": "Broadcast not found"}), 404
    return jsonify({"ok": True, "broadcast": result})


@bp.delete("/<broadcast_id>")
def delete_broadcast(broadcast_id: str):
    service = _get_service()
    deleted = service.delete(broadcast_id)
    if not deleted:
        return jsonify({"error": "Broadcast not found"}), 404
    console.print(f"[yellow][API] Broadcast deleted: {broadcast_id}[/yellow]")
    return jsonify({"ok": True, "message": "Broadcast deleted"})


@bp.get("/stats")
def broadcast_stats():
    session_id = request.args.get("session_id", "global")
    service = _get_service()
    stats = service.get_stats(session_id)
    return jsonify({"ok": True, "stats": stats})