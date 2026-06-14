"""
server/whatsapp/commands/group.py — Group management commands
kick, promote, demote, link, antilink, delete, del, tagall, groupinfo, admins,
welcome, goodbye, antistatusmention, onlyadmin, kickall, groupdesc, members,
mute, unmute, mutelist, setwarn, antibadword, addbadword, removebadword, listbadword
"""
import time
import re
from server.whatsapp.handlers.command_handler import command, register_builtin
from server.config.settings import settings
from server.utils.helpers import get_country_from_number, get_user_number


def register():
    builtins = [
        # Core group
        {"name": "kick", "description": "👢 Kick member from group", "category": "group"},
        {"name": "promote", "description": "⬆️ Promote to admin", "category": "group"},
        {"name": "demote", "description": "⬇️ Demote from admin", "category": "group"},
        {"name": "link", "description": "🔗 Get group invite link", "category": "group"},
        {"name": "antilink", "description": "🛡️ Anti-link protection", "category": "group", "admin_only": True},
        {"name": "delete", "description": "🗑️ Delete quoted message", "category": "group"},
        {"name": "del", "description": "🗑️ Alias for delete", "category": "group", "is_alias": True, "parent": "delete"},
        {"name": "tagall", "description": "📢 Mention all members", "category": "group"},
        {"name": "groupinfo", "description": "👥 Group information", "category": "group"},
        {"name": "admins", "description": "👑 List group admins", "category": "group"},
        # Welcome/Goodbye
        {"name": "welcome", "description": "👋 Set welcome message", "category": "group"},
        {"name": "goodbye", "description": "🚪 Set goodbye message", "category": "group"},
        # Protection
        {"name": "antistatusmention", "description": "📵 Anti-status mention", "category": "group", "admin_only": True},
        # Moderation
        {"name": "onlyadmin", "description": "🔒 Admin-only messaging", "category": "group"},
        {"name": "kickall", "description": "👢 Kick all non-admins", "category": "group"},
        {"name": "groupdesc", "description": "📝 View/set group description", "category": "group"},
        {"name": "members", "description": "👥 Member statistics + countries", "category": "group"},
        # Mute system
        {"name": "mute", "description": "🔇 Mute a member", "category": "group"},
        {"name": "unmute", "description": "🔊 Unmute a member", "category": "group"},
        {"name": "mutelist", "description": "📋 List muted members", "category": "group"},
        {"name": "setwarn", "description": "⚠️ Set warning limit", "category": "group"},
        # Bad word filter
        {"name": "antibadword", "description": "🚫 Toggle bad word filter", "category": "group"},
        {"name": "addbadword", "description": "➕ Add bad word", "category": "group"},
        {"name": "removebadword", "description": "➖ Remove bad word", "category": "group"},
        {"name": "listbadword", "description": "📋 List bad words", "category": "group"},
    ]
    for cmd in builtins:
        if not cmd.get("is_alias"):
            register_builtin(cmd)


# ============================================================
# HELPERS
# ============================================================

async def _get_chat(msg):
    """Get chat object from message, return None if not in group."""
    try:
        chat = await msg.getChat()
        return chat if chat.isGroup else None
    except Exception:
        return None


async def _require_group(handler, client, jid, msg):
    """Ensure command is used in a group. Returns chat or sends error."""
    chat = await _get_chat(msg)
    if not chat:
        await handler.send_reply(client, jid, "❌ This command only works in groups.")
        return None
    return chat


async def _require_bot_admin(handler, client, jid, chat, action: str = "do this"):
    """Ensure bot is a group admin."""
    try:
        bot_id = client.info.wid._serialized if hasattr(client.info, 'wid') else None
    except Exception:
        bot_id = None
    if not bot_id:
        await handler.send_reply(client, jid, "❌ Bot not connected properly.")
        return False

    participant = next((p for p in chat.participants if p.id._serialized == bot_id), None)
    is_admin = participant and (getattr(participant, 'isAdmin', False) or getattr(participant, 'isSuperAdmin', False))

    if not is_admin:
        await handler.send_reply(client, jid, f"❌ I need admin privileges to {action}.")
        return False
    return True


