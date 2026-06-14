"""
server/routes/chat_routes.py — Chat API routes
"""
import traceback
from flask import Blueprint, request, jsonify
from rich.console import Console

console = Console()
bp = Blueprint("chat", __name__, url_prefix="/api")


def _get_service():
    from services.message_service import message_service
    return message_service

def _get_client_manager():
    from whatsapp.client_manager import client_manager
    return client_manager

def _get_settings():
    from config.settings import settings
    return settings

def _get_default_client():
    try:
        from main import _client
        return _client
    except:
        return None


@bp.get("/chats")
def list_conversations():
    """Get list of unique conversations."""
    settings = _get_settings()
    session_id = request.args.get("session_id", settings.SESSION_NAME)
    service = _get_service()
    conversations = service.get_conversations(session_id)
    
    chats = []
    for c in conversations:
        chats.append({
            "jid": c.get("jid", c.get("_id", "")),
            "last_message": c.get("last_message", ""),
            "timestamp": str(c.get("timestamp", "")),
            "message_count": c.get("count", c.get("message_count", 0)),
        })
    
    return jsonify({"ok": True, "chats": chats, "total": len(chats)})


@bp.get("/chat/<path:jid>")
def get_chat_messages(jid: str):
    """Get messages for a specific chat/JID."""
    settings = _get_settings()
    session_id = request.args.get("session_id", settings.SESSION_NAME)
    limit = request.args.get("limit", 100, type=int)
    service = _get_service()
    
    messages = service.get_chat(session_id, jid, limit)
    return jsonify({"ok": True, "messages": messages, "total": len(messages)})


@bp.post("/chat/send")
def send_chat_message():
    """Send a message and log it."""
    data = request.get_json(force=True, silent=True) or {}
    jid = data.get("jid", "").strip()
    text = data.get("text", "").strip()
    settings = _get_settings()
    session_id = data.get("session_id", settings.SESSION_NAME)
    
    if not jid or not text:
        return jsonify({"error": "jid and text are required"}), 400
    
    try:
        # Get client from manager, fallback to default
        cm = _get_client_manager()
        client = cm.get_client(session_id)
        if not client:
            client = _get_default_client()
        
        if not client:
            return jsonify({"error": "No WhatsApp client connected"}), 503
        
        from whatsapp.connection import send_text
        send_text(client, jid, text)
        
        # Log the sent message
        service = _get_service()
        service.log_message(
            session_id=session_id,
            from_jid="BOT",
            chat_jid=jid,
            body=text,
            direction="out",
        )
        
        console.print(f"[cyan][Chat] Sent to {jid}: {text[:50]}[/cyan]")
        return jsonify({"ok": True, "jid": jid, "text": text})
        
    except Exception as exc:
        traceback.print_exc()
        console.print(f"[red][Chat] Send error: {exc}[/red]")
        return jsonify({"error": str(exc)}), 500