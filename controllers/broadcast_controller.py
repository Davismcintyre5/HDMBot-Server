"""
server/controllers/broadcast_controller.py — Broadcast CRUD endpoints
"""
from flask import Blueprint, request, jsonify
from services.broadcast_service import broadcast_service

bp = Blueprint("broadcasts", __name__, url_prefix="/api/broadcasts")


@bp.get("")
async def list_broadcasts():
    session_id = request.args.get("session_id", "global")
    broadcasts = await broadcast_service.get_all(session_id)
    return jsonify({"ok": True, "broadcasts": broadcasts})


@bp.post("")
async def create_broadcast():
    data = request.get_json() or {}
    name = data.get("name", "").strip()
    message = data.get("message", "").strip()

    if not name or not message:
        return jsonify({"error": "Name and message are required"}), 400

    result = await broadcast_service.create(data)
    return jsonify({"ok": True, "broadcast": result}), 201


@bp.put("/<broadcast_id>")
async def update_broadcast(broadcast_id: str):
    data = request.get_json() or {}
    result = await broadcast_service.update(broadcast_id, data)
    if result is None:
        return jsonify({"error": "Broadcast not found"}), 404
    return jsonify({"ok": True, "broadcast": result})


@bp.delete("/<broadcast_id>")
async def delete_broadcast(broadcast_id: str):
    deleted = await broadcast_service.delete(broadcast_id)
    if not deleted:
        return jsonify({"error": "Broadcast not found"}), 404
    return jsonify({"ok": True})


@bp.get("/stats")
async def broadcast_stats():
    session_id = request.args.get("session_id", "global")
    stats = await broadcast_service.get_stats(session_id)
    return jsonify({"ok": True, "stats": stats})