async def _require_sender_admin(handler, client, jid, chat, sender_jid):
    """Ensure sender is a group admin."""
    participant = next((p for p in chat.participants if p.id._serialized == sender_jid), None)
    is_admin = participant and (getattr(participant, 'isAdmin', False) or getattr(participant, 'isSuperAdmin', False))
    if not is_admin:
        await handler.send_reply(client, jid, "❌ Only group admins can use this command.")
        return False
    return True


async def _get_group_admins(chat) -> list:
    """Get list of admin JIDs in a group (matching JS getGroupAdmins)."""
    return [
        p.id._serialized for p in chat.participants
        if getattr(p, 'isAdmin', False) or getattr(p, 'isSuperAdmin', False)
    ]


def _get_target_jid(handler, msg, args) -> str | None:
    """Extract target JID from quoted message or args (matching JS pattern)."""
    try:
        if hasattr(msg, 'hasQuotedMsg') and msg.hasQuotedMsg:
            quoted = msg.getQuotedMessage()
            target = getattr(quoted, 'author', None) or getattr(quoted, 'from', None)
            return str(target)
    except Exception:
        pass
    if args and args[0]:
        num = handler.format_number(args[0])
        return f"{num}@c.us"
    return None

def _get_target_from_mention_or_arg(handler, msg, args) -> str | None:
    """Get target from @mention in args or quoted message."""
    target = _get_target_jid(handler, msg, [])
    if target:
        return target
    if args and args[0].startswith("@"):
        num = handler.format_number(args[0].replace("@", ""))
        return f"{num}@c.us"
    if args and args[0]:
        num = handler.format_number(args[0])
        return f"{num}@c.us"
    return None


def _parse_duration(time_str: str) -> int | None:
    """Parse duration string like 10s, 5m, 1h, 2d into milliseconds."""
    match = re.match(r"^(\d+)([smhd])$", time_str.lower())
    if not match:
        return None
    value = int(match.group(1))
    unit = match.group(2)
    multipliers = {"s": 1000, "m": 60000, "h": 3600000, "d": 86400000}
    return value * multipliers[unit]


# ============================================================
# CORE GROUP COMMANDS
# ============================================================

@command("kick")
async def cmd_kick(client, jid, args, sender_jid, sender_num, session_id, handler, msg, **kwargs):
    chat = await _require_group(handler, client, jid, msg)
    if not chat:
        return True
    if not await _require_bot_admin(handler, client, jid, chat, "kick members"):
        return True

    target = _get_target_jid(handler, msg, args)
    if not target:
        prefix = await handler.get_prefix()
        await handler.send_reply(client, jid,
            f"❌ Usage: {prefix}kick @user / reply / {prefix}kick <number>"
        )
        return True

    try:
        await chat.removeParticipants([target])
        await handler.send_reply(client, jid, f"✅ Kicked {target.split('@')[0]}")
    except Exception as e:
        await handler.send_reply(client, jid, f"❌ Failed: {e}")
    return True


@command("promote")
async def cmd_promote(client, jid, args, sender_jid, sender_num, session_id, handler, msg, **kwargs):
    chat = await _require_group(handler, client, jid, msg)
    if not chat:
        return True
    if not await _require_bot_admin(handler, client, jid, chat, "promote members"):
        return True

    target = _get_target_jid(handler, msg, args)
    if not target:
        prefix = await handler.get_prefix()
        await handler.send_reply(client, jid,
            f"❌ Usage: {prefix}promote @user / reply / <number>"
        )
        return True

    try:
        await chat.promoteParticipants([target])
        await handler.send_reply(client, jid, f"✅ Promoted {target.split('@')[0]}")
    except Exception as e:
        await handler.send_reply(client, jid, f"❌ Failed: {e}")
    return True


