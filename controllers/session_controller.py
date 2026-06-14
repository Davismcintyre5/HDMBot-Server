"""
server/controllers/session_controller.py — Session management endpoints
"""
from flask import Blueprint, request, jsonify
from services.session_service import session_service

bp = Blueprint("sessions", __name__, url_prefix="/api/sessions")


@bp.get("")
async def list_sessions():
    sessions = await session_service.get_all()
    return jsonify({"ok": True, "sessions": sessions})


@bp.get("/<session_id>")
async def get_session(session_id: str):
    session = await session_service.get(session_id)
    if session is None:
        return jsonify({"error": "Session not found"}), 404
    return jsonify({"ok": True, "session": session})


@bp.post("")
async def create_session():
    data = request.get_json() or {}
    session_id = data.get("session_id", "").strip()
    session_name = data.get("session_name", "").strip()

    if not session_id or not session_name:
        return jsonify({"error": "session_id and session_name are required"}), 400

    result = await session_service.create(data)
    return jsonify({"ok": True, "session": result}), 201


@bp.put("/<session_id>")
async def update_session(session_id: str):
    data = request.get_json() or {}
    result = await session_service.update(session_id, data)
    if result is None:
        return jsonify({"error": "Session not found"}), 404
    return jsonify({"ok": True, "session": result})


@bp.delete("/<session_id>")
async def delete_session(session_id: str):
    deleted = await session_service.delete(session_id)
    if not deleted:
        return jsonify({"error": "Session not found"}), 404
    return jsonify({"ok": True})