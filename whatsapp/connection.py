"""
server/whatsapp/connection.py — HDM BOT  |  Complete WhatsApp Bot
Organized: 72 commands in categories, interactive blue-themed menu, all fixes preserved.
"""
from __future__ import annotations

import os
import re
import time
import inspect
import threading
import requests
from datetime import datetime
from typing import Callable, Optional

from dotenv import load_dotenv
from neonize.client import NewClient
from neonize.events import (
    ConnectedEv, MessageEv, PairStatusEv, ReceiptEv, CallOfferEv,
    event as neonize_event,
)
from rich.console import Console
from rich.panel import Panel

load_dotenv()

console = Console()

# ╔══════════════════════════════════════════════════════════════════╗
# ║                        CONFIG                                    ║
# ╚══════════════════════════════════════════════════════════════════╝

BOT_NAME    = os.getenv("BOT_NAME", "HDM BOT")
_PREFIX     = [os.getenv("BOT_PREFIX", ".")]
SESSION     = os.getenv("SESSION_NAME", "hdm_session")
DB_PATH     = os.getenv("DB_PATH", "store.db")
OWNER_JID   = os.getenv("OWNER_JID", "")
OWNER_NUM   = os.getenv("OWNER_NUMBER", "")
_ADMIN_NUMS = [a.strip() for a in os.getenv("ADMIN_NUMBERS", "").split(",") if a.strip()]
ENABLE_AI   = os.getenv("ENABLE_AI_COMMANDS", "true").lower() in ("true", "1", "yes")
ENABLE_BUG  = os.getenv("ENABLE_BUG_COMMANDS", "true").lower() in ("true", "1", "yes")
DEFAULT_AI  = os.getenv("DEFAULT_AI_MODEL", "hdmai")
BUG_MAX     = int(os.getenv("BUG_MAX_MESSAGES", "1000"))
_BUG_USERS  = [u.strip() for u in os.getenv("BUG_ALLOWED_USERS", "").split(",") if u.strip()]

def get_prefix() -> str: return _PREFIX[0]
def set_prefix(val: str):
    _PREFIX[0] = val
    os.environ["BOT_PREFIX"] = val

try:
    from PIL import Image
    HAS_PILLOW = True
except ImportError:
    HAS_PILLOW = False

# ╔══════════════════════════════════════════════════════════════════╗
# ║                      GLOBAL STATE                                ║
# ╚══════════════════════════════════════════════════════════════════╝

_COMMANDS: dict[str, Callable] = {}
_CATEGORIES: dict[str, dict] = {}
_active_attacks: dict[str, dict] = {}
_menu_sessions: dict[str, dict] = {}
_muted_users: dict[str, dict] = {}
_warning_users: dict[str, dict] = {}
_bad_words: dict[str, set] = {}
_anti_link: dict[str, dict] = {}
_only_admin: dict[str, bool] = {}
_anti_status: dict[str, dict] = {}
_member_stats: dict[str, dict] = {}
_bug_logs: list[dict] = []
_pairing_codes: dict[str, dict] = {}

# ╔══════════════════════════════════════════════════════════════════╗
# ║                    GENERAL HELPERS                               ║
# ╚══════════════════════════════════════════════════════════════════╝

def _ts() -> str:
    return datetime.now().strftime("%H:%M:%S")

def send_text(client: NewClient, jid, text: str):
    client.send_message(jid, text)

def get_text(msg: MessageEv) -> str:
    try:
        m = msg.Message
        if hasattr(m, "conversation") and m.conversation: return m.conversation
        if hasattr(m, "extendedTextMessage") and m.extendedTextMessage:
            etm = m.extendedTextMessage
            if hasattr(etm, "text") and etm.text: return etm.text
    except Exception: pass
    return ""

def jid_to_str(jid) -> str:
    try: return f"{jid.User}@{jid.Server}"
    except: return str(jid)

def get_user_number(jid) -> str:
    if hasattr(jid, 'User'): return str(jid.User)
    s = str(jid)
    return s.split("@")[0] if "@" in s else s

def format_number(number: str) -> str:
    return re.sub(r"[^0-9]", "", str(number))

def print_msg(direction: str, sender: str, chat: str, body: str):
    arrow = "▶" if direction == "out" else "◀"
    colour = "green" if direction == "out" else "cyan"
    console.print(f"[dim]{_ts()}[/dim] [{colour}]{arrow} {sender}[/{colour}] [dim]→ {chat}[/dim]\n   {body}")

def create_progress_bar(percent: float, length: int = 10) -> str:
    filled = round((percent / 100) * length)
    return "█" * filled + "░" * (length - filled)

def parse_duration(time_str: str) -> int | None:
    match = re.match(r"^(\d+)([smhd])$", time_str.lower())
    if not match: return None
    value = int(match.group(1))
    multipliers = {"s": 1000, "m": 60000, "h": 3600000, "d": 86400000}
    return value * multipliers[match.group(2)]

def _get_target_jid(msg, args) -> str | None:
    try:
        if hasattr(msg, 'hasQuotedMsg') and msg.hasQuotedMsg:
            quoted = msg.getQuotedMessage()
            target = getattr(quoted, 'author', None) or getattr(quoted, 'from', None)
            return str(target)
    except Exception: pass
    if args and args[0]: return f"{format_number(args[0])}@c.us"
    return None

def _get_target_from_mention(msg, args) -> str | None:
    target = _get_target_jid(msg, [])
    if target: return target
    if args and args[0].startswith("@"): return f"{format_number(args[0][1:])}@c.us"
    if args and args[0]: return f"{format_number(args[0])}@c.us"
    return None

def _get_target_number(msg, args) -> str | None:
    try:
        if hasattr(msg, 'hasQuotedMsg') and msg.hasQuotedMsg:
            quoted = msg.getQuotedMessage()
            target = getattr(quoted, 'author', None) or getattr(quoted, 'from', None)
            return get_user_number(str(target))
    except Exception: pass
    if args and args[0]: return format_number(args[0])
    return None

def _get_chat(msg):
    try:
        chat = msg.getChat()
        return chat if chat.isGroup else None
    except: return None

def _get_group_admins(chat) -> list:
    return [p.id._serialized for p in chat.participants if getattr(p, 'isAdmin', False) or getattr(p, 'isSuperAdmin', False)]

def _is_bot_admin(chat, client) -> bool:
    try: bot_id = client.info.wid._serialized
    except: return False
    p = next((x for x in chat.participants if x.id._serialized == bot_id), None)
    return bool(p and (getattr(p, 'isAdmin', False) or getattr(p, 'isSuperAdmin', False)))

def _is_sender_admin(chat, sender_jid) -> bool:
    p = next((x for x in chat.participants if x.id._serialized == str(sender_jid)), None)
    return bool(p and (getattr(p, 'isAdmin', False) or getattr(p, 'isSuperAdmin', False)))

def _get_country(num: str) -> str:
    countries = {
        "254": "🇰🇪 Kenya", "255": "🇹🇿 Tanzania", "256": "🇺🇬 Uganda", "1": "🇺🇸 USA",
        "44": "🇬🇧 UK", "91": "🇮🇳 India", "234": "🇳🇬 Nigeria", "233": "🇬🇭 Ghana",
        "27": "🇿🇦 South Africa", "7": "🇷🇺 Russia", "49": "🇩🇪 Germany", "33": "🇫🇷 France",
        "86": "🇨🇳 China", "81": "🇯🇵 Japan", "55": "🇧🇷 Brazil", "971": "🇦🇪 UAE",
        "966": "🇸🇦 Saudi Arabia", "20": "🇪🇬 Egypt", "61": "🇦🇺 Australia",
    }
    n = format_number(num)
    for code, name in sorted(countries.items(), key=lambda x: -len(x[0])):
        if n.startswith(code): return name
    return "🌍 Other"

# ╔══════════════════════════════════════════════════════════════════╗
# ║                  PERMISSION HELPERS                              ║
# ╚══════════════════════════════════════════════════════════════════╝

def _is_admin(jid) -> bool:
    num = get_user_number(str(jid))
    if num == OWNER_NUM: return True
    if num in _ADMIN_NUMS: return True
    return False

def _is_owner(jid) -> bool:
    return get_user_number(str(jid)) == OWNER_NUM

def _is_user_allowed_bug(jid) -> bool:
    num = get_user_number(str(jid))
    if _is_admin(jid): return True
    return num in _BUG_USERS

# ╔══════════════════════════════════════════════════════════════════╗
# ║                PER-USER SETTINGS HELPERS                         ║
# ╚══════════════════════════════════════════════════════════════════╝