@command("demote")
async def cmd_demote(client, jid, args, sender_jid, sender_num, session_id, handler, msg, **kwargs):
    chat = await _require_group(handler, client, jid, msg)
    if not chat:
        return True
    if not await _require_bot_admin(handler, client, jid, chat, "demote members"):
        return True

    target = _get_target_jid(handler, msg, args)
    if not target:
        prefix = await handler.get_prefix()
        await handler.send_reply(client, jid,
            f"❌ Usage: {prefix}demote @user / reply / <number>"
        )
        return True

    try:
        await chat.demoteParticipants([target])
        await handler.send_reply(client, jid, f"✅ Demoted {target.split('@')[0]}")
    except Exception as e:
        await handler.send_reply(client, jid, f"❌ Failed: {e}")
    return True


@command("link")
async def cmd_link(client, jid, args, sender_jid, sender_num, session_id, handler, msg, **kwargs):
    chat = await _require_group(handler, client, jid, msg)
    if not chat:
        return True
    if not await _require_bot_admin(handler, client, jid, chat, "get invite link"):
        return True

    try:
        code = await chat.getInviteCode()
        await handler.send_reply(client, jid, f"🔗 https://chat.whatsapp.com/{code}")
    except Exception as e:
        await handler.send_reply(client, jid, f"❌ Failed: {e}")
    return True


@command("antilink")
async def cmd_antilink(client, jid, args, sender_jid, sender_num, session_id, handler, msg, **kwargs):
    if not await handler.is_admin(sender_jid):
        return await handler.send_reply(client, jid, "❌ Admin only.")

    chat = await _require_group(handler, client, jid, msg)
    if not chat:
        return True

    group_id = chat.id._serialized
    prefix = await handler.get_prefix()
    action = (args[0] or "").lower() if args else ""
    state = (args[1] or "").lower() if len(args) > 1 else ""

    if not action or not state:
        current = handler._anti_link_settings.get(group_id, {"enabled": False, "action": "delete"})
        return await handler.send_reply(client, jid,
            f"🛡️ Anti-Link: {'ON' if current['enabled'] else 'OFF'} | Action: {current['action']}\n"
            f"Usage: {prefix}antilink <delete|kick|warn> <on|off>"
        )

    if action not in ("delete", "kick", "warn"):
        return await handler.send_reply(client, jid, "Action must be: delete, kick, warn")
    if state not in ("on", "off"):
        return await handler.send_reply(client, jid, "State must be: on, off")

    handler._anti_link_settings[group_id] = {"enabled": state == "on", "action": action}
    await handler.set_group_setting(group_id, "antiLink", {"enabled": state == "on", "action": action})
    await handler.send_reply(client, jid, f"✅ Anti-link {'enabled' if state == 'on' else 'disabled'} ({action})")
    return True


@command("delete", "del")
async def cmd_delete(client, jid, args, sender_jid, sender_num, session_id, handler, msg, **kwargs):
    if not hasattr(msg, 'hasQuotedMsg') or not msg.hasQuotedMsg:
        return await handler.send_reply(client, jid, "❌ Reply to a message to delete it.")

    quoted = msg.getQuotedMessage()
    chat = await _get_chat(msg)

    if chat and not await _require_bot_admin(handler, client, jid, chat, "delete messages"):
        return True

    try:
        await quoted.delete(True)
        await handler.send_reply(client, jid, "✅ Message deleted.")
    except Exception as e:
        await handler.send_reply(client, jid, f"❌ Failed: {e}")
    return True


@command("tagall")
async def cmd_tagall(client, jid, args, sender_jid, sender_num, session_id, handler, msg, **kwargs):
    chat = await _require_group(handler, client, jid, msg)
    if not chat:
        return True

    text = "📢 *Attention everyone!*\n"
    if args:
        text += " ".join(args) + "\n"

    mentions = [p.id._serialized for p in chat.participants]
    client.send_message(jid, text, mentions=mentions)
    return True


@command("groupinfo")
async def cmd_groupinfo(client, jid, args, sender_jid, sender_num, session_id, handler, msg, **kwargs):
    chat = await _require_group(handler, client, jid, msg)
    if not chat:
        return True

    await handler.send_reply(client, jid,
        f"*{chat.name}*\n"
        f"ID: {chat.id._serialized}\n"
        f"Members: {len(chat.participants)}\n"
        f"Description: {chat.description or 'None'}"
    )
    return True


