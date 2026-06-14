"""
server/controllers/dashboard_controller.py — Dashboard overview endpoint
"""
from flask import Blueprint, request, jsonify
from server.services.message_service import message_service
from server.services.broadcast_service import broadcast_service
from server.services.session_service import session_service

bp = Blueprint("dashboard", __name__, url_prefix="/api/dashboard")


@bp.get("/overview")
async def overview():
    session_id = request.args.get("session_id", "global")
    
    msg_stats = await message_service.get_stats(session_id)
    broadcast_stats = await broadcast_service.get_stats(session_id)
    sessions = await session_service.get_all()
    
    return jsonify({
        "ok": True,
        "overview": {
            "messages": msg_stats,
            "broadcasts": broadcast_stats,
            "active_sessions": len([s for s in sessions if s.get("status") == "connected"]),
            "total_sessions": len(sessions),
        },
    })