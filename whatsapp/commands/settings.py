"""
server/whatsapp/commands/settings.py — Settings commands
setprefix, setfooter, mode, alwaysonline, autoviewstatus, reload, listadmins, antidelete
"""
from server.whatsapp.handlers.command_registry import _commands_cache, _last_commands_load
from server.whatsapp.handlers.command_handler import command, register_builtin
from server.config.settings import settings


def register():
    builtins = [
        {"name": "setprefix", "description": "🔧 Change command prefix", "category": "settings", "admin_only": True},
        {"name": "setfooter", "description": "📝 Change footer text", "category": "settings", "admin_only": True},
        {"name": "mode", "description": "🔒 Set public/private mode", "category": "settings", "admin_only": True},
        {"name": "alwaysonline", "description": "🟢 Toggle always online", "category": "settings", "admin_only": True},
        {"name": "autoviewstatus", "description": "👀 Toggle auto-view status", "category": "settings", "admin_only": True},
        {"name": "reload", "description": "🔄 Reload commands/rules", "category": "settings", "admin_only": True},
        {"name": "listadmins", "description": "📋 List bot admins", "category": "settings", "admin_only": True},
        {"name": "antidelete", "description": "🗑️ Anti-delete protection", "category": "privacy", "admin_only": True},
    ]
    for cmd in builtins:
        register_builtin(cmd)


@command("setprefix")
async def cmd_setprefix(client, jid, args, sender_jid, sender_num, session_id, handler, msg, **kwargs):
    if not await handler.is_admin(sender_jid):
        return await handler.send_reply(client, jid, "❌ Admin only.")

    current_prefix = await handler.get_prefix()
    new_prefix = args[0] if args else ""
    if not new_prefix or len(new_prefix) > 3:
        return await handler.send_reply(client, jid, f"❌ Usage: {current_prefix}setprefix <symbol>")

    await handler.set_session_setting("commandPrefix", new_prefix)
    global _commands_cache, _last_commands_load
    _commands_cache.clear()
    _last_commands_load = 0

    await handler.send_reply(client, jid, f"✅ Command prefix changed to \"{new_prefix}\"")
    return True


@command("setfooter")
async def cmd_setfooter(client, jid, args, sender_jid, sender_num, session_id, handler, msg, **kwargs):
    if not await handler.is_admin(sender_jid):
        return await handler.send_reply(client, jid, "❌ Admin only.")
    current_prefix = await handler.get_prefix()
    new_footer = " ".join(args) if args else ""
    if not new_footer:
        return await handler.send_reply(client, jid, f"❌ Usage: {current_prefix}setfooter <text>")
    await handler.set_session_setting("footerText", new_footer)
    await handler.send_reply(client, jid, f"✅ Footer updated to:\n\"{new_footer}\"")
    return True


@command("mode")
async def cmd_mode(client, jid, args, sender_jid, sender_num, session_id, handler, msg, **kwargs):
    if not await handler.is_admin(sender_jid):
        return await handler.send_reply(client, jid, "❌ Admin only.")
    current_prefix = await handler.get_prefix()
    mode = (args[0] or "").lower() if args else ""
    if mode not in ("private", "public"):
        return await handler.send_reply(client, jid, f"❌ Usage: {current_prefix}mode private|public")
    await handler.set_session_setting("mode", mode)
    await handler.send_reply(client, jid, f"✅ Bot mode set to: {mode}")
    return True


@command("alwaysonline")
async def cmd_alwaysonline(client, jid, args, sender_jid, sender_num, session_id, handler, msg, **kwargs):
    if not await handler.is_admin(sender_jid):
        return await handler.send_reply(client, jid, "❌ Admin only.")
    current_prefix = await handler.get_prefix()
    state = (args[0] or "").lower() if args else ""
    if state not in ("on", "off"):
        return await handler.send_reply(client, jid, f"❌ Usage: {current_prefix}alwaysonline on|off")
    await handler.set_session_setting("alwaysOnline", state == "on")
    await handler.send_reply(client, jid, f"✅ Always Online: {state.upper()}")
    return True


@command("autoviewstatus")
async def cmd_autoviewstatus(client, jid, args, sender_jid, sender_num, session_id, handler, msg, **kwargs):
    if not await handler.is_admin(sender_jid):
        return await handler.send_reply(client, jid, "❌ Admin only.")
    current_prefix = await handler.get_prefix()
    state = (args[0] or "").lower() if args else ""
    if state not in ("on", "off"):
        return await handler.send_reply(client, jid, f"❌ Usage: {current_prefix}autoviewstatus on|off")
    await handler.set_session_setting("autoViewStatus", state == "on")
    await handler.send_reply(client, jid, f"✅ Auto-View Status: {state.upper()}")
    return True


@command("reload")
async def cmd_reload(client, jid, args, sender_jid, sender_num, session_id, handler, msg, **kwargs):
    if not await handler.is_admin(sender_jid):
        return await handler.send_reply(client, jid, "❌ Admin only.")
    global _commands_cache, _last_commands_load
    _commands_cache.clear()
    _last_commands_load = 0
    handler._session_settings_cache.clear()
    handler._group_settings_cache.clear()
    await handler.load_commands()
    await handler.send_reply(client, jid, f"✅ Reloaded! {len(_commands_cache)} commands available.")
    return True


@command("listadmins")
async def cmd_listadmins(client, jid, args, sender_jid, sender_num, session_id, handler, msg, **kwargs):
    admins = settings.ADMIN_NUMBERS
    text = f"👑 *Bot Admins:*\n" + ("\n".join(admins) if admins else "No admins configured.")
    await handler.send_reply(client, jid, text)
    return True


@command("antidelete")
async def cmd_antidelete(client, jid, args, sender_jid, sender_num, session_id, handler, msg, **kwargs):
    if not await handler.is_admin(sender_jid):
        return await handler.send_reply(client, jid, "❌ Admin only.")
    prefix = await handler.get_prefix()
    state = (args[0] or "").lower() if args else ""
    if state not in ("on", "off"):
        current = await handler.get_session_setting("antiDelete", True)
        return await handler.send_reply(client, jid,
            f"🗑️ *Anti-Delete Protection*\nStatus: {'✅ ON' if current else '❌ OFF'}\n\nUsage: {prefix}antidelete on/off"
        )
    await handler.set_session_setting("antiDelete", state == "on")
    await handler.send_reply(client, jid, f"✅ Anti-delete protection {'enabled' if state == 'on' else 'disabled'}.")
    return True