@command("admins")
async def cmd_admins(client, jid, args, sender_jid, sender_num, session_id, handler, msg, **kwargs):
    chat = await _require_group(handler, client, jid, msg)
    if not chat:
        return True

    admin_ids = await _get_group_admins(chat)
    text = f"👑 *Group Admins ({len(admin_ids)})*\n"

    for aid in admin_ids:
        try:
            contact = client.getContactById(aid)
            text += f"- {contact.pushname or contact.number}\n"
        except Exception:
            text += f"- {aid.split('@')[0]}\n"

    await handler.send_reply(client, jid, text)
    return True


# ============================================================
# WELCOME / GOODBYE
# ============================================================

@command("welcome")
async def cmd_welcome(client, jid, args, sender_jid, sender_num, session_id, handler, msg, **kwargs):
    chat = await _require_group(handler, client, jid, msg)
    if not chat:
        return True

    group_id = chat.id._serialized
    prefix = await handler.get_prefix()
    sub_cmd = (args[0] or "").lower() if args else ""

    group_desc = chat.description or "Enjoy your stay!"
    group_name = chat.name or "this group"

    if sub_cmd == "on":
        await handler.set_group_setting(group_id, "welcomeEnabled", True)
        default_msg = (
            f"👋 *Welcome to {group_name}!*\n\n"
            f"📋 *Group Description:*\n{group_desc}\n\n"
            f"✅ Please read the group rules and enjoy your stay!"
        )
        await handler.set_group_setting(group_id, "welcomeMessage", default_msg)
        return await handler.send_reply(client, jid,
            f"✅ *Welcome messages enabled!*\n\nThe following message will be sent to new members:\n\n{default_msg}"
        )

    elif sub_cmd == "off":
        await handler.set_group_setting(group_id, "welcomeEnabled", False)
        return await handler.send_reply(client, jid, "✅ Welcome messages disabled.")

    elif args:
        custom_msg = " ".join(args)
        await handler.set_group_setting(group_id, "welcomeMessage", custom_msg)
        await handler.set_group_setting(group_id, "welcomeEnabled", True)
        return await handler.send_reply(client, jid,
            f"✅ *Custom welcome message set!*\n\n{custom_msg}\n\n💡 Tip: Use @user to mention the new member."
        )

    else:
        enabled = await handler.get_group_setting(group_id, "welcomeEnabled", False)
        message = await handler.get_group_setting(group_id, "welcomeMessage", "Not set")
        return await handler.send_reply(client, jid,
            f"👋 *Welcome Settings*\n\n"
            f"Status: {'✅ ON' if enabled else '❌ OFF'}\n"
            f"Message: {message}\n\n"
            f"*Usage:*\n"
            f"{prefix}welcome on - Enable with default\n"
            f"{prefix}welcome off - Disable\n"
            f"{prefix}welcome <text> - Set custom message\n\n"
            f"💡 Tip: Use @user to mention the new member"
        )
    return True


@command("goodbye")
async def cmd_goodbye(client, jid, args, sender_jid, sender_num, session_id, handler, msg, **kwargs):
    chat = await _require_group(handler, client, jid, msg)
    if not chat:
        return True

    group_id = chat.id._serialized
    prefix = await handler.get_prefix()
    sub_cmd = (args[0] or "").lower() if args else ""

    if sub_cmd == "on":
        await handler.set_group_setting(group_id, "goodbyeEnabled", True)
        default_msg = "😢 @user has left the group. We'll miss you!"
        await handler.set_group_setting(group_id, "goodbyeMessage", default_msg)
        return await handler.send_reply(client, jid,
            f"✅ Goodbye messages enabled.\n\nMessage: {default_msg}"
        )

    elif sub_cmd == "off":
        await handler.set_group_setting(group_id, "goodbyeEnabled", False)
        return await handler.send_reply(client, jid, "✅ Goodbye messages disabled.")

    elif args:
        custom_msg = " ".join(args)
        await handler.set_group_setting(group_id, "goodbyeMessage", custom_msg)
        await handler.set_group_setting(group_id, "goodbyeEnabled", True)
        return await handler.send_reply(client, jid,
            f"✅ Goodbye message set to:\n\n{custom_msg}"
        )

    else:
        enabled = await handler.get_group_setting(group_id, "goodbyeEnabled", False)
        message = await handler.get_group_setting(group_id, "goodbyeMessage", "Not set")
        return await handler.send_reply(client, jid,
            f"🚪 *Goodbye Settings*\n\n"
            f"Status: {'✅ ON' if enabled else '❌ OFF'}\n"
            f"Message: {message}\n\n"
            f"*Usage:*\n"
            f"{prefix}goodbye on - Enable with default\n"
            f"{prefix}goodbye off - Disable\n"
            f"{prefix}goodbye <text> - Set custom message\n\n"
            f"💡 Tip: Use @user to mention the leaving member"
        )
    return True


