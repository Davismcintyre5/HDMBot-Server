"""
main.py — HDM BOT  |  Production Entry Point
PXXL-compatible with Gunicorn + eventlet WebSocket support
"""
from __future__ import annotations

import os
import sys
import signal
import threading
import time
import atexit
from datetime import datetime, timedelta

_current_dir = os.path.dirname(os.path.abspath(__file__))
if _current_dir not in sys.path:
    sys.path.insert(0, _current_dir)

from dotenv import load_dotenv
load_dotenv(os.path.join(_current_dir, ".env"))

from flask import Flask, jsonify, request
from flask_socketio import SocketIO
from flask_cors import CORS
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich import box

from config.settings import settings
from whatsapp.connection import (
    build_client, send_text, BOT_NAME, get_prefix, set_prefix, _COMMANDS,
)
from whatsapp.client_manager import client_manager

from routes.auth_routes import bp as auth_bp, init_auth
from routes.session_routes import bp as session_bp
from routes.settings_routes import bp as settings_bp
from routes.command_routes import bp as command_api_bp
from routes.autoreply_routes import bp as autoreply_bp
from routes.contact_routes import bp as contact_bp
from routes.broadcast_routes import bp as broadcast_bp
from routes.chat_routes import bp as chat_bp

from services.session_service import session_service
from services.settings_service import settings_service as user_settings_service
from keep_alive import start_keep_alive

console = Console()
app = Flask(__name__)
CORS(app, origins="*")
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='eventlet')

init_auth(os.getenv("JWT_SECRET", "hdm_bot_secret_change_this"), os.getenv("JWT_EXPIRE", "7d"))

app.register_blueprint(auth_bp)
app.register_blueprint(session_bp)
app.register_blueprint(settings_bp)
app.register_blueprint(command_api_bp)
app.register_blueprint(autoreply_bp)
app.register_blueprint(contact_bp)
app.register_blueprint(broadcast_bp)
app.register_blueprint(chat_bp)

_start_time = datetime.now()
_shutdown_event = threading.Event()
_client = None

@socketio.on('connect')
def handle_connect():
    socketio.emit('status_change', {'status': 'connected' if _client else 'disconnected'})

@socketio.on('disconnect')
def handle_disconnect(): pass

@socketio.on('send_message')
def handle_send_message(data):
    if not _client: return {'error': 'WhatsApp client not ready'}
    jid, text = data.get('jid', ''), data.get('text', '')
    if jid and text:
        send_text(_client, jid, text)
        return {'ok': True}
    return {'error': 'jid and text required'}

def emit_message(sender_str, chat_str, body, is_from_me):
    socketio.emit('new_message', {
        'from': sender_str, 'chat': chat_str, 'body': body,
        'direction': 'out' if is_from_me else 'in',
        'timestamp': datetime.now().strftime('%H:%M:%S'),
    })

@app.get("/")
def index():
    return jsonify({"bot": BOT_NAME, "version": "2.0.0", "status": "running",
        "uptime": str(datetime.now() - _start_time).split(".")[0],
        "prefix": get_prefix(), "commands": len(_COMMANDS)})

@app.get("/health")
def health():
    connected = _client is not None
    return jsonify({"status": "healthy" if connected else "starting",
        "timestamp": datetime.now().isoformat(),
        "uptime_seconds": int((datetime.now() - _start_time).total_seconds()),
        "whatsapp_connected": connected}), 200 if connected else 503

@app.get("/api")
def api_overview():
    routes_list = []
    for rule in sorted(app.url_map.iter_rules(), key=lambda r: r.rule):
        if rule.endpoint != "static":
            routes_list.append({"endpoint": rule.rule, "methods": sorted(rule.methods - {"HEAD", "OPTIONS"})})
    return jsonify({"bot": BOT_NAME, "api_version": "2.0.0", "endpoints": routes_list})

@app.post("/send")
def send():
    data = request.get_json(force=True, silent=True) or {}
    jid, text = data.get("jid", "").strip(), data.get("text", "").strip()
    if not jid or not text: return jsonify({"error": "jid and text are required"}), 400
    if _client is None: return jsonify({"error": "WhatsApp client not ready"}), 503
    try:
        send_text(_client, jid, text)
        emit_message("BOT", jid, text, True)
        return jsonify({"ok": True, "jid": jid, "text": text})
    except Exception as exc: return jsonify({"error": str(exc)}), 500

@app.get("/commands")
def list_commands():
    cmds = [{"name": n, "usage": f"{get_prefix()}{n}"} for n in sorted(_COMMANDS.keys())]
    return jsonify({"prefix": get_prefix(), "total": len(cmds), "commands": cmds})

@app.get("/prefix")
def get_prefix_route(): return jsonify({"prefix": get_prefix()})

@app.post("/prefix")
def set_prefix_route():
    data = request.get_json(force=True, silent=True) or {}
    new_prefix = data.get("prefix", "").strip()
    user_number = data.get("user_number", settings.PAIRING_PHONE or settings.OWNER_NUMBER or "")
    if not new_prefix or len(new_prefix) > 3: return jsonify({"error": "prefix required (max 3 chars)"}), 400
    from services.settings_service import settings_service
    settings_service.set_prefix(user_number, new_prefix[:3])
    return jsonify({"ok": True, "prefix": new_prefix[:3]})