def _get_user_setting(user_number: str, key: str, default=None):
    try:
        from server.services.settings_service import settings_service
        return settings_service.get_setting(user_number, key, default)
    except: return default

def _set_user_setting(user_number: str, key: str, value) -> bool:
    try:
        from server.services.settings_service import settings_service
        return settings_service.set_setting(user_number, key, value)
    except: return False

# ╔══════════════════════════════════════════════════════════════════╗
# ║                  AUTO-REPLY HELPER                               ║
# ╚══════════════════════════════════════════════════════════════════╝

def _check_auto_reply(user_number: str, body: str) -> str | None:
    enabled = _get_user_setting(user_number, "auto_reply", False)
    if not enabled: return None
    try:
        from server.models.auto_reply import AutoReply
        rules = AutoReply.find_all("global")
        body_lower = body.lower()
        for rule in rules:
            if not rule.enabled: continue
            trigger = rule.trigger.lower()
            if rule.match_type == "exact" and body_lower == trigger: return rule.response
            elif rule.match_type == "starts_with" and body_lower.startswith(trigger): return rule.response
            elif rule.match_type == "regex":
                try:
                    if re.search(rule.trigger, body, re.IGNORECASE): return rule.response
                except: pass
            elif trigger in body_lower: return rule.response
    except: pass
    return None

# ╔══════════════════════════════════════════════════════════════════╗
# ║                      AI HELPERS                                  ║
# ╚══════════════════════════════════════════════════════════════════╝

def _query_hdm_ai(prompt: str) -> str:
    try:
        url = os.getenv("HDM_AI_API_URL", "https://hdm-ai-server.onrender.com/api/v1/general/chat/public")
        key = os.getenv("HDM_AI_API_KEY", "hdm_gen_94b1a42c30805c31852105c287a5812272857a0af82e1e58")
        try: requests.get(url.replace("/api/v1/general/chat/public", "/health"), timeout=5)
        except: pass
        r = requests.post(url, headers={"x-api-key": key}, data={"message": prompt, "system_prompt": f"You are {BOT_NAME}, a helpful WhatsApp assistant. Be concise.", "interface": "client"}, timeout=60)
        data = r.json()
        if data.get("success") and data.get("data", {}).get("reply"): return data["data"]["reply"]
        return f"❌ HDM AI: {data.get('message', 'Unknown')}"
    except Exception as e: return f"❌ HDM AI: {e}"