# ============================================================
# PROTECTION
# ============================================================

@command("antistatusmention")
async def cmd_antistatusmention(client, jid, args, sender_jid, sender_num, session_id, handler, msg, **kwargs):
    chat = await _require_group(handler, client, jid, msg)
    if not chat:
        return True
    if not await _require_sender_admin(handler, client, jid, chat, sender_jid):
        return True
    if not await _require_bot_admin(handler, client, jid, chat, "enforce this"):
        return True

    group_id = chat.id._serialized
    prefix = await handler.get_prefix()
    action = (args[0] or "").lower() if args else ""
    state = (args[1] or "").lower() if len(args) > 1 else ""

    if not action or not state:
        current = handler._anti_status_mention.get(group_id, {"enabled": False, "action": "warn"})
        return await handler.send_reply(client, jid,
            f"📵 *Anti-Status Mention Protection*\n\n"
            f"Status: {'✅ ON' if current['enabled'] else '❌ OFF'}\n"
            f"Action: {current['action']}\n\n"
            f"*Usage:*\n{prefix}antistatusmention <delete|kick|warn> <on|off>\n\n"
            f"*Actions:*\n"
            f"• delete - Delete the status mention\n"
            f"• kick - Remove the person\n"
            f"• warn - Send warning\n\n"
            f"*Example:* {prefix}antistatusmention kick on"
        )

    if action not in ("delete", "kick", "warn"):
        return await handler.send_reply(client, jid, "❌ Action must be: delete, kick, or warn")
    if state not in ("on", "off"):
        return await handler.send_reply(client, jid, "❌ State must be: on or off")

    handler._anti_status_mention[group_id] = {"enabled": state == "on", "action": action}
    await handler.set_group_setting(group_id, "antiStatusMention", {"enabled": state == "on", "action": action})

    action_emoji = {"delete": "🗑️", "kick": "👢", "warn": "⚠️"}.get(action, "")
    await handler.send_reply(client, jid,
        f"{action_emoji} Anti-status mention protection {'enabled' if state == 'on' else 'disabled'}\n"
        f"Action: {action}"
    )
    return True


# ============================================================
# MODERATION
# ============================================================

@command("onlyadmin")
async def cmd_onlyadmin(client, jid, args, sender_jid, sender_num, session_id, handler, msg, **kwargs):
    chat = await _require_group(handler, client, jid, msg)
    if not chat:
        return True
    if not await _require_sender_admin(handler, client, jid, chat, sender_jid):
        return True
    if not await _require_bot_admin(handler, client, jid, chat, "enforce this"):
        return True

    group_id = chat.id._serialized
    prefix = await handler.get_prefix()
    state = (args[0] or "").lower() if args else ""

    if state not in ("on", "off"):
        current = handler._only_admin_settings.get(group_id, False)
        return await handler.send_reply(client, jid,
            f"🔒 *Admin-Only Messaging*\nStatus: {'✅ ON' if current else '❌ OFF'}\n\nUsage: {prefix}onlyadmin on/off"
        )

    handler._only_admin_settings[group_id] = state == "on"
    await handler.set_group_setting(group_id, "onlyAdmin", state == "on")
    await handler.send_reply(client, jid, f"✅ Admin-only messaging {'enabled' if state == 'on' else 'disabled'}.")
    return True


