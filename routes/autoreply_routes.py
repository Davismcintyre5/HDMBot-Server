"""
server/routes/autoreply_routes.py — Auto-reply rules CRUD API
"""
from flask import Blueprint, request, jsonify
from rich.console import Console

console = Console()
bp = Blueprint("autoreplies", __name__, url_prefix="/api/autoreplies")


def _get_service():
    from server.services.autoreply_service import autoreply_service
    return autoreply_service


@bp.get("")
def list_rules():
    session_id = request.args.get("session_id", "global")
    service = _get_service()
    rules = service.get_all(session_id)
    return jsonify({"ok": True, "rules": rules, "total": len(rules)})


@bp.post("")
def create_rule():
    data = request.get_json(force=True, silent=True) or {}
    name = data.get("name", "").strip()
    trigger = data.get("trigger", "").strip()
    response = data.get("response", "").strip()
    if not name or not trigger or not response:
        return jsonify({"error": "name, trigger, and response are required"}), 400

    service = _get_service()
    result = service.create(data)
    console.print(f"[green][API] Rule created: {name}[/green]")
    return jsonify({"ok": True, "rule": result}), 201


@bp.get("/<rule_id>")
def get_rule(rule_id: str):
    service = _get_service()
    rule = service.get(rule_id)
    if not rule:
        return jsonify({"error": "Rule not found"}), 404
    return jsonify({"ok": True, "rule": rule})


@bp.put("/<rule_id>")
def update_rule(rule_id: str):
    data = request.get_json(force=True, silent=True) or {}
    service = _get_service()
    result = service.update(rule_id, data)
    if result is None:
        return jsonify({"error": "Rule not found"}), 404
    return jsonify({"ok": True, "rule": result})


@bp.delete("/<rule_id>")
def delete_rule(rule_id: str):
    service = _get_service()
    deleted = service.delete(rule_id)
    if not deleted:
        return jsonify({"error": "Rule not found"}), 404
    console.print(f"[yellow][API] Rule deleted: {rule_id}[/yellow]")
    return jsonify({"ok": True, "message": "Rule deleted"})


@bp.patch("/<rule_id>/toggle")
def toggle_rule(rule_id: str):
    service = _get_service()
    result = service.toggle(rule_id)
    if result is None:
        return jsonify({"error": "Rule not found"}), 404
    return jsonify({"ok": True, "rule": result})