"""
server/whatsapp/commands/general.py — General commands
menu, help, ping, info, status, getid, rules
"""
import time
from server.whatsapp.handlers.command_registry import _commands_cache
from server.whatsapp.handlers.command_handler import command, register_builtin
from server.config.settings import settings
from server.utils.helpers import create_progress_bar


def register():
    builtins = [
        {"name": "menu", "description": "📱 Interactive command menu", "category": "general"},
        {"name": "help", "description": "❓ Show help information", "category": "general"},
        {"name": "ping", "description": "🏓 Check bot latency", "category": "utility"},
        {"name": "info", "description": "ℹ️ Bot information & uptime", "category": "utility"},
        {"name": "status", "description": "📊 WhatsApp connection status", "category": "utility"},
        {"name": "getid", "description": "🆔 Get your WhatsApp ID", "category": "utility"},
        {"name": "rules", "description": "📜 List active auto-reply rules", "category": "utility"},
    ]
    for cmd in builtins:
        register_builtin(cmd)


@command("menu")
async def cmd_menu(client, jid, args, sender_jid, sender_num, session_id, handler, msg, **kwargs):
    """Interactive command menu (matching JS menu handler)."""
    await handler.load_commands()
    prefix = await handler.get_prefix()
    mode = await handler.get_session_setting("mode", "public")
    always_online = await handler.get_session_setting("alwaysOnline", False)
    handler.clear_menu_session(sender_jid)

    categories = {
        "general": {"emoji": "📋", "name": "General", "cmds": []},
        "utility": {"emoji": "🔧", "name": "Utility", "cmds": []},
        "group": {"emoji": "👥", "name": "Group Management", "cmds": []},
        "ai": {"emoji": "🤖", "name": "AI Assistant", "cmds": []},
        "fun": {"emoji": "🎉", "name": "Fun & Games", "cmds": []},
        "media": {"emoji": "🖼️", "name": "Media Tools", "cmds": []},
        "settings": {"emoji": "⚙️", "name": "Bot Settings", "cmds": []},
        "admin": {"emoji": "👑", "name": "Admin", "cmds": []},
        "bug": {"emoji": "🐛", "name": "Testing Tools", "cmds": []},
        "privacy": {"emoji": "🔒", "name": "Privacy", "cmds": []},
    }

    all_cmds = [c for c in _commands_cache.values() if not c.get("is_alias")]
    seen = set()
    unique_cmds = []
    for c in all_cmds:
        if c["name"] not in seen:
            seen.add(c["name"])
            unique_cmds.append(c)

    for cmd in unique_cmds:
        cat = cmd.get("category", "general")
        if cat in categories:
            categories[cat]["cmds"].append(cmd)

    menu_text = "╭━━━━━━━━━━━━━━━━━━━━━━╮\n┃   *🤖 HDM BOT MENU*   ┃\n╰━━━━━━━━━━━━━━━━━━━━━━╯\n\n"
    flat_list = []
    counter = 1

    for cat_data in categories.values():
        if not cat_data["cmds"]:
            continue
        menu_text += f"*{cat_data['emoji']} {cat_data['name']}*\n├{'─'*20}\n"
        sorted_cmds = sorted(cat_data["cmds"], key=lambda c: c["name"])
        for cmd in sorted_cmds:
            lock = " 🔒" if cmd.get("admin_only") else ""
            menu_text += f"│ {str(counter).rjust(2)}. {prefix}{cmd['name']}{lock}\n│    {cmd.get('description', 'No description')}\n"
            flat_list.append({"number": counter, "command": cmd})
            counter += 1
        menu_text += f"╰{'─'*20}\n\n"

    menu_text += (
        f"╭{'─'*22}╮\n"
        f"│ Prefix: {prefix.ljust(13)} │\n"
        f"│ Mode: {mode.ljust(15)} │\n"
        f"│ Online: {'ON' if always_online else 'OFF'.ljust(14)} │\n"
        f"╰{'─'*22}╯\n\n"
        f"_Reply with number (1-{len(flat_list)}) • Expires 60s_"
    )

    client.send_message(jid, menu_text)
    handler.start_menu_session(sender_jid, flat_list, "", 60000)
    return True


@command("help", "h")
async def cmd_help(client, jid, args, sender_jid, sender_num, session_id, handler, msg, **kwargs):
    prefix = await handler.get_prefix()
    await handler.send_reply(client, jid,
        f"*📚 HELP*\n\n"
        f"Prefix: {prefix}\n"
        f"Self-commands: {prefix}{prefix}command\n\n"
        f"{prefix}menu - Interactive menu\n"
        f"{prefix}ping - Check response time\n"
        f"{prefix}ai <query> - Ask AI\n"
        f"{prefix}welcome on/off - Welcome messages\n"
        f"{prefix}goodbye on/off - Goodbye messages\n\n"
        f"Use {prefix}menu for all commands."
    )
    return True


@command("ping", "p")
async def cmd_ping(client, jid, args, sender_jid, sender_num, session_id, handler, msg, **kwargs):
    start = time.time()
    await handler.send_reply(client, jid, "📡 Pinging...")
    latency = int((time.time() - start) * 1000)
    await handler.send_reply(client, jid, f"🏓 Pong! Latency: {latency}ms")
    return True


@command("info")
async def cmd_info(client, jid, args, sender_jid, sender_num, session_id, handler, msg, **kwargs):
    if not hasattr(cmd_info, "_start_time"):
        cmd_info._start_time = time.time()
    uptime_seconds = time.time() - cmd_info._start_time

    hours = int(uptime_seconds // 3600)
    minutes = int((uptime_seconds % 3600) // 60)
    seconds = int(uptime_seconds % 60)
    prefix = await handler.get_prefix()

    await handler.send_reply(client, jid,
        f"*🤖 {settings.BOT_NAME} v2.0*\n"
        f"Prefix: {prefix}\n"
        f"Uptime: {hours}h {minutes}m {seconds}s\n"
        f"Session: {session_id}"
    )
    return True


@command("status")
async def cmd_status(client, jid, args, sender_jid, sender_num, session_id, handler, msg, **kwargs):
    connected = False
    phone = "N/A"
    try:
        if hasattr(client, 'info') and client.info and hasattr(client.info, 'wid'):
            connected = True
            phone = client.info.wid.User if hasattr(client.info.wid, 'User') else str(client.info.wid)
    except Exception:
        pass

    await handler.send_reply(client, jid,
        f"📊 *Status*\n"
        f"WhatsApp: {'✅ Connected' if connected else '❌ Disconnected'}\n"
        f"Phone: {phone}"
    )
    return True


@command("getid")
async def cmd_getid(client, jid, args, sender_jid, sender_num, session_id, handler, msg, **kwargs):
    await handler.send_reply(client, jid, f"🆔 Your ID: {sender_num}")
    return True


@command("rules")
async def cmd_rules(client, jid, args, sender_jid, sender_num, session_id, handler, msg, **kwargs):
    try:
        from server.models.auto_reply import AutoReply
        rules = await AutoReply.find_all_enabled(session_id)
        if rules:
            text = f"📜 *Active Rules:*\n" + "\n".join(f"{i+1}. {r.name}" for i, r in enumerate(rules[:10]))
        else:
            text = "No active rules."
        await handler.send_reply(client, jid, text)
    except Exception:
        await handler.send_reply(client, jid, "Error loading rules.")
    return True