@command("kickall")
async def cmd_kickall(client, jid, args, sender_jid, sender_num, session_id, handler, msg, **kwargs):
    chat = await _require_group(handler, client, jid, msg)
    if not chat:
        return True
    if not await _require_sender_admin(handler, client, jid, chat, sender_jid):
        return True
    if not await _require_bot_admin(handler, client, jid, chat, "kick members"):
        return True

    admin_ids = await _get_group_admins(chat)
    non_admins = [p for p in chat.participants if p.id._serialized not in admin_ids]

    if not non_admins:
        return await handler.send_reply(client, jid, "❌ No non-admin members to kick.")

    if not args or args[0].upper() != "CONFIRM":
        prefix = await handler.get_prefix()
        return await handler.send_reply(client, jid,
            f"⚠️ *Kick All Confirmation*\n\n"
            f"This will kick {len(non_admins)} non-admin members.\n\n"
            f"Type: {prefix}kickall CONFIRM to proceed."
        )

    await handler.send_reply(client, jid, f"🔄 Kicking {len(non_admins)} members...")

    kicked = 0
    batch_size = 20
    for i in range(0, len(non_admins), batch_size):
        batch = non_admins[i:i + batch_size]
        batch_jids = [p.id._serialized for p in batch]
        try:
            await chat.removeParticipants(batch_jids)
            kicked += len(batch)
        except Exception:
            pass
        time.sleep(2)

    await handler.send_reply(client, jid, f"✅ Successfully kicked {kicked} members.")
    return True


@command("groupdesc")
async def cmd_groupdesc(client, jid, args, sender_jid, sender_num, session_id, handler, msg, **kwargs):
    chat = await _require_group(handler, client, jid, msg)
    if not chat:
        return True

    if not args:
        desc = chat.description or "No description set"
        return await handler.send_reply(client, jid, f"📋 *Group Description:*\n{desc}")

    if not await _require_sender_admin(handler, client, jid, chat, sender_jid):
        return True
    if not await _require_bot_admin(handler, client, jid, chat, "change description"):
        return True

    new_desc = " ".join(args)
    try:
        await chat.setDescription(new_desc)
        await handler.send_reply(client, jid, "✅ Group description updated!")
    except Exception as e:
        await handler.send_reply(client, jid, f"❌ Failed: {e}")
    return True


@command("members")
async def cmd_members(client, jid, args, sender_jid, sender_num, session_id, handler, msg, **kwargs):
    chat = await _require_group(handler, client, jid, msg)
    if not chat:
        return True

    group_id = chat.id._serialized

    # Check cache
    cached = handler._member_stats_cache.get(group_id)
    if cached and (time.time() * 1000) - cached["timestamp"] < settings.MEMBERS_CACHE_TTL:
        return await handler.send_reply(client, jid, cached["stats"])

    participants = chat.participants
    admin_ids = await _get_group_admins(chat)
    admin_count = len(admin_ids)
    total_count = len(participants)

    # Country breakdown
    country_stats = {}
    for p in participants:
        number = get_user_number(p.id._serialized)
        country = get_country_from_number(number)
        key = f"{country['flag']} {country['name']}"
        country_stats[key] = country_stats.get(key, 0) + 1

    sorted_countries = sorted(country_stats.items(), key=lambda x: x[1], reverse=True)

    text = (
        f"👥 *Group Members Stats*\n\n"
        f"📊 Total Members: {total_count}\n"
        f"👑 Total Admins: {admin_count}\n\n"
        f"🌍 *Members by Country:*\n"
    )

    for country, count in sorted_countries[:15]:
        text += f"{country}: {count} members\n"

    if len(sorted_countries) > 15:
        other = sum(c for _, c in sorted_countries[15:])
        text += f"Other: {other} members\n"

    handler._member_stats_cache[group_id] = {"stats": text, "timestamp": time.time() * 1000}
    await handler.send_reply(client, jid, text)
    return True


# ============================================================
# MUTE SYSTEM
# ============================================================