@app.get("/api/messages")
def api_messages_list():
    from services.message_service import message_service
    session_id = request.args.get("session_id", settings.SESSION_NAME)
    limit = request.args.get("limit", 50, type=int)
    query = request.args.get("q", "").strip()
    messages = message_service.search(session_id, query, limit) if query else message_service.get_recent(session_id, limit)
    return jsonify({"ok": True, "messages": messages, "total": len(messages)})

@app.get("/api/messages/stats")
def api_messages_stats():
    from services.message_service import message_service
    session_id = request.args.get("session_id", settings.SESSION_NAME)
    stats = message_service.get_stats(session_id)
    return jsonify({"ok": True, "stats": stats})

@app.get("/api/dashboard/overview")
def api_dashboard_overview():
    sessions = session_service.get_all()
    connected = sum(1 for s in sessions if s.get("status") == "connected")
    all_users = user_settings_service.get_all_users()
    from services.message_service import message_service
    msg_stats = message_service.get_stats(settings.SESSION_NAME)
    return jsonify({"ok": True, "overview": {
        "messages": msg_stats,
        "broadcasts": {"total": 0, "draft": 0, "completed": 0, "failed": 0},
        "active_sessions": connected, "total_sessions": len(sessions),
        "total_users": len(all_users), "total_commands": len(_COMMANDS), "prefix": get_prefix(),
    }})

def _print_banner():
    console.clear()
    console.print(Panel(f"[bold magenta]{BOT_NAME}[/bold magenta] v2.0.0 [dim](Production)[/dim]\n[dim]WhatsApp Multi-Command Bot[/dim]",
        border_style="magenta", title="[bold]🚀 Starting[/bold]"))
    table = Table(title="Configuration", box=box.ROUNDED, title_style="bold cyan")
    table.add_column("Setting", style="cyan"); table.add_column("Value", style="green")
    table.add_row("Bot Name", BOT_NAME); table.add_row("Prefix", get_prefix())
    table.add_row("Commands", str(len(_COMMANDS))); table.add_row("Port", str(settings.FLASK_PORT))
    table.add_row("MongoDB", "Connected" if settings.MONGODB_URI else "Not set")
    console.print(table)
    console.print(f"\n[bold green]✓[/bold green] [dim]API →[/dim] [cyan]http://0.0.0.0:{settings.FLASK_PORT}[/cyan]")
    console.print(f"[dim]{'─'*50}[/dim]\n")

def _run_flask():
    port = int(os.getenv("PORT", settings.FLASK_PORT))
    console.print(f"[bold blue][HTTP][/bold blue] Production + WebSocket on port {port}")
    socketio.run(app, host="0.0.0.0", port=port, debug=False, allow_unsafe_werkzeug=True)

def _graceful_shutdown(signum=None, frame=None):
    if _shutdown_event.is_set(): return
    _shutdown_event.set()
    for s in session_service.get_all():
        session_service.update_status(s["session_id"], "disconnected")
    console.print(f"\n[yellow][SHUTDOWN] Shutting down...[/yellow]")
    sys.exit(0)

def main():
    global _client
    signal.signal(signal.SIGINT, _graceful_shutdown)
    signal.signal(signal.SIGTERM, _graceful_shutdown)
    atexit.register(lambda: _graceful_shutdown() if not _shutdown_event.is_set() else None)

    for d in ["uploads", "logs", "temp", "whatsapp/sessions"]:
        os.makedirs(d, exist_ok=True)

    _print_banner()
    start_keep_alive()
    session_service.ensure_default_session()

    def on_status_change(session_id, status):
        session_service.update_status(session_id, status)
        try: socketio.emit("session_status", {"session_id": session_id, "status": status})
        except Exception: pass

    client_manager.on_status_change(on_status_change)

    def on_any_message(client, msg, session_id):
        from whatsapp.connection import handle_message
        handle_message(client, msg)

    client_manager.on_message(on_any_message)

    threading.Thread(target=_run_flask, daemon=True, name="flask").start()

    console.print(f"[cyan][WA][/cyan] Building default client ({len(_COMMANDS)} commands)...")
    _client = build_client()

    client_manager.register_existing(
        session_id=settings.SESSION_NAME, client=_client,
        phone_number=settings.PAIRING_PHONE,
        pairing_enabled=settings.PAIRING_ENABLED,
        pairing_phone=settings.PAIRING_PHONE,
    )

    pairing = settings.PAIRING_PHONE
    console.print(f"[cyan][WA][/cyan] Connecting +{pairing}..." if (settings.PAIRING_ENABLED and pairing) else "[cyan][WA][/cyan] Connecting...")
    _client.connect()

    client_manager._set_status(settings.SESSION_NAME, "connected")
    session_service.update_status(settings.SESSION_NAME, "connected")

    console.print("[dim]Running. Ctrl+C to stop.[/dim]")

    try:
        while not _shutdown_event.is_set():
            _shutdown_event.wait(timeout=1)
    except KeyboardInterrupt:
        pass
    _graceful_shutdown()

if __name__ == "__main__":
    main()

# For Gunicorn + eventlet WebSocket support
application = app