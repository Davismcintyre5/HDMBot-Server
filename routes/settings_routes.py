"""
server/routes/settings_routes.py — Per-user settings API routes
"""
from flask import Blueprint, request, jsonify
from rich.console import Console

console = Console()
bp = Blueprint("settings", __name__, url_prefix="/api/settings")


def _get_service():
    from server.services.settings_service import settings_service
    return settings_service

def _get_default_user():
    """Get default user number from env."""
    import os
    from server.config.settings import settings
    return settings.PAIRING_PHONE or settings.OWNER_NUMBER or ""


# ===================================================================
# USER SETTINGS
# ===================================================================

@bp.get("")
def get_user_settings():
    """Get settings for a user."""
    user_number = request.args.get("user_number", _get_default_user())
    service = _get_service()
    settings = service.get_or_create(user_number)
    return jsonify({
        "ok": True,
        "user_number": user_number,
        "settings": {
            "commandPrefix": settings.get("prefix", "."),
            "mode": settings.get("mode", "public"),
            "auto_reply": settings.get("auto_reply", False),
            "alwaysOnline": settings.get("always_online", False),
            "autoViewStatus": settings.get("auto_view_status", False),
            "antiDelete": settings.get("anti_delete", True),
            "antiBug": settings.get("anti_bug", False),
            "footerText": settings.get("footer_text", "🤖 HDM BOT"),
        }
    })


@bp.get("/<key>")
def get_setting(key: str):
    """Get a specific setting."""
    user_number = request.args.get("user_number", _get_default_user())
    service = _get_service()
    
    key_map = {
        "commandPrefix": "prefix", "alwaysOnline": "always_online",
        "autoViewStatus": "auto_view_status", "antiDelete": "anti_delete",
        "antiBug": "anti_bug", "footerText": "footer_text",
    }
    db_key = key_map.get(key, key)
    value = service.get_setting(user_number, db_key)
    
    return jsonify({"ok": True, "user_number": user_number, "key": key, "value": value})


@bp.put("/<key>")
def update_setting(key: str):
    """Update a specific setting."""
    data = request.get_json(force=True, silent=True) or {}
    user_number = data.get("user_number", _get_default_user())
    
    if "value" not in data:
        return jsonify({"error": "value is required"}), 400
    
    value = data["value"]
    service = _get_service()
    
    key_map = {
        "commandPrefix": "prefix", "alwaysOnline": "always_online",
        "autoViewStatus": "auto_view_status", "antiDelete": "anti_delete",
        "antiBug": "anti_bug", "footerText": "footer_text",
        "auto_reply": "auto_reply",
    }
    db_key = key_map.get(key, key)
    
    service.set_setting(user_number, db_key, value)
    console.print(f"[dim]Setting: {user_number}/{key} = {value}[/dim]")
    
    return jsonify({"ok": True, "user_number": user_number, "key": key, "value": value})


@bp.post("/reset/<key>")
def reset_setting(key: str):
    """Reset a setting to default."""
    data = request.get_json(force=True, silent=True) or {}
    user_number = data.get("user_number", _get_default_user())
    
    defaults = {
        "commandPrefix": ".", "mode": "public", "auto_reply": False,
        "alwaysOnline": False, "autoViewStatus": False,
        "antiDelete": True, "antiBug": False, "footerText": "🤖 HDM BOT",
    }
    
    key_map = {
        "commandPrefix": "prefix", "alwaysOnline": "always_online",
        "autoViewStatus": "auto_view_status", "antiDelete": "anti_delete",
        "antiBug": "anti_bug", "footerText": "footer_text",
    }
    db_key = key_map.get(key, key)
    default_val = defaults.get(key)
    
    if default_val is not None:
        service = _get_service()
        service.set_setting(user_number, db_key, default_val)
    
    return jsonify({"ok": True, "key": key, "reset": True})


# ===================================================================
# GROUP SETTINGS (per user)
# ===================================================================

@bp.get("/<user_number>/welcome")
def get_welcome(user_number: str):
    service = _get_service()
    welcome = service.get_welcome(user_number)
    return jsonify({"ok": True, "user_number": user_number, "welcome": welcome})


@bp.put("/<user_number>/welcome")
def set_welcome(user_number: str):
    data = request.get_json(force=True, silent=True) or {}
    service = _get_service()
    ok = service.set_welcome(user_number, enabled=data.get("enabled"), message=data.get("message"))
    return jsonify({"ok": ok})


@bp.get("/<user_number>/goodbye")
def get_goodbye(user_number: str):
    service = _get_service()
    goodbye = service.get_goodbye(user_number)
    return jsonify({"ok": True, "user_number": user_number, "goodbye": goodbye})


@bp.put("/<user_number>/goodbye")
def set_goodbye(user_number: str):
    data = request.get_json(force=True, silent=True) or {}
    service = _get_service()
    ok = service.set_goodbye(user_number, enabled=data.get("enabled"), message=data.get("message"))
    return jsonify({"ok": ok})


@bp.get("/<user_number>/antilink")
def get_antilink(user_number: str):
    service = _get_service()
    antilink = service.get_antilink(user_number)
    return jsonify({"ok": True, "user_number": user_number, "antilink": antilink})


@bp.put("/<user_number>/antilink")
def set_antilink(user_number: str):
    data = request.get_json(force=True, silent=True) or {}
    service = _get_service()
    ok = service.set_antilink(user_number, enabled=data.get("enabled", False), action=data.get("action", "delete"))
    return jsonify({"ok": ok})


@bp.get("/<user_number>/badwords")
def get_bad_words(user_number: str):
    service = _get_service()
    words = service.get_bad_words(user_number)
    return jsonify({"ok": True, "user_number": user_number, "bad_words": words, "total": len(words)})


@bp.post("/<user_number>/badwords")
def add_bad_word(user_number: str):
    data = request.get_json(force=True, silent=True) or {}
    word = data.get("word", "").strip().lower()
    if not word: return jsonify({"error": "word is required"}), 400
    service = _get_service()
    service.add_bad_word(user_number, word)
    return jsonify({"ok": True, "word": word})


@bp.delete("/<user_number>/badwords/<word>")
def remove_bad_word(user_number: str, word: str):
    service = _get_service()
    service.remove_bad_word(user_number, word.lower())
    return jsonify({"ok": True, "word": word})


@bp.get("/<user_number>/muted")
def get_muted(user_number: str):
    service = _get_service()
    muted = service.get_muted_users(user_number)
    return jsonify({"ok": True, "user_number": user_number, "muted": muted})


@bp.get("/all")
def get_all_users_settings():
    service = _get_service()
    users = service.get_all_users()
    return jsonify({"ok": True, "users": users, "total": len(users)})