@command("mute")
async def cmd_mute(client, jid, args, sender_jid, sender_num, session_id, handler, msg, **kwargs):
    chat = await _require_group(handler, client, jid, msg)
    if not chat:
        return True
    if not await _require_sender_admin(handler, client, jid, chat, sender_jid):
        return True
    if not await _require_bot_admin(handler, client, jid, chat, "enforce mute"):
        return True

    target = _get_target_from_mention_or_arg(handler, msg, args)
    if not target:
        prefix = await handler.get_prefix()
        return await handler.send_reply(client, jid,
            f"❌ Usage: {prefix}mute @user <time> or {prefix}mute <number> <time>\nTime formats: 10m, 1h, 1d"
        )

    time_str = args[-1] if args else None
    if not time_str:
        return await handler.send_reply(client, jid, "❌ Please specify a time (e.g., 10m, 1h, 1d)")

    duration_ms = _parse_duration(time_str)
    if duration_ms is None:
        return await handler.send_reply(client, jid, "❌ Invalid time format. Use: 10s, 10m, 1h, 1d")

    group_id = chat.id._serialized
    if group_id not in handler._muted_users:
        handler._muted_users[group_id] = {}

    until = time.time() * 1000 + duration_ms
    handler._muted_users[group_id][target] = {"until": until, "by": sender_jid}

    await handler.send_reply(client, jid, f"🔇 @{target.split('@')[0]} muted for {time_str}.")
    return True


@command("unmute")
async def cmd_unmute(client, jid, args, sender_jid, sender_num, session_id, handler, msg, **kwargs):
    chat = await _require_group(handler, client, jid, msg)
    if not chat:
        return True
    if not await _require_sender_admin(handler, client, jid, chat, sender_jid):
        return True

    target = _get_target_from_mention_or_arg(handler, msg, args)
    if not target:
        prefix = await handler.get_prefix()
        return await handler.send_reply(client, jid,
            f"❌ Usage: {prefix}unmute @user or {prefix}unmute <number>"
        )

    group_id = chat.id._serialized
    if group_id in handler._muted_users:
        handler._muted_users[group_id].pop(target, None)

    await handler.send_reply(client, jid, f"🔊 @{target.split('@')[0]} unmuted.")
    return True


