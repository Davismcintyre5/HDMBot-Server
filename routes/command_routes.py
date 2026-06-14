"""
server/routes/command_routes.py — Command CRUD API routes
"""
from flask import Blueprint, request, jsonify
from rich.console import Console

console = Console()
bp = Blueprint("commands_api", __name__, url_prefix="/api/commands")


def _get_service():
    from services.command_service import command_service
    return command_service


@bp.get("")
def list_commands():
    session_id = request.args.get("session_id", "global")
    service = _get_service()
    commands = service.get_all(session_id)
    return jsonify({"ok": True, "commands": commands, "total": len(commands)})


@bp.post("")
def create_command():
    data = request.get_json(force=True, silent=True) or {}
    name = data.get("name", "").strip()
    response = data.get("response", "").strip()
    if not name or not response:
        return jsonify({"error": "name and response are required"}), 400

    service = _get_service()
    result = service.create(data)
    if result is None:
        return jsonify({"error": "Command already exists"}), 409

    console.print(f"[green][API] Command created: {name}[/green]")
    return jsonify({"ok": True, "command": result}), 201


@bp.get("/<command_id>")
def get_command(command_id: str):
    service = _get_service()
    cmd = service.get(command_id)
    if not cmd:
        return jsonify({"error": "Command not found"}), 404
    return jsonify({"ok": True, "command": cmd})


@bp.put("/<command_id>")
def update_command(command_id: str):
    data = request.get_json(force=True, silent=True) or {}
    service = _get_service()
    result = service.update(command_id, data)
    if result is None:
        return jsonify({"error": "Command not found"}), 404
    return jsonify({"ok": True, "command": result})


@bp.delete("/<command_id>")
def delete_command(command_id: str):
    service = _get_service()
    deleted = service.delete(command_id)
    if not deleted:
        return jsonify({"error": "Command not found"}), 404
    console.print(f"[yellow][API] Command deleted: {command_id}[/yellow]")
    return jsonify({"ok": True, "message": "Command deleted"})


@bp.patch("/<command_id>/toggle")
def toggle_command(command_id: str):
    data = request.get_json(force=True, silent=True) or {}
    enabled = data.get("enabled")
    service = _get_service()
    result = service.toggle(command_id, enabled)
    if result is None:
        return jsonify({"error": "Command not found"}), 404
    return jsonify({"ok": True, "command": result})