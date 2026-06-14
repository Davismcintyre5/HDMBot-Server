"""
server/controllers/command_controller.py — Command CRUD endpoints
"""
from flask import Blueprint, request, jsonify
from services.command_service import command_service

bp = Blueprint("commands", __name__, url_prefix="/api/commands")


@bp.get("")
async def list_commands():
    session_id = request.args.get("session_id", "global")
    commands = await command_service.get_all(session_id)
    return jsonify({"ok": True, "commands": commands})


@bp.post("")
async def create_command():
    data = request.get_json() or {}
    name = data.get("name", "").strip()
    response = data.get("response", "").strip()

    if not name or not response:
        return jsonify({"error": "Name and response are required"}), 400

    result = await command_service.create(data)
    if result is None:
        return jsonify({"error": "Failed to create command"}), 500

    return jsonify({"ok": True, "command": result}), 201


@bp.put("/<command_id>")
async def update_command(command_id: str):
    data = request.get_json() or {}
    result = await command_service.update(command_id, data)
    if result is None:
        return jsonify({"error": "Command not found"}), 404
    return jsonify({"ok": True, "command": result})


@bp.delete("/<command_id>")
async def delete_command(command_id: str):
    deleted = await command_service.delete(command_id)
    if not deleted:
        return jsonify({"error": "Command not found"}), 404
    return jsonify({"ok": True})


@bp.patch("/<command_id>/toggle")
async def toggle_command(command_id: str):
    data = request.get_json() or {}
    enabled = data.get("enabled", True)
    result = await command_service.toggle(command_id, enabled)
    if result is None:
        return jsonify({"error": "Command not found"}), 404
    return jsonify({"ok": True, "command": result})