@command("mutelist")
async def cmd_mutelist(client, jid, args, sender_jid, sender_num, session_id, handler, msg, **kwargs):
    chat = await _require_group(handler, client, jid, msg)
    if not chat:
        return True

    group_id = chat.id._serialized
    group_mutes = handler._muted_users.get(group_id, {})

    if not group_mutes:
        return await handler.send_reply(client, jid, "📋 No muted members in this group.")

    now = time.time() * 1000
    active = {uid: data for uid, data in group_mutes.items() if data["until"] > now}

    if not active:
        return await handler.send_reply(client, jid, "📋 No currently muted members.")

    text = "🔇 *Muted Members*\n\n"
    for user_id, data in active.items():
        remaining = max(0, data["until"] - now)
        minutes = int(remaining // 60000)
        text += f"• @{user_id.split('@')[0]} - {minutes} min remaining\n"

    await handler.send_reply(client, jid, text)
    return True


@command("setwarn")
async def cmd_setwarn(client, jid, args, sender_jid, sender_num, session_id, handler, msg, **kwargs):
    chat = await _require_group(handler, client, jid, msg)
    if not chat:
        return True
    if not await _require_sender_admin(handler, client, jid, chat, sender_jid):
        return True

    try:
        limit = int(args[0]) if args else 0
    except (ValueError, IndexError):
        return await handler.send_reply(client, jid, "❌ Please provide a limit between 1 and 10.")

    if limit < 1 or limit > 10:
        return await handler.send_reply(client, jid, "❌ Please provide a limit between 1 and 10.")

    group_id = chat.id._serialized
    await handler.set_group_setting(group_id, "warnLimit", limit)
    await handler.send_reply(client, jid, f"✅ Warning limit set to {limit}.")
    return True


# ============================================================
# BAD WORD FILTER
# ============================================================

@command("antibadword")
async def cmd_antibadword(client, jid, args, sender_jid, sender_num, session_id, handler, msg, **kwargs):
    chat = await _require_group(handler, client, jid, msg)
    if not chat:
        return True
    if not await _require_sender_admin(handler, client, jid, chat, sender_jid):
        return True
    if not await _require_bot_admin(handler, client, jid, chat, "enforce this"):
        return True

    group_id = chat.id._serialized
    prefix = await handler.get_prefix()
    action = (args[0] or "").lower() if args else ""
    state = (args[1] or "").lower() if len(args) > 1 else ""

    if not action or not state:
        enabled = await handler.get_group_setting(group_id, "antiBadWord", False)
        current_action = await handler.get_group_setting(group_id, "badWordAction", "delete")
        return await handler.send_reply(client, jid,
            f"🚫 *Bad Word Filter*\n"
            f"Status: {'✅ ON' if enabled else '❌ OFF'}\n"
            f"Action: {current_action}\n\n"
            f"Usage: {prefix}antibadword <delete|warn|kick|mute> <on|off>"
        )

    if action not in ("delete", "warn", "kick", "mute"):
        return await handler.send_reply(client, jid, "❌ Action must be: delete, warn, kick, mute")
    if state not in ("on", "off"):
        return await handler.send_reply(client, jid, "❌ State must be: on, off")

    await handler.set_group_setting(group_id, "antiBadWord", state == "on")
    await handler.set_group_setting(group_id, "badWordAction", action)
    await handler.send_reply(client, jid, f"✅ Bad word filter {'enabled' if state == 'on' else 'disabled'} ({action}).")
    return True


@command("addbadword")
async def cmd_addbadword(client, jid, args, sender_jid, sender_num, session_id, handler, msg, **kwargs):
    chat = await _require_group(handler, client, jid, msg)
    if not chat:
        return True
    if not await _require_sender_admin(handler, client, jid, chat, sender_jid):
        return True

    word = (args[0] or "").lower() if args else ""
    if not word:
        prefix = await handler.get_prefix()
        return await handler.send_reply(client, jid, f"❌ Usage: {prefix}addbadword <word>")

    group_id = chat.id._serialized
    if group_id not in handler._bad_words_cache:
        saved = await handler.get_group_setting(group_id, "badWords", [])
        handler._bad_words_cache[group_id] = set(saved)

    handler._bad_words_cache[group_id].add(word)
    await handler.set_group_setting(group_id, "badWords", list(handler._bad_words_cache[group_id]))
    await handler.send_reply(client, jid, f"✅ \"{word}\" added to bad word list.")
    return True


@command("removebadword")
async def cmd_removebadword(client, jid, args, sender_jid, sender_num, session_id, handler, msg, **kwargs):
    chat = await _require_group(handler, client, jid, msg)
    if not chat:
        return True
    if not await _require_sender_admin(handler, client, jid, chat, sender_jid):
        return True

    word = (args[0] or "").lower() if args else ""
    if not word:
        prefix = await handler.get_prefix()
        return await handler.send_reply(client, jid, f"❌ Usage: {prefix}removebadword <word>")

    group_id = chat.id._serialized
    if group_id not in handler._bad_words_cache:
        saved = await handler.get_group_setting(group_id, "badWords", [])
        handler._bad_words_cache[group_id] = set(saved)

    removed = word in handler._bad_words_cache[group_id]
    handler._bad_words_cache[group_id].discard(word)
    await handler.set_group_setting(group_id, "badWords", list(handler._bad_words_cache[group_id]))

    await handler.send_reply(client, jid,
        f"✅ \"{word}\" removed from bad word list." if removed else f"❌ \"{word}\" not in bad word list."
    )
    return True


@command("listbadword")
async def cmd_listbadword(client, jid, args, sender_jid, sender_num, session_id, handler, msg, **kwargs):
    chat = await _require_group(handler, client, jid, msg)
    if not chat:
        return True

    group_id = chat.id._serialized
    if group_id not in handler._bad_words_cache:
        saved = await handler.get_group_setting(group_id, "badWords", [])
        handler._bad_words_cache[group_id] = set(saved)

    words = handler._bad_words_cache[group_id]
    if not words:
        return await handler.send_reply(client, jid, "📋 No bad words configured for this group.")

    word_list = ", ".join(sorted(words))
    await handler.send_reply(client, jid, f"🚫 *Bad Words ({len(words)})*\n{word_list}")
    return True