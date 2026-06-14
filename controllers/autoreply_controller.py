"""
server/controllers/autoreply_controller.py — Auto-reply CRUD endpoints
"""
from flask import Blueprint, request, jsonify
from server.services.autoreply_service import autoreply_service

bp = Blueprint("autoreplies", __name__, url_prefix="/api/autoreplies")


@bp.get("")
async def list_autoreplies():
    session_id = request.args.get("session_id", "global")
    rules = await autoreply_service.get_all(session_id)
    return jsonify({"ok": True, "rules": rules})


@bp.post("")
async def create_autoreply():
    data = request.get_json() or {}
    name = data.get("name", "").strip()
    trigger = data.get("trigger", "").strip()
    response = data.get("response", "").strip()

    if not name or not trigger or not response:
        return jsonify({"error": "Name, trigger, and response are required"}), 400

    result = await autoreply_service.create(data)
    if result is None:
        return jsonify({"error": "Failed to create auto-reply"}), 500

    return jsonify({"ok": True, "rule": result}), 201


@bp.put("/<rule_id>")
async def update_autoreply(rule_id: str):
    data = request.get_json() or {}
    result = await autoreply_service.update(rule_id, data)
    if result is None:
        return jsonify({"error": "Auto-reply not found"}), 404
    return jsonify({"ok": True, "rule": result})


@bp.delete("/<rule_id>")
async def delete_autoreply(rule_id: str):
    deleted = await autoreply_service.delete(rule_id)
    if not deleted:
        return jsonify({"error": "Auto-reply not found"}), 404
    return jsonify({"ok": True})