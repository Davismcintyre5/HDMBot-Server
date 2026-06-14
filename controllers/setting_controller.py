"""
server/controllers/setting_controller.py — Settings endpoints
"""
from flask import Blueprint, request, jsonify
from services.setting_service import setting_service

bp = Blueprint("settings", __name__, url_prefix="/api/settings")


@bp.get("")
async def get_settings():
    session_id = request.args.get("session_id", "global")
    settings = await setting_service.get_all(session_id)
    return jsonify({"ok": True, "settings": settings})


@bp.get("/<key>")
async def get_setting(key: str):
    session_id = request.args.get("session_id", "global")
    value = await setting_service.get(session_id, key)
    return jsonify({"ok": True, "key": key, "value": value})


@bp.put("/<key>")
async def update_setting(key: str):
    data = request.get_json() or {}
    session_id = data.get("session_id", "global")
    value = data.get("value")

    if value is None:
        return jsonify({"error": "value is required"}), 400

    await setting_service.set(session_id, key, value)
    return jsonify({"ok": True, "key": key, "value": value})


@bp.post("/reset/<key>")
async def reset_setting(key: str):
    data = request.get_json() or {}
    session_id = data.get("session_id", "global")
    ok = await setting_service.reset(session_id, key)
    return jsonify({"ok": ok})