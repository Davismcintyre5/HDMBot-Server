"""
server/controllers/message_controller.py — Message log endpoints
"""
from flask import Blueprint, request, jsonify
from server.services.message_service import message_service

bp = Blueprint("messages", __name__, url_prefix="/api/messages")


@bp.get("")
async def list_messages():
    session_id = request.args.get("session_id", "global")
    limit = request.args.get("limit", 50, type=int)
    query = request.args.get("q", "").strip()

    if query:
        messages = await message_service.search(session_id, query, limit)
    else:
        messages = await message_service.get_recent(session_id, limit)

    return jsonify({"ok": True, "messages": messages})


@bp.get("/stats")
async def message_stats():
    session_id = request.args.get("session_id", "global")
    stats = await message_service.get_stats(session_id)
    return jsonify({"ok": True, "stats": stats})