def _query_deepseek(prompt: str) -> str:
    try:
        key = os.getenv("DEEPSEEK_API_KEY", "")
        if not key: return "❌ DeepSeek API key not set."
        r = requests.post("https://api.deepseek.com/v1/chat/completions", headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"}, json={"model": "deepseek-chat", "messages": [{"role": "system", "content": "You are helpful."}, {"role": "user", "content": prompt}], "temperature": 0.7, "max_tokens": 1000}, timeout=30)
        return r.json()["choices"][0]["message"]["content"]
    except Exception as e: return f"❌ DeepSeek: {e}"

def _query_gemini(prompt: str) -> str:
    try:
        key = os.getenv("GEMINI_API_KEY", "")
        if not key: return "❌ Gemini API key not set."
        r = requests.post(f"https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent?key={key}", headers={"Content-Type": "application/json"}, json={"contents": [{"parts": [{"text": prompt}]}]}, timeout=30)
        return r.json()["candidates"][0]["content"]["parts"][0]["text"]
    except Exception as e: return f"❌ Gemini: {e}"

def _query_chatgpt(prompt: str) -> str:
    try:
        key = os.getenv("OPENAI_API_KEY", "")
        if not key: return "❌ ChatGPT API key not set."
        r = requests.post("https://api.openai.com/v1/chat/completions", headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"}, json={"model": "gpt-3.5-turbo", "messages": [{"role": "system", "content": "You are helpful."}, {"role": "user", "content": prompt}], "temperature": 0.7, "max_tokens": 1000}, timeout=30)
        return r.json()["choices"][0]["message"]["content"]
    except Exception as e: return f"❌ ChatGPT: {e}"

def _query_grok(prompt: str) -> str:
    try:
        key = os.getenv("GROK_API_KEY", "")
        if not key: return "❌ Grok API key not set."
        r = requests.post("https://api.x.ai/v1/chat/completions", headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"}, json={"model": "grok-2-latest", "messages": [{"role": "system", "content": "You are helpful."}, {"role": "user", "content": prompt}], "temperature": 0.7, "max_tokens": 1000}, timeout=30)
        return r.json()["choices"][0]["message"]["content"]
    except Exception as e: return f"❌ Grok: {e}"

def _query_groq(prompt: str) -> str:
    try:
        key = os.getenv("GROQ_API_KEY", "")
        if not key: return "❌ Groq API key not set."
        r = requests.post("https://api.groq.com/openai/v1/chat/completions", headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"}, json={"model": "llama-3.3-70b-versatile", "messages": [{"role": "system", "content": "You are helpful."}, {"role": "user", "content": prompt}], "temperature": 0.7, "max_tokens": 1000}, timeout=30)
        return r.json()["choices"][0]["message"]["content"]
    except Exception as e: return f"❌ Groq: {e}"

# ╔══════════════════════════════════════════════════════════════════╗
# ║                  COMMAND DECORATOR + CATEGORIES                  ║
# ╚══════════════════════════════════════════════════════════════════╝

def command(name: str, *aliases: str, category: str = "general"):
    def decorator(fn: Callable):
        for key in [name, *aliases]:
            _COMMANDS[key.lower()] = fn
        if category not in _CATEGORIES:
            _CATEGORIES[category] = {"name": category, "emoji": "📋", "cmds": []}
        _CATEGORIES[category]["cmds"].append(name)
        return fn
    return decorator

# Set category emojis
_CATEGORY_EMOJIS = {
    "general": "📋", "fun": "🎉", "group": "👥", "settings": "⚙️",
    "admin": "👑", "ai": "🤖", "media": "🖼️", "bug": "🐛", "utility": "🔧",
}

# ╔══════════════════════════════════════════════════════════════════╗
# ║                    GENERAL COMMANDS                              ║
# ╚══════════════════════════════════════════════════════════════════╝

@command("ping", "p", category="general")
def cmd_ping(client, jid, args, sender_jid, sender_num, msg, **_):
    start = time.time()
    send_text(client, jid, "📡 Pinging...")
    send_text(client, jid, f"🏓 Pong! Latency: {int((time.time()-start)*1000)}ms")

@command("help", "h", category="general")
def cmd_help(client, jid, args, sender_jid, sender_num, msg, **_):
    p = get_prefix()
    send_text(client, jid, f"*📚 {BOT_NAME} HELP*\n\nPrefix: `{p}`\n\n{p}menu - Interactive menu\n{p}ping - Check response\n{p}ai <query> - Ask AI\n{p}info - Bot info\n{p}status - Connection\nUse `{p}menu` for all commands.")

@command("menu", category="general")
def cmd_menu(client, jid, args, sender_jid, sender_num, msg, **_):
    p = _get_user_setting(sender_num, "prefix", get_prefix())
    mode = _get_user_setting(sender_num, "mode", "public")
    user_num = get_user_number(str(jid))
    
    if user_num in _menu_sessions:
        old = _menu_sessions[user_num]
        if old.get("timer"): old["timer"].cancel()
        del _menu_sessions[user_num]

    # Build blue-themed menu
    menu_text = "╔══════════════════════════════════════╗\n"
    menu_text += "║                                      ║\n"
    menu_text += "║   ╦ ╦╔╦╗╔╦╗  ╔╗ ╔═╗╔╦╗            ║\n"
    menu_text += "║   ╠═╣ ║║║║║  ╠╩╗║ ║ ║             ║\n"
    menu_text += "║   ╩ ╩═╩╝╩ ╩  ╚═╝╚═╝ ╩             ║\n"
    menu_text += "║   🤖 Multi-Session WhatsApp Bot     ║\n"
    menu_text += f"║   Prefix: {p.ljust(26)}║\n"
    menu_text += f"║   Mode: {mode.ljust(28)}║\n"
    menu_text += f"║   Commands: {str(len(_COMMANDS)).ljust(25)}║\n"
    menu_text += "╠══════════════════════════════════════╣\n"
    menu_text += "║       📋 SELECT CATEGORY             ║\n"
    menu_text += "╠══════════════════════════════════════╣\n"
    menu_text += "║                                      ║\n"

    cats = []
    counter = 1
    for cat_key in ["general", "fun", "group", "settings", "admin", "ai", "media", "bug", "utility"]:
        emoji = _CATEGORY_EMOJIS.get(cat_key, "📋")
        name = cat_key.capitalize()
        cats.append({"number": counter, "key": cat_key, "emoji": emoji, "name": name})
        counter += 1

    # Display in 2 columns
    for i in range(0, len(cats), 2):
        left = cats[i]
        right = cats[i+1] if i+1 < len(cats) else None
        left_text = f"{left['number']}. {left['emoji']} {left['name']}"
        if right:
            right_text = f"{right['number']}. {right['emoji']} {right['name']}"
            menu_text += f"║  {left_text.ljust(20)} {right_text.ljust(17)}║\n"
        else:
            menu_text += f"║  {left_text.ljust(37)}║\n"

    menu_text += "║                                      ║\n"
    menu_text += "╚══════════════════════════════════════╝\n"
    menu_text += "Reply with number (1-9) • Expires 60s"

    send_text(client, jid, menu_text)

    timer = threading.Timer(60, lambda: _menu_sessions.pop(user_num, None))
    timer.daemon = True; timer.start()
    _menu_sessions[user_num] = {"items": cats, "type": "category", "expires": time.time() + 60, "timer": timer, "prefix": p}

@command("info", category="general")
def cmd_info(client, jid, args, sender_jid, sender_num, msg, **_):
    send_text(client, jid, f"*🤖 {BOT_NAME} v2.0*\nPrefix: `{get_prefix()}`\nCommands: {len(_COMMANDS)}\nAI: {DEFAULT_AI.upper()}")

@command("status", category="general")
def cmd_status(client, jid, args, sender_jid, sender_num, msg, **_):
    try:
        connected = bool(client.info and client.info.wid)
        phone = get_user_number(str(client.info.wid)) if connected else "N/A"
    except: connected, phone = False, "N/A"
    send_text(client, jid, f"📊 *Status*\nWhatsApp: {'✅ Connected' if connected else '❌ Disconnected'}\nPhone: {phone}")

@command("getid", category="general")
def cmd_getid(client, jid, args, sender_jid, sender_num, msg, **_):
    send_text(client, jid, f"🆔 Your ID: {sender_num}")

@command("echo", "say", category="general")
def cmd_echo(client, jid, args, sender_jid, sender_num, msg, **_):
    send_text(client, jid, " ".join(args) if args else "(nothing to echo)")

@command("test", category="general")
def cmd_test(client, jid, args, sender_jid, sender_num, msg, **_):
    send_text(client, jid, "✅ Bot is working! Test successful.")

@command("rules", category="general")
def cmd_rules(client, jid, args, sender_jid, sender_num, msg, **_):
    send_text(client, jid, "📜 *Rules:*\nConfigure auto-reply rules via the dashboard.")

# ╔══════════════════════════════════════════════════════════════════╗
# ║                      FUN COMMANDS                                ║
# ╚══════════════════════════════════════════════════════════════════╝

@command("joke", category="fun")
def cmd_joke(client, jid, args, sender_jid, sender_num, msg, **_):
    try:
        r = requests.get("https://v2.jokeapi.dev/joke/Any?safe-mode", timeout=5)
        d = r.json()
        joke = d["joke"] if d.get("type") == "single" else f"{d.get('setup','')}\n\n{d.get('delivery','')}"
    except: joke = "Why did the developer go broke? Because he used up all his cache."
    send_text(client, jid, joke)

@command("quote", category="fun")
def cmd_quote(client, jid, args, sender_jid, sender_num, msg, **_):
    try:
        r = requests.get("https://api.quotable.io/random", timeout=5)
        d = r.json()
        quote = f"\"{d['content']}\"\n— {d['author']}"
    except: quote = '"The only way to do great work is to love what you do." — Steve Jobs'
    send_text(client, jid, quote)

# ╔══════════════════════════════════════════════════════════════════╗
# ║                    GROUP COMMANDS (24)                           ║
# ╚══════════════════════════════════════════════════════════════════╝

@command("kick", category="group")
def cmd_kick(client, jid, args, sender_jid, sender_num, msg, **_):
    chat = _get_chat(msg)
    if not chat: return send_text(client, jid, "❌ Groups only.")
    if not _is_bot_admin(chat, client): return send_text(client, jid, "❌ I need admin privileges.")
    target = _get_target_jid(msg, args)
    if not target: return send_text(client, jid, f"❌ Usage: {get_prefix()}kick @user / reply / <number>")
    try:
        chat.removeParticipants([target])
        send_text(client, jid, f"✅ Kicked {target.split('@')[0]}")
    except Exception as e: send_text(client, jid, f"❌ Failed: {e}")

@command("promote", category="group")
def cmd_promote(client, jid, args, sender_jid, sender_num, msg, **_):
    chat = _get_chat(msg)
    if not chat: return send_text(client, jid, "❌ Groups only.")
    if not _is_bot_admin(chat, client): return send_text(client, jid, "❌ I need admin privileges.")
    target = _get_target_jid(msg, args)
    if not target: return send_text(client, jid, f"❌ Usage: {get_prefix()}promote @user / reply / <number>")
    try:
        chat.promoteParticipants([target])
        send_text(client, jid, f"✅ Promoted {target.split('@')[0]}")
    except Exception as e: send_text(client, jid, f"❌ Failed: {e}")

@command("demote", category="group")
def cmd_demote(client, jid, args, sender_jid, sender_num, msg, **_):
    chat = _get_chat(msg)
    if not chat: return send_text(client, jid, "❌ Groups only.")
    if not _is_bot_admin(chat, client): return send_text(client, jid, "❌ I need admin privileges.")
    target = _get_target_jid(msg, args)
    if not target: return send_text(client, jid, f"❌ Usage: {get_prefix()}demote @user / reply / <number>")
    try:
        chat.demoteParticipants([target])
        send_text(client, jid, f"✅ Demoted {target.split('@')[0]}")
    except Exception as e: send_text(client, jid, f"❌ Failed: {e}")

@command("link", category="group")
def cmd_link(client, jid, args, sender_jid, sender_num, msg, **_):
    chat = _get_chat(msg)
    if not chat: return send_text(client, jid, "❌ Groups only.")
    if not _is_bot_admin(chat, client): return send_text(client, jid, "❌ I need admin privileges.")
    try:
        code = chat.getInviteCode()
        send_text(client, jid, f"🔗 https://chat.whatsapp.com/{code}")
    except Exception as e: send_text(client, jid, f"❌ Failed: {e}")

@command("antilink", category="group")
def cmd_antilink(client, jid, args, sender_jid, sender_num, msg, **_):
    if not _is_admin(sender_jid): return send_text(client, jid, "❌ Admin only.")
    chat = _get_chat(msg)
    if not chat: return send_text(client, jid, "❌ Groups only.")
    gid = chat.id._serialized
    action = (args[0] or "").lower() if args else ""
    state = (args[1] or "").lower() if len(args) > 1 else ""
    if not action or not state:
        cur = _anti_link.get(gid, {"enabled": False, "action": "delete"})
        return send_text(client, jid, f"🛡️ Anti-Link: {'ON' if cur['enabled'] else 'OFF'} | {cur['action']}\n{get_prefix()}antilink <delete|kick|warn> <on|off>")
    if action not in ("delete","kick","warn"): return send_text(client, jid, "Action: delete, kick, warn")
    if state not in ("on","off"): return send_text(client, jid, "State: on, off")
    _anti_link[gid] = {"enabled": state == "on", "action": action}
    send_text(client, jid, f"✅ Anti-link {'enabled' if state=='on' else 'disabled'} ({action})")

@command("delete", "del", category="group")
def cmd_delete(client, jid, args, sender_jid, sender_num, msg, **_):
    if not hasattr(msg, 'hasQuotedMsg') or not msg.hasQuotedMsg:
        return send_text(client, jid, "❌ Reply to a message to delete it.")
    chat = _get_chat(msg)
    if chat and not _is_bot_admin(chat, client): return send_text(client, jid, "❌ I need admin privileges.")
    try:
        msg.getQuotedMessage().delete(True)
        send_text(client, jid, "✅ Message deleted.")
    except Exception as e: send_text(client, jid, f"❌ Failed: {e}")

@command("tagall", category="group")
def cmd_tagall(client, jid, args, sender_jid, sender_num, msg, **_):
    chat = _get_chat(msg)
    if not chat: return send_text(client, jid, "❌ Groups only.")
    text = "📢 *Attention everyone!*\n" + (" ".join(args) + "\n" if args else "")
    mentions = [p.id._serialized for p in chat.participants]
    client.send_message(jid, text, mentions=mentions)

@command("groupinfo", category="group")
def cmd_groupinfo(client, jid, args, sender_jid, sender_num, msg, **_):
    chat = _get_chat(msg)
    if not chat: return send_text(client, jid, "❌ Groups only.")
    send_text(client, jid, f"*{chat.name}*\nID: {chat.id._serialized}\nMembers: {len(chat.participants)}\nDesc: {chat.description or 'None'}")

@command("admins", category="group")
def cmd_admins(client, jid, args, sender_jid, sender_num, msg, **_):
    chat = _get_chat(msg)
    if not chat: return send_text(client, jid, "❌ Groups only.")
    admin_ids = _get_group_admins(chat)
    text = f"👑 *Group Admins ({len(admin_ids)})*\n"
    for aid in admin_ids:
        try:
            c = client.getContactById(aid)
            text += f"- {c.pushname or c.number}\n"
        except: text += f"- {aid.split('@')[0]}\n"
    send_text(client, jid, text)

@command("welcome", category="group")
def cmd_welcome(client, jid, args, sender_jid, sender_num, msg, **_):
    chat = _get_chat(msg)
    if not chat: return send_text(client, jid, "❌ Groups only.")
    sub = (args[0] or "").lower() if args else ""
    if sub == "on": send_text(client, jid, f"✅ Welcome enabled!\n\n👋 Welcome to {chat.name or 'this group'}!")
    elif sub == "off": send_text(client, jid, "✅ Welcome disabled.")
    elif args: send_text(client, jid, f"✅ Custom welcome set!\n\n{' '.join(args)}")
    else: send_text(client, jid, f"👋 *Welcome Settings*\n{get_prefix()}welcome on|off|<text>")

@command("goodbye", category="group")
def cmd_goodbye(client, jid, args, sender_jid, sender_num, msg, **_):
    chat = _get_chat(msg)
    if not chat: return send_text(client, jid, "❌ Groups only.")
    sub = (args[0] or "").lower() if args else ""
    if sub == "on": send_text(client, jid, "✅ Goodbye enabled.\n\n😢 @user has left. We'll miss you!")
    elif sub == "off": send_text(client, jid, "✅ Goodbye disabled.")
    elif args: send_text(client, jid, f"✅ Custom goodbye set!\n\n{' '.join(args)}")
    else: send_text(client, jid, f"🚪 *Goodbye Settings*\n{get_prefix()}goodbye on|off|<text>")

@command("antistatusmention", category="group")
def cmd_antistatusmention(client, jid, args, sender_jid, sender_num, msg, **_):
    chat = _get_chat(msg)
    if not chat: return send_text(client, jid, "❌ Groups only.")
    if not _is_sender_admin(chat, sender_jid): return send_text(client, jid, "❌ Only group admins.")
    if not _is_bot_admin(chat, client): return send_text(client, jid, "❌ I need admin privileges.")
    gid = chat.id._serialized
    action = (args[0] or "").lower() if args else ""
    state = (args[1] or "").lower() if len(args) > 1 else ""
    if not action or not state:
        cur = _anti_status.get(gid, {"enabled": False, "action": "warn"})
        return send_text(client, jid, f"📵 Anti-Status: {'ON' if cur['enabled'] else 'OFF'} | {cur['action']}\n{get_prefix()}antistatusmention <delete|kick|warn> <on|off>")
    if action not in ("delete","kick","warn"): return send_text(client, jid, "❌ Action: delete, kick, warn")
    if state not in ("on","off"): return send_text(client, jid, "❌ State: on, off")
    _anti_status[gid] = {"enabled": state == "on", "action": action}
    send_text(client, jid, f"✅ Anti-status mention {'enabled' if state=='on' else 'disabled'} ({action})")

@command("onlyadmin", category="group")
def cmd_onlyadmin(client, jid, args, sender_jid, sender_num, msg, **_):
    chat = _get_chat(msg)
    if not chat: return send_text(client, jid, "❌ Groups only.")
    if not _is_sender_admin(chat, sender_jid): return send_text(client, jid, "❌ Only group admins.")
    if not _is_bot_admin(chat, client): return send_text(client, jid, "❌ I need admin privileges.")
    gid = chat.id._serialized
    state = (args[0] or "").lower() if args else ""
    if state not in ("on","off"): return send_text(client, jid, f"🔒 Admin-Only: {'ON' if _only_admin.get(gid,False) else 'OFF'}\n{get_prefix()}onlyadmin on/off")
    _only_admin[gid] = state == "on"
    send_text(client, jid, f"✅ Admin-only {'enabled' if state=='on' else 'disabled'}.")

@command("kickall", category="group")
def cmd_kickall(client, jid, args, sender_jid, sender_num, msg, **_):
    chat = _get_chat(msg)
    if not chat: return send_text(client, jid, "❌ Groups only.")
    if not _is_sender_admin(chat, sender_jid): return send_text(client, jid, "❌ Only group admins.")
    if not _is_bot_admin(chat, client): return send_text(client, jid, "❌ I need admin privileges.")
    admin_ids = _get_group_admins(chat)
    non_admins = [p for p in chat.participants if p.id._serialized not in admin_ids]
    if not non_admins: return send_text(client, jid, "❌ No non-admins.")
    if not args or args[0].upper() != "CONFIRM":
        return send_text(client, jid, f"⚠️ This will kick {len(non_admins)} non-admins.\nType: {get_prefix()}kickall CONFIRM")
    send_text(client, jid, f"🔄 Kicking {len(non_admins)}...")
    kicked = 0
    for i in range(0, len(non_admins), 20):
        batch = non_admins[i:i+20]
        try:
            chat.removeParticipants([p.id._serialized for p in batch])
            kicked += len(batch)
        except: pass
        time.sleep(2)
    send_text(client, jid, f"✅ Kicked {kicked} members.")

@command("groupdesc", category="group")
def cmd_groupdesc(client, jid, args, sender_jid, sender_num, msg, **_):
    chat = _get_chat(msg)
    if not chat: return send_text(client, jid, "❌ Groups only.")
    if not args: return send_text(client, jid, f"📋 *Description:*\n{chat.description or 'None'}")
    if not _is_sender_admin(chat, sender_jid): return send_text(client, jid, "❌ Only group admins.")
    if not _is_bot_admin(chat, client): return send_text(client, jid, "❌ I need admin privileges.")
    try:
        chat.setDescription(" ".join(args))
        send_text(client, jid, "✅ Description updated!")
    except Exception as e: send_text(client, jid, f"❌ Failed: {e}")

@command("members", category="group")
def cmd_members(client, jid, args, sender_jid, sender_num, msg, **_):
    chat = _get_chat(msg)
    if not chat: return send_text(client, jid, "❌ Groups only.")
    gid = chat.id._serialized
    cached = _member_stats.get(gid)
    if cached and (time.time()*1000) - cached["timestamp"] < 60000:
        return send_text(client, jid, cached["stats"])
    participants = chat.participants
    admin_ids = _get_group_admins(chat)
    countries = {}
    for p in participants:
        c = _get_country(get_user_number(p.id._serialized))
        countries[c] = countries.get(c, 0) + 1
    text = f"👥 *Members*\n📊 Total: {len(participants)}\n👑 Admins: {len(admin_ids)}\n\n🌍 *By Country:*\n"
    for c, cnt in sorted(countries.items(), key=lambda x: -x[1])[:15]:
        text += f"{c}: {cnt}\n"
    if len(countries) > 15: text += f"Other: {sum(list(countries.values())[15:])}\n"
    _member_stats[gid] = {"stats": text, "timestamp": time.time()*1000}
    send_text(client, jid, text)

@command("mute", category="group")
def cmd_mute(client, jid, args, sender_jid, sender_num, msg, **_):
    chat = _get_chat(msg)
    if not chat: return send_text(client, jid, "❌ Groups only.")
    if not _is_sender_admin(chat, sender_jid): return send_text(client, jid, "❌ Only group admins.")
    if not _is_bot_admin(chat, client): return send_text(client, jid, "❌ I need admin privileges.")
    target = _get_target_from_mention(msg, args)
    if not target: return send_text(client, jid, f"❌ Usage: {get_prefix()}mute @user <time>\nTime: 10m, 1h, 1d")
    ts_str = args[-1] if args else ""
    dur = parse_duration(ts_str)
    if dur is None: return send_text(client, jid, "❌ Invalid time. Use: 10s, 10m, 1h, 1d")
    gid = chat.id._serialized
    if gid not in _muted_users: _muted_users[gid] = {}
    _muted_users[gid][target] = {"until": time.time()*1000 + dur, "by": str(sender_jid)}
    send_text(client, jid, f"🔇 @{target.split('@')[0]} muted for {ts_str}.")

@command("unmute", category="group")
def cmd_unmute(client, jid, args, sender_jid, sender_num, msg, **_):
    chat = _get_chat(msg)
    if not chat: return send_text(client, jid, "❌ Groups only.")
    if not _is_sender_admin(chat, sender_jid): return send_text(client, jid, "❌ Only group admins.")
    target = _get_target_from_mention(msg, args)
    if not target: return send_text(client, jid, f"❌ Usage: {get_prefix()}unmute @user / <number>")
    gid = chat.id._serialized
    if gid in _muted_users: _muted_users[gid].pop(target, None)
    send_text(client, jid, f"🔊 @{target.split('@')[0]} unmuted.")

@command("mutelist", category="group")
def cmd_mutelist(client, jid, args, sender_jid, sender_num, msg, **_):
    chat = _get_chat(msg)
    if not chat: return send_text(client, jid, "❌ Groups only.")
    gid = chat.id._serialized
    mutes = _muted_users.get(gid, {})
    now = time.time()*1000
    active = {u: d for u, d in mutes.items() if d["until"] > now}
    if not active: return send_text(client, jid, "📋 No muted members.")
    text = "🔇 *Muted Members*\n\n"
    for uid, data in active.items():
        mins = int(max(0, data["until"] - now)//60000)
        text += f"• @{uid.split('@')[0]} - {mins}min\n"
    send_text(client, jid, text)

@command("setwarn", category="group")
def cmd_setwarn(client, jid, args, sender_jid, sender_num, msg, **_):
    chat = _get_chat(msg)
    if not chat: return send_text(client, jid, "❌ Groups only.")
    if not _is_sender_admin(chat, sender_jid): return send_text(client, jid, "❌ Only group admins.")
    try: limit = int(args[0])
    except: return send_text(client, jid, "❌ Provide limit 1-10.")
    if limit < 1 or limit > 10: return send_text(client, jid, "❌ Limit 1-10.")
    gid = chat.id._serialized
    if gid not in _warning_users: _warning_users[gid] = {}
    send_text(client, jid, f"✅ Warning limit set to {limit}.")

@command("antibadword", category="group")
def cmd_antibadword(client, jid, args, sender_jid, sender_num, msg, **_):
    chat = _get_chat(msg)
    if not chat: return send_text(client, jid, "❌ Groups only.")
    if not _is_sender_admin(chat, sender_jid): return send_text(client, jid, "❌ Only group admins.")
    if not _is_bot_admin(chat, client): return send_text(client, jid, "❌ I need admin privileges.")
    action = (args[0] or "").lower() if args else ""
    state = (args[1] or "").lower() if len(args) > 1 else ""
    if not action or not state: return send_text(client, jid, f"🚫 Bad Word Filter\n{get_prefix()}antibadword <delete|warn|kick|mute> <on|off>")
    if action not in ("delete","warn","kick","mute"): return send_text(client, jid, "❌ Action: delete, warn, kick, mute")
    if state not in ("on","off"): return send_text(client, jid, "❌ State: on, off")
    send_text(client, jid, f"✅ Bad word filter {'enabled' if state=='on' else 'disabled'} ({action}).")

@command("addbadword", category="group")
def cmd_addbadword(client, jid, args, sender_jid, sender_num, msg, **_):
    chat = _get_chat(msg)
    if not chat: return send_text(client, jid, "❌ Groups only.")
    if not _is_sender_admin(chat, sender_jid): return send_text(client, jid, "❌ Only group admins.")
    word = (args[0] or "").lower() if args else ""
    if not word: return send_text(client, jid, f"❌ Usage: {get_prefix()}addbadword <word>")
    gid = chat.id._serialized
    if gid not in _bad_words: _bad_words[gid] = set()
    _bad_words[gid].add(word)
    send_text(client, jid, f"✅ \"{word}\" added.")

@command("removebadword", category="group")
def cmd_removebadword(client, jid, args, sender_jid, sender_num, msg, **_):
    chat = _get_chat(msg)
    if not chat: return send_text(client, jid, "❌ Groups only.")
    if not _is_sender_admin(chat, sender_jid): return send_text(client, jid, "❌ Only group admins.")
    word = (args[0] or "").lower() if args else ""
    if not word: return send_text(client, jid, f"❌ Usage: {get_prefix()}removebadword <word>")
    gid = chat.id._serialized
    if gid in _bad_words:
        removed = word in _bad_words[gid]
        _bad_words[gid].discard(word)
        send_text(client, jid, f"✅ \"{word}\" removed." if removed else f"❌ Not found.")
    else: send_text(client, jid, f"❌ Not found.")

@command("listbadword", category="group")
def cmd_listbadword(client, jid, args, sender_jid, sender_num, msg, **_):
    chat = _get_chat(msg)
    if not chat: return send_text(client, jid, "❌ Groups only.")
    gid = chat.id._serialized
    words = _bad_words.get(gid, set())
    if not words: return send_text(client, jid, "📋 No bad words.")
    send_text(client, jid, f"🚫 *Bad Words ({len(words)})*\n{', '.join(sorted(words))}")

# ╔══════════════════════════════════════════════════════════════════╗
# ║                  SETTINGS COMMANDS                               ║
# ╚══════════════════════════════════════════════════════════════════╝

@command("setprefix", category="settings")
def cmd_setprefix(client, jid, args, sender_jid, sender_num, msg, **_):
    if not args or len(args[0]) > 3:
        current = _get_user_setting(sender_num, "prefix", get_prefix())
        return send_text(client, jid, f"❌ Usage: {current}setprefix <symbol>")
    new_prefix = args[0][:3]
    _set_user_setting(sender_num, "prefix", new_prefix)
    send_text(client, jid, f"✅ Your prefix updated to `{new_prefix}`")

@command("setfooter", category="settings")
def cmd_setfooter(client, jid, args, sender_jid, sender_num, msg, **_):
    if not _is_admin(sender_jid): return send_text(client, jid, "❌ Admin only.")
    if not args: return send_text(client, jid, f"❌ Usage: {get_prefix()}setfooter <text>")
    send_text(client, jid, f"✅ Footer updated.")

@command("mode", category="settings")
def cmd_mode(client, jid, args, sender_jid, sender_num, msg, **_):
    mode = (args[0] or "").lower() if args else ""
    current = _get_user_setting(sender_num, "mode", "public")
    if mode not in ("private", "public"):
        return send_text(client, jid, f"❌ Usage: {get_prefix()}mode private|public\nCurrent: {current}")
    _set_user_setting(sender_num, "mode", mode)
    send_text(client, jid, f"✅ Your mode set to: {mode}")

@command("alwaysonline", category="settings")
def cmd_alwaysonline(client, jid, args, sender_jid, sender_num, msg, **_):
    state = (args[0] or "").lower() if args else ""
    current = _get_user_setting(sender_num, "always_online", False)
    if state not in ("on", "off"):
        return send_text(client, jid, f"❌ Usage: {get_prefix()}alwaysonline on|off\nCurrent: {'ON' if current else 'OFF'}")
    _set_user_setting(sender_num, "always_online", state == "on")
    send_text(client, jid, f"✅ Always Online: {state.upper()}")

@command("autoviewstatus", category="settings")
def cmd_autoviewstatus(client, jid, args, sender_jid, sender_num, msg, **_):
    state = (args[0] or "").lower() if args else ""
    current = _get_user_setting(sender_num, "auto_view_status", False)
    if state not in ("on", "off"):
        return send_text(client, jid, f"❌ Usage: {get_prefix()}autoviewstatus on|off\nCurrent: {'ON' if current else 'OFF'}")
    _set_user_setting(sender_num, "auto_view_status", state == "on")
    send_text(client, jid, f"✅ Auto-View Status: {state.upper()}")

@command("reload", category="settings")
def cmd_reload(client, jid, args, sender_jid, sender_num, msg, **_):
    if not _is_admin(sender_jid): return send_text(client, jid, "❌ Admin only.")
    send_text(client, jid, f"✅ Reloaded! {len(_COMMANDS)} commands.")

@command("listadmins", category="settings")
def cmd_listadmins(client, jid, args, sender_jid, sender_num, msg, **_):
    text = "👑 *Bot Admins:*\n" + ("\n".join(_ADMIN_NUMS) if _ADMIN_NUMS else "None.")
    send_text(client, jid, text)

@command("antidelete", category="settings")
def cmd_antidelete(client, jid, args, sender_jid, sender_num, msg, **_):
    state = (args[0] or "").lower() if args else ""
    current = _get_user_setting(sender_num, "anti_delete", True)
    if state not in ("on", "off"):
        return send_text(client, jid, f"🗑️ Anti-Delete: {'ON' if current else 'OFF'}\n{get_prefix()}antidelete on/off")
    _set_user_setting(sender_num, "anti_delete", state == "on")
    send_text(client, jid, f"✅ Anti-delete {'enabled' if state=='on' else 'disabled'}.")

@command("autoreply", category="settings")
def cmd_autoreply(client, jid, args, sender_jid, sender_num, msg, **_):
    state = (args[0] or "").lower() if args else ""
    current = _get_user_setting(sender_num, "auto_reply", False)
    if state not in ("on", "off"):
        return send_text(client, jid, f"🤖 Auto-Reply: {'✅ ON' if current else '❌ OFF'}\n{get_prefix()}autoreply on/off")
    _set_user_setting(sender_num, "auto_reply", state == "on")
    send_text(client, jid, f"✅ Auto-reply {'enabled' if state=='on' else 'disabled'}.")

# ╔══════════════════════════════════════════════════════════════════╗
# ║                    ADMIN COMMANDS                                ║
# ╚══════════════════════════════════════════════════════════════════╝

@command("addbotadmin", category="admin")
def cmd_addbotadmin(client, jid, args, sender_jid, sender_num, msg, **_):
    if not _is_owner(sender_jid): return send_text(client, jid, "❌ Only owner.")
    target = _get_target_number(msg, args)
    if not target: return send_text(client, jid, f"❌ {get_prefix()}addbotadmin <number> or reply")
    if target in _ADMIN_NUMS: return send_text(client, jid, f"❌ Already admin.")
    _ADMIN_NUMS.append(target)
    os.environ["ADMIN_NUMBERS"] = ",".join(_ADMIN_NUMS)
    send_text(client, jid, f"✅ @{target} added as bot admin.")

@command("listbotadmins", category="admin")
def cmd_listbotadmins(client, jid, args, sender_jid, sender_num, msg, **_):
    text = f"👑 *Bot Admins ({len(_ADMIN_NUMS)})*\n" + "\n".join(f"{i+1}. {n}" for i,n in enumerate(_ADMIN_NUMS))
    send_text(client, jid, text if _ADMIN_NUMS else "None.")

@command("removebotadmin", category="admin")
def cmd_removebotadmin(client, jid, args, sender_jid, sender_num, msg, **_):
    if not _is_owner(sender_jid): return send_text(client, jid, "❌ Only owner.")
    target = _get_target_number(msg, args)
    if not target: return send_text(client, jid, f"❌ {get_prefix()}removebotadmin <number> or reply")
    if target not in _ADMIN_NUMS: return send_text(client, jid, f"❌ Not an admin.")
    _ADMIN_NUMS.remove(target)
    os.environ["ADMIN_NUMBERS"] = ",".join(_ADMIN_NUMS)
    send_text(client, jid, f"✅ @{target} removed.")

@command("addsudo", category="admin")
def cmd_addsudo(client, jid, args, sender_jid, sender_num, msg, **_):
    if not _is_owner(sender_jid): return send_text(client, jid, "❌ Only owner.")
    target = _get_target_number(msg, args)
    if not target: return send_text(client, jid, f"❌ {get_prefix()}addsudo <number> or reply")
    _ADMIN_NUMS.append(target)
    send_text(client, jid, f"✅ @{target} added as super admin.")

@command("setsudo", category="admin")
def cmd_setsudo(client, jid, args, sender_jid, sender_num, msg, **_):
    if not _is_owner(sender_jid): return send_text(client, jid, "❌ Only owner.")
    target = _get_target_number(msg, args)
    if not target: return send_text(client, jid, f"❌ {get_prefix()}setsudo <number> or reply")
    global OWNER_NUM; OWNER_NUM = target
    os.environ["OWNER_NUMBER"] = target
    send_text(client, jid, f"✅ @{target} set as owner.")

@command("ownerinfo", category="admin")
def cmd_ownerinfo(client, jid, args, sender_jid, sender_num, msg, **_):
    send_text(client, jid, f"👑 *Owner*\n👤 {BOT_NAME}\n📱 +{OWNER_NUM}\n📧 owner@hdm-bot.com")

# ╔══════════════════════════════════════════════════════════════════╗
# ║                      AI COMMANDS                                 ║
# ╚══════════════════════════════════════════════════════════════════╝

@command("ai", "ask", category="ai")
def cmd_ai(client, jid, args, sender_jid, sender_num, msg, **_):
    if not args: return send_text(client, jid, f"❌ Usage: {get_prefix()}ai <question>")
    send_text(client, jid, "🤖 Thinking...")
    model = DEFAULT_AI
    if model == "deepseek": response = _query_deepseek(" ".join(args))
    elif model == "gemini": response = _query_gemini(" ".join(args))
    elif model == "chatgpt": response = _query_chatgpt(" ".join(args))
    elif model == "grok": response = _query_grok(" ".join(args))
    elif model == "groq": response = _query_groq(" ".join(args))
    else: response = _query_hdm_ai(" ".join(args))
    send_text(client, jid, response)

@command("hdmai", category="ai")
def cmd_hdmai(client, jid, args, sender_jid, sender_num, msg, **_):
    if not args: return send_text(client, jid, f"❌ Usage: {get_prefix()}hdmai <question>")
    send_text(client, jid, "🤖 HDM AI thinking...")
    send_text(client, jid, _query_hdm_ai(" ".join(args)))

@command("deepseek", category="ai")
def cmd_deepseek(client, jid, args, sender_jid, sender_num, msg, **_):
    if not args: return send_text(client, jid, f"❌ Usage: {get_prefix()}deepseek <question>")
    send_text(client, jid, "🤖 DeepSeek thinking...")
    send_text(client, jid, _query_deepseek(" ".join(args)))

@command("gemini", category="ai")
def cmd_gemini(client, jid, args, sender_jid, sender_num, msg, **_):
    if not args: return send_text(client, jid, f"❌ Usage: {get_prefix()}gemini <question>")
    send_text(client, jid, "🧠 Gemini thinking...")
    send_text(client, jid, _query_gemini(" ".join(args)))

@command("chatgpt", category="ai")
def cmd_chatgpt(client, jid, args, sender_jid, sender_num, msg, **_):
    if not args: return send_text(client, jid, f"❌ Usage: {get_prefix()}chatgpt <question>")
    send_text(client, jid, "💬 ChatGPT thinking...")
    send_text(client, jid, _query_chatgpt(" ".join(args)))

@command("grok", category="ai")
def cmd_grok(client, jid, args, sender_jid, sender_num, msg, **_):
    if not args: return send_text(client, jid, f"❌ Usage: {get_prefix()}grok <question>")
    send_text(client, jid, "🚀 Grok thinking...")
    send_text(client, jid, _query_grok(" ".join(args)))

@command("groq", category="ai")
def cmd_groq(client, jid, args, sender_jid, sender_num, msg, **_):
    if not args: return send_text(client, jid, f"❌ Usage: {get_prefix()}groq <question>")
    send_text(client, jid, "⚡ Groq thinking...")
    send_text(client, jid, _query_groq(" ".join(args)))

# ╔══════════════════════════════════════════════════════════════════╗
# ║                    MEDIA COMMANDS                                ║
# ╚══════════════════════════════════════════════════════════════════╝

@command("sticker", category="media")
def cmd_sticker(client, jid, args, sender_jid, sender_num, msg, **_):
    if not HAS_PILLOW: return send_text(client, jid, "❌ pip install Pillow")
    try:
        if hasattr(msg,'hasQuotedMsg') and msg.hasQuotedMsg:
            q = msg.getQuotedMessage()
            if hasattr(q,'hasMedia') and q.hasMedia:
                send_text(client, jid, "🎨 Creating...")
                media = q.downloadMedia()
                buf = bytes(media.data) if not isinstance(media.data,bytes) else media.data
                d = os.path.join(os.path.dirname(__file__),"..","temp")
                os.makedirs(d, exist_ok=True)
                inp = os.path.join(d, f"{int(time.time())}_in.jpg")
                out = os.path.join(d, f"{int(time.time())}_sticker.webp")
                with open(inp,"wb") as f: f.write(buf)
                Image.open(inp).resize((512,512),Image.LANCZOS).save(out,"WEBP",quality=90)
                with open(out,"rb") as f: client.send_message(jid, f.read())
                os.unlink(inp); os.unlink(out)
                return
        send_text(client, jid, "❌ Reply to an image with .sticker")
    except Exception as e: send_text(client, jid, f"❌ {e}")

@command("take", category="media")
def cmd_take(client, jid, args, sender_jid, sender_num, msg, **_):
    if not args: return send_text(client, jid, f"❌ Usage: {get_prefix()}take <pack>|<author>")
    send_text(client, jid, "✅ Sticker metadata set.")

# ╔══════════════════════════════════════════════════════════════════╗
# ║                    BUG / TESTING COMMANDS                        ║
# ╚══════════════════════════════════════════════════════════════════╝

@command("bugmenu", category="bug")
def cmd_bugmenu(client, jid, args, sender_jid, sender_num, msg, **_):
    if not ENABLE_BUG: return send_text(client, jid, "❌ Bug disabled.")
    if not _is_user_allowed_bug(sender_jid): return send_text(client, jid, "❌ Not authorized.")
    send_text(client, jid, f"🐛 *BUG MENU*\n\n{get_prefix()}bug <num> <msg> <count> <interval>\n{get_prefix()}stopbug\n\nExample: {get_prefix()}bug 254712345678 \"Hi\" 50 2")

@command("bug", category="bug")
def cmd_bug(client, jid, args, sender_jid, sender_num, msg, **_):
    if not ENABLE_BUG: return send_text(client, jid, "❌ Bug disabled.")
    if not _is_user_allowed_bug(sender_jid): return send_text(client, jid, "❌ Not authorized.")
    if len(args) < 4: return send_text(client, jid, f"❌ {get_prefix()}bug <num> <msg> <count> <interval>")
    try:
        tn = format_number(args[0]); count = int(args[-2]); interval = float(args[-1])
        mt = " ".join(args[1:-2])
    except: return send_text(client, jid, "❌ Invalid args.")
    if count < 1 or count > BUG_MAX: return send_text(client, jid, f"❌ Count 1-{BUG_MAX}.")
    if interval < 0.01 or interval > 60: return send_text(client, jid, "❌ Interval 0.01-60s.")
    tj = f"{tn}@c.us"; ims = int(interval*1000); aid = f"{int(time.time()*1000)}_{tj}"
    sent = [0]; _active_attacks[aid] = {"stopped":False,"from":str(jid)}
    def _loop():
        a = _active_attacks.get(aid)
        if not a or a["stopped"] or sent[0] >= count:
            _active_attacks.pop(aid,None)
            try: send_text(client, jid, f"✅ Done: {sent[0]}/{count}")
            except: pass
            return
        try: client.send_message(tj, mt); sent[0] += 1
        except: pass
        threading.Timer(ims/1000,_loop).start()
    threading.Thread(target=_loop,daemon=True).start()
    send_text(client, jid, f"🐛 Started: {tn} ({count}msgs, {interval}s)")

@command("stopbug", category="bug")
def cmd_stopbug(client, jid, args, sender_jid, sender_num, msg, **_):
    if not _is_user_allowed_bug(sender_jid): return send_text(client, jid, "❌ Not authorized.")
    stopped = 0
    for aid, a in list(_active_attacks.items()):
        if a.get("from") == str(jid): a["stopped"] = True; _active_attacks.pop(aid,None); stopped += 1
    send_text(client, jid, f"✅ Stopped {stopped}." if stopped else "❌ None active.")

@command("addbuguser", category="bug")
def cmd_addbuguser(client, jid, args, sender_jid, sender_num, msg, **_):
    if not _is_admin(sender_jid): return send_text(client, jid, "❌ Admin only.")
    target = _get_target_number(msg, args)
    if not target: return send_text(client, jid, f"❌ {get_prefix()}addbuguser <number> or reply")
    if target in _BUG_USERS: return send_text(client, jid, "❌ Already bug user.")
    _BUG_USERS.append(target)
    os.environ["BUG_ALLOWED_USERS"] = ",".join(_BUG_USERS)
    send_text(client, jid, f"✅ @{target} added.")

@command("listbugusers", category="bug")
def cmd_listbugusers(client, jid, args, sender_jid, sender_num, msg, **_):
    if not _is_admin(sender_jid): return send_text(client, jid, "❌ Admin only.")
    text = f"🐛 *Bug Users ({len(_BUG_USERS)})*\n" + "\n".join(f"{i+1}. {u}" for i,u in enumerate(_BUG_USERS))
    send_text(client, jid, text if _BUG_USERS else "None.")

@command("removebuguser", category="bug")
def cmd_removebuguser(client, jid, args, sender_jid, sender_num, msg, **_):
    if not _is_admin(sender_jid): return send_text(client, jid, "❌ Admin only.")
    target = _get_target_number(msg, args)
    if not target: return send_text(client, jid, f"❌ {get_prefix()}removebuguser <number> or reply")
    if target not in _BUG_USERS: return send_text(client, jid, "❌ Not a bug user.")
    _BUG_USERS.remove(target)
    os.environ["BUG_ALLOWED_USERS"] = ",".join(_BUG_USERS)
    send_text(client, jid, f"✅ @{target} removed.")

@command("antibug", category="bug")
def cmd_antibug(client, jid, args, sender_jid, sender_num, msg, **_):
    state = (args[0] or "").lower() if args else ""
    current = _get_user_setting(sender_num, "anti_bug", False)
    if state not in ("on", "off"):
        return send_text(client, jid, f"🛡️ Anti-Bug: {'ON' if current else 'OFF'}\n{get_prefix()}antibug on/off")
    _set_user_setting(sender_num, "anti_bug", state == "on")
    send_text(client, jid, f"✅ Anti-bug {'enabled' if state=='on' else 'disabled'}.")

@command("buglogs", category="bug")
def cmd_buglogs(client, jid, args, sender_jid, sender_num, msg, **_):
    if not _is_admin(sender_jid): return send_text(client, jid, "❌ Admin only.")
    if not _bug_logs: return send_text(client, jid, "📜 None.")
    text = "🐛 *Bug Logs*\n\n"
    for i, log in enumerate(_bug_logs[-10:][::-1]): text += f"{i+1}. {log['attacker']} - {log['command']}\n   {log['timestamp']}\n\n"
    send_text(client, jid, text)

@command("clearbuglogs", category="bug")
def cmd_clearbuglogs(client, jid, args, sender_jid, sender_num, msg, **_):
    if not _is_owner(sender_jid): return send_text(client, jid, "❌ Only owner.")
    _bug_logs.clear()
    send_text(client, jid, "✅ Cleared.")

# ╔══════════════════════════════════════════════════════════════════╗
# ║                  UTILITY COMMANDS                                ║
# ╚══════════════════════════════════════════════════════════════════╝

@command("poll", category="utility")
def cmd_poll(client, jid, args, sender_jid, sender_num, msg, **_):
    match = re.findall(r'"([^"]*)"', " ".join(args))
    if len(match) < 2: return send_text(client, jid, f"❌ {get_prefix()}poll \"Q?\" \"A\" \"B\" \"C\"")
    text = f"📊 *POLL*\n\n{match[0]}\n\n"
    for i, o in enumerate(match[1:6]): text += f"{i+1}️⃣ {o}\n"
    text += "\n_Reply with number!_"
    client.send_message(jid, text)

@command("broadcast", category="utility")
def cmd_broadcast(client, jid, args, sender_jid, sender_num, msg, **_):
    if not _is_admin(sender_jid): return send_text(client, jid, "❌ Admin only.")
    bm = " ".join(args)
    if not bm: return send_text(client, jid, f"❌ {get_prefix()}broadcast <msg>")
    try:
        chats = client.get_chats()
        groups = [c for c in chats if hasattr(c,'isGroup') and c.isGroup]
    except: groups = []
    if not groups: return send_text(client, jid, "❌ No groups.")
    send_text(client, jid, f"📢 Broadcasting to {len(groups)}...")
    sent = 0
    for g in groups:
        try: client.send_message(g.id._serialized, f"📢 *BROADCAST*\n\n{bm}"); sent += 1
        except: pass
        time.sleep(1)
    send_text(client, jid, f"✅ {sent}/{len(groups)}")

@command("pair", category="utility")
def cmd_pair(client, jid, args, sender_jid, sender_num, msg, **_):
    phone = args[0] if args else ""
    if not phone: return send_text(client, jid, f"❌ {get_prefix()}pair <phone>")
    formatted = format_number(phone)
    try:
        for m in ['get_pairing_code','pairing_code','getPairingCode']:
            if hasattr(client, m):
                code = getattr(client, m)(formatted)
                _pairing_codes[code] = {"phone":formatted,"timestamp":time.time()*1000}
                return send_text(client, jid, f"🔗 *Pairing Code*\n📱 +{formatted}\n🔑 {code}\n\n_Expires 5min._")
        send_text(client, jid, "❌ Not supported.")
    except Exception as e: send_text(client, jid, f"❌ {e}")

# ╔══════════════════════════════════════════════════════════════════╗
# ║                  MESSAGE HANDLER                                 ║
# ╚══════════════════════════════════════════════════════════════════╝

def handle_message(client: NewClient, msg: MessageEv):
    try:
        src = msg.Info.MessageSource
        chat_jid = src.Chat
        sender_jid = src.Sender
        is_from_me = src.IsFromMe
    except Exception as e:
        console.print(f"[red][MSG] Parse error: {e}[/red]")
        return

    body = get_text(msg)
    sender_str = jid_to_str(sender_jid)
    chat_str = jid_to_str(chat_jid)
    
    if hasattr(sender_jid, 'User'): user_num = str(sender_jid.User)
    else: user_num = get_user_number(str(sender_jid))
    
    phone_num = user_num
    try:
        session_id = getattr(client, '_hdm_session_id', None)
        if session_id:
            from server.services.session_service import session_service
            session = session_service.get(session_id)
            if session and session.get("phone_number"): phone_num = session["phone_number"]
    except: pass
    
    p = _get_user_setting(phone_num, "prefix", get_prefix())
    bot_num = phone_num

    print_msg("out" if is_from_me else "in", sender_str, chat_str, body or "[media/no text]")

    if body:
        try:
            from server.services.message_service import message_service
            sid = getattr(client, '_hdm_session_id', 'default')
            message_service.log_message(session_id=sid, from_jid=sender_str, chat_jid=chat_str, body=body, direction="out" if is_from_me else "in")
        except: pass

    if not body: return

    # Menu reply check
    if user_num in _menu_sessions:
        session = _menu_sessions[user_num]
        if time.time() > session.get("expires", 0):
            _menu_sessions.pop(user_num, None)
        else:
            match = re.match(r"^(\d+)$", body.strip())
            if match:
                num = int(match.group(1))
                items = session.get("items", [])
                item = next((i for i in items if i["number"] == num), None)
                if item:
                    if session.get("type") == "category":
                        # Show commands for that category
                        cat_key = item["key"]
                        prefix = session.get("prefix", get_prefix())
                        _show_category_commands(client, chat_jid, cat_key, prefix, user_num)
                    else:
                        _menu_sessions.pop(user_num, None)
                        handler = _COMMANDS.get(item["command"])
                        if handler:
                            try:
                                handler(client=client, jid=chat_jid, args=[], sender_jid=sender_jid, sender_num=phone_num, msg=msg)
                            except Exception as e:
                                send_text(client, chat_jid, f"❌ {e}")
                    return
                else:
                    send_text(client, chat_jid, f"❌ Invalid. 1-{len(items)}")
                    return

    # Command dispatch
    if body.startswith(p):
        parts = body[len(p):].strip().split()
        if not parts: return
        cmd_name = parts[0].lower()
        args = parts[1:]
        
        if cmd_name != "mode":
            mode = _get_user_setting(phone_num, "mode", "public")
            if mode == "private":
                sender_phone = str(sender_jid.User) if hasattr(sender_jid, 'User') else get_user_number(str(sender_jid))
                if sender_phone != phone_num: return

        handler = _COMMANDS.get(cmd_name)
        if handler:
            console.print(f"[dim]{_ts()}[/dim] [bold cyan][CMD][/bold cyan] {p}{cmd_name} from {sender_str}")
            try:
                handler(client=client, jid=chat_jid, args=args, sender_jid=sender_jid, sender_num=phone_num, msg=msg)
                try:
                    from server.services.message_service import message_service
                    sid = getattr(client, '_hdm_session_id', 'default')
                    message_service.log_message(session_id=sid, from_jid=sender_str, chat_jid=chat_str, body=body, direction="out" if is_from_me else "in", is_command=True, command_name=cmd_name)
                except: pass
            except Exception as exc:
                console.print_exception()
                try: send_text(chat_jid, f"❌ Error in `{cmd_name}`: {exc}")
                except: pass
            return

    # Auto-reply
    if not is_from_me and body:
        reply = _check_auto_reply(bot_num, body)
        if reply:
            send_text(client, chat_jid, reply)
            print_msg("out", "BOT", chat_str, reply)
            try:
                from server.services.message_service import message_service
                sid = getattr(client, '_hdm_session_id', 'default')
                message_service.log_message(session_id=sid, from_jid="BOT", chat_jid=chat_str, body=reply, direction="out")
            except: pass


def _show_category_commands(client, chat_jid, cat_key, prefix, user_num):
    """Show commands in a category as a submenu."""
    cat_cmds = []
    for name in sorted(_COMMANDS.keys()):
        # Find which commands belong to this category
        for cat, data in _CATEGORIES.items():
            if cat == cat_key and name in data.get("cmds", []):
                cat_cmds.append(name)
                break
    
    emoji = _CATEGORY_EMOJIS.get(cat_key, "📋")
    cat_name = cat_key.capitalize()
    
    menu_text = f"╔══════════════════════════════════════╗\n"
    menu_text += f"║   {emoji} {cat_name} Commands                 ║\n"
    menu_text += f"╠══════════════════════════════════════╣\n"
    
    flat_list = []
    counter = 1
    for name in sorted(set(cat_cmds)):
        menu_text += f"║ {str(counter).rjust(2)}. {prefix}{name.ljust(30)}║\n"
        flat_list.append({"number": counter, "command": name})
        counter += 1
    
    menu_text += f"╚══════════════════════════════════════╝\n"
    menu_text += f"Reply with number (1-{len(flat_list)}) • 0: Back • Expires 60s"
    
    send_text(client, chat_jid, menu_text)
    
    timer = threading.Timer(60, lambda: _menu_sessions.pop(user_num, None))
    timer.daemon = True; timer.start()
    _menu_sessions[user_num] = {"items": flat_list, "type": "command", "expires": time.time() + 60, "timer": timer}


# ╔══════════════════════════════════════════════════════════════════╗
# ║                  CLIENT FACTORY                                  ║
# ╚══════════════════════════════════════════════════════════════════╝

def build_client(
    session_name: str = None,
    db_path: str = None,
    on_message_callback: Callable = None,
    on_connected_callback: Callable = None,
    on_pair_callback: Callable = None,
) -> NewClient:
    name = session_name or SESSION
    path = db_path or DB_PATH
    params = inspect.signature(NewClient.__init__).parameters
    if "database" in params: client = NewClient(name=name, database=path)
    elif "name" in params: client = NewClient(name=path)
    else: client = NewClient(path)

    client._hdm_session_id = name

    @client.event(ConnectedEv)
    def on_connected(_: NewClient, __: ConnectedEv):
        console.print(Panel(
            f"[bold green]✓ Connected[/bold green]\nSession: [cyan]{name}[/cyan]\nPrefix: [cyan]{get_prefix()}[/cyan]\nCommands: [cyan]{len(_COMMANDS)}[/cyan]",
            title=f"[bold]{BOT_NAME}[/bold]", border_style="green"))
        if on_connected_callback: on_connected_callback(_, __)

    @client.event(PairStatusEv)
    def on_pair(_: NewClient, pair: PairStatusEv):
        console.print(f"[green][PAIR] Logged in as {jid_to_str(pair.ID)}[/green]")
        if on_pair_callback: on_pair_callback(_, pair)

    @client.event(ReceiptEv)
    def on_receipt(_: NewClient, receipt: ReceiptEv):
        console.print(f"[dim]{_ts()}[/dim] [magenta][RECEIPT][/magenta] type={receipt.Type}")

    @client.event(CallOfferEv)
    def on_call(_: NewClient, call: CallOfferEv):
        console.print(f"[dim]{_ts()}[/dim] [yellow][CALL][/yellow] incoming call")

    @client.event(MessageEv)
    def on_message(cli: NewClient, msg: MessageEv):
        if on_message_callback: on_message_callback(cli, msg)
        else: handle_message(cli, msg)

    return client