"""
server/whatsapp/commands/admin.py — Admin management commands
addbotadmin, listbotadmins, removebotadmin, addsudo, setsudo, ownerinfo
"""
from whatsapp.handlers.command_handler import command, register_builtin
from config.settings import settings


def register():
    builtins = [
        {"name": "addbotadmin", "description": "➕ Add bot admin", "category": "admin", "admin_only": True},
        {"name": "listbotadmins", "description": "📋 List bot admins", "category": "admin", "admin_only": True},
        {"name": "removebotadmin", "description": "➖ Remove bot admin", "category": "admin", "admin_only": True},
        {"name": "addsudo", "description": "👑 Add super admin", "category": "admin", "admin_only": True},
        {"name": "setsudo", "description": "👤 Set primary owner", "category": "admin", "admin_only": True},
        {"name": "ownerinfo", "description": "ℹ️ Owner information", "category": "admin"},
    ]
    for cmd in builtins:
        register_builtin(cmd)


def _get_target_number(handler, msg, args) -> str | None:
    try:
        if hasattr(msg, 'hasQuotedMsg') and msg.hasQuotedMsg:
            quoted = msg.getQuotedMessage()
            target = getattr(quoted, 'author', None) or getattr(quoted, 'from', None)
            return handler.get_user_number(str(target))
    except Exception:
        pass
    if args and args[0]:
        return handler.format_number(args[0])
    return None


@command("addbotadmin")
async def cmd_addbotadmin(client, jid, args, sender_jid, sender_num, session_id, handler, msg, **kwargs):
    if not await handler.is_super_admin(sender_jid) and not handler.is_owner(sender_jid):
        return await handler.send_reply(client, jid, "❌ Only super admins or owner can use this command.")
    target = _get_target_number(handler, msg, args)
    if not target:
        prefix = await handler.get_prefix()
        return await handler.send_reply(client, jid, f"❌ Usage: {prefix}addbotadmin <number> or reply to user")
    bot_admins = await handler.get_session_setting("botAdmins", [])
    if target in bot_admins:
        return await handler.send_reply(client, jid, f"❌ @{target} is already a bot admin.")
    bot_admins.append(target)
    await handler.set_session_setting("botAdmins", bot_admins)
    await handler.send_reply(client, jid, f"✅ @{target} added as bot admin.")
    return True


@command("listbotadmins")
async def cmd_listbotadmins(client, jid, args, sender_jid, sender_num, session_id, handler, msg, **kwargs):
    if not await handler.is_admin(sender_jid):
        return await handler.send_reply(client, jid, "❌ Admin only.")
    bot_admins = await handler.get_session_setting("botAdmins", [])
    if not bot_admins:
        return await handler.send_reply(client, jid, "📋 No bot admins configured for this session.")
    text = f"👑 *Bot Admins ({len(bot_admins)})*\n" + "\n".join(f"{i+1}. {n}" for i, n in enumerate(bot_admins))
    await handler.send_reply(client, jid, text)
    return True


@command("removebotadmin")
async def cmd_removebotadmin(client, jid, args, sender_jid, sender_num, session_id, handler, msg, **kwargs):
    if not await handler.is_super_admin(sender_jid) and not handler.is_owner(sender_jid):
        return await handler.send_reply(client, jid, "❌ Only super admins or owner can use this command.")
    target = _get_target_number(handler, msg, args)
    if not target:
        prefix = await handler.get_prefix()
        return await handler.send_reply(client, jid, f"❌ Usage: {prefix}removebotadmin <number> or reply to user")
    bot_admins = await handler.get_session_setting("botAdmins", [])
    if target not in bot_admins:
        return await handler.send_reply(client, jid, f"❌ @{target} is not a bot admin.")
    bot_admins.remove(target)
    await handler.set_session_setting("botAdmins", bot_admins)
    await handler.send_reply(client, jid, f"✅ @{target} removed from bot admins.")
    return True


@command("addsudo")
async def cmd_addsudo(client, jid, args, sender_jid, sender_num, session_id, handler, msg, **kwargs):
    if not handler.is_owner(sender_jid):
        return await handler.send_reply(client, jid, "❌ Only the owner can use this command.")
    target = _get_target_number(handler, msg, args)
    if not target:
        prefix = await handler.get_prefix()
        return await handler.send_reply(client, jid, f"❌ Usage: {prefix}addsudo <number> or reply to user")
    super_admins = await handler.get_session_setting("superAdmins", [])
    if target in super_admins:
        return await handler.send_reply(client, jid, f"❌ @{target} is already a super admin.")
    super_admins.append(target)
    await handler.set_session_setting("superAdmins", super_admins)
    await handler.send_reply(client, jid, f"✅ @{target} added as super admin.")
    return True


@command("setsudo")
async def cmd_setsudo(client, jid, args, sender_jid, sender_num, session_id, handler, msg, **kwargs):
    if not handler.is_owner(sender_jid):
        return await handler.send_reply(client, jid, "❌ Only the owner can use this command.")
    target = _get_target_number(handler, msg, args)
    if not target:
        prefix = await handler.get_prefix()
        return await handler.send_reply(client, jid, f"❌ Usage: {prefix}setsudo <number> or reply to user")
    await handler.set_session_setting("primaryOwner", target)
    await handler.send_reply(client, jid, f"✅ @{target} set as primary owner for this session.")
    return True


@command("ownerinfo")
async def cmd_ownerinfo(client, jid, args, sender_jid, sender_num, session_id, handler, msg, **kwargs):
    primary_owner = await handler.get_session_setting("primaryOwner", settings.OWNER_NUMBER)
    text = (
        f"👑 *BOT OWNER INFO*\n"
        f"👤 Name: {settings.BOT_NAME} Owner\n"
        f"📱 Contact: +{primary_owner}\n"
        f"📧 Email: owner@hdm-bot.com\n"
        f"🌐 Website: https://hdm-bot.com"
    )
    await handler.send_reply(client, jid, text)
    return True