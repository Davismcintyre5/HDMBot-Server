"""
server/routes/session_routes.py — Session management API routes
"""
import time
from flask import Blueprint, request, jsonify
from rich.console import Console

console = Console()
bp = Blueprint("sessions", __name__, url_prefix="/api/sessions")


def _get_session_service():
    from services.session_service import session_service
    return session_service

def _get_client_manager():
    from whatsapp.client_manager import client_manager
    return client_manager

def _get_socketio():
    from main import socketio
    return socketio


@bp.get("")
def list_sessions():
    """List all sessions from MongoDB, overlay runtime status."""
    service = _get_session_service()
    cm = _get_client_manager()
    sessions = service.get_all()

    for s in sessions:
        sid = s["session_id"]
        runtime_status = cm.get_status(sid)
        if runtime_status != "not_found":
            s["status"] = runtime_status

    return jsonify({"ok": True, "sessions": sessions, "total": len(sessions)})


@bp.get("/<session_id>")
def get_session(session_id: str):
    service = _get_session_service()
    cm = _get_client_manager()
    session = service.get(session_id)
    if not session:
        return jsonify({"error": "Session not found"}), 404

    runtime_status = cm.get_status(session_id)
    if runtime_status != "not_found":
        session["status"] = runtime_status

    return jsonify({"ok": True, "session": session})


@bp.post("")
def create_session():
    data = request.get_json(force=True, silent=True) or {}
    session_id = data.get("session_id", "").strip()
    session_name = data.get("session_name", "").strip() or session_id
    if not session_id:
        return jsonify({"error": "session_id is required"}), 400

    service = _get_session_service()
    result = service.create({
        "session_id": session_id,
        "session_name": session_name,
        "phone_number": data.get("phone_number", ""),
        "pairing_enabled": data.get("pairing_enabled", False),
        "pairing_phone": data.get("pairing_phone", ""),
        "db_path": data.get("db_path", f"whatsapp/sessions/store_{session_id}.db"),
        "is_default": False,
    })
    if result is None:
        return jsonify({"error": f"Session '{session_id}' already exists"}), 409

    console.print(f"[green][API] Session created: {session_id}[/green]")
    return jsonify({"ok": True, "session": result}), 201


@bp.put("/<session_id>")
def update_session(session_id: str):
    data = request.get_json(force=True, silent=True) or {}
    service = _get_session_service()
    result = service.update(session_id, data)
    if result is None:
        return jsonify({"error": "Session not found"}), 404
    return jsonify({"ok": True, "session": result})


@bp.delete("/<session_id>")
def delete_session(session_id: str):
    cm = _get_client_manager()
    service = _get_session_service()
    cm.disconnect(session_id)
    cm.remove(session_id)
    deleted = service.delete(session_id)
    if not deleted:
        return jsonify({"error": "Cannot delete default session or not found"}), 400
    console.print(f"[yellow][API] Session deleted: {session_id}[/yellow]")
    return jsonify({"ok": True, "message": f"Session '{session_id}' deleted"})


@bp.post("/<session_id>/connect")
def connect_session(session_id: str):
    cm = _get_client_manager()
    service = _get_session_service()
    session_data = service.get(session_id)
    if not session_data:
        return jsonify({"error": "Session not found"}), 404

    instance = cm.get_instance(session_id)
    if not instance:
        instance = cm.create_client(
            session_id=session_id,
            session_name=session_data.get("session_name", session_id),
            db_path=session_data.get("db_path", f"whatsapp/sessions/store_{session_id}.db"),
            phone_number=session_data.get("phone_number", ""),
            pairing_enabled=session_data.get("pairing_enabled", False),
            pairing_phone=session_data.get("pairing_phone", ""),
        )
    cm.connect(session_id)
    service.update_status(session_id, "connecting")

    try:
        _get_socketio().emit("session_status", {"session_id": session_id, "status": "connecting"})
    except Exception:
        pass

    console.print(f"[cyan][API] Connecting: {session_id}[/cyan]")
    return jsonify({"ok": True, "session_id": session_id, "status": "connecting"})


@bp.post("/<session_id>/disconnect")
def disconnect_session(session_id: str):
    cm = _get_client_manager()
    service = _get_session_service()
    cm.disconnect(session_id)
    service.update_status(session_id, "disconnected")

    try:
        _get_socketio().emit("session_status", {"session_id": session_id, "status": "disconnected"})
    except Exception:
        pass

    console.print(f"[yellow][API] Disconnected: {session_id}[/yellow]")
    return jsonify({"ok": True, "session_id": session_id, "status": "disconnected"})


@bp.post("/<session_id>/restart")
def restart_session(session_id: str):
    cm = _get_client_manager()
    service = _get_session_service()
    cm.disconnect(session_id)
    time.sleep(2)
    cm.connect(session_id)
    service.update_status(session_id, "connecting")

    try:
        _get_socketio().emit("session_status", {"session_id": session_id, "status": "connecting"})
    except Exception:
        pass

    console.print(f"[cyan][API] Restarting: {session_id}[/cyan]")
    return jsonify({"ok": True, "session_id": session_id, "status": "connecting"})


@bp.get("/<session_id>/qr")
def get_session_qr(session_id: str):
    service = _get_session_service()
    session_data = service.get(session_id)
    if not session_data:
        return jsonify({"error": "Session not found"}), 404
    qr = session_data.get("qr_string")
    return jsonify({"ok": True, "session_id": session_id, "qr": qr,
        "message": "QR available" if qr else "QR not available yet"})