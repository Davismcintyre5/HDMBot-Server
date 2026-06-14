"""
server/whatsapp/commands/bug.py — Bug/testing commands
bugmenu, bug, stopbug, addbuguser, listbugusers, removebuguser, antibug, buglogs, clearbuglogs
"""
import time
import threading
from datetime import datetime
from server.whatsapp.handlers.command_handler import command, register_builtin
from server.config.settings import settings
from server.utils.helpers import create_progress_bar


def register():
    if settings.ENABLE_BUG_COMMANDS:
        builtins = [
            {"name": "bugmenu", "description": "🐛 Bug testing menu", "category": "bug"},
            {"name": "bug", "description": "💣 Start message attack", "category": "bug"},
            {"name": "stopbug", "description": "🛑 Stop all attacks", "category": "bug"},
            {"name": "addbuguser", "description": "🐛 Add bug user", "category": "bug", "admin_only": True},
            {"name": "listbugusers", "description": "📋 List bug users", "category": "bug", "admin_only": True},
            {"name": "removebuguser", "description": "➖ Remove bug user", "category": "bug", "admin_only": True},
            {"name": "antibug", "description": "🛡️ Toggle bug protection", "category": "bug", "admin_only": True},
            {"name": "buglogs", "description": "📜 View bug logs", "category": "bug", "admin_only": True},
            {"name": "clearbuglogs", "description": "🗑️ Clear bug logs", "category": "bug", "admin_only": True},
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


def _start_bug_attack(client, target_jid, msg_text, count, interval_ms, from_jid, session_id, handler):
    attack_id = f"{int(time.time() * 1000)}_{target_jid}"
    sent_count = [0]

    attack = {
        "stopped": False,
        "interval": None,
        "target": target_jid,
        "from": from_jid,
        "session_id": session_id,
    }
    handler._active_attacks[attack_id] = attack

    def _loop():
        a = handler._active_attacks.get(attack_id)
        if not a or a["stopped"] or sent_count[0] >= count:
            if a and a.get("interval"):
                try:
                    a["interval"].cancel()
                except Exception:
                    pass
            handler._active_attacks.pop(attack_id, None)
            try:
                client.send_message(from_jid,
                    f"✅ *BUG ATTACK COMPLETED*\n\n"
                    f"📱 Target: {target_jid.split('@')[0]}\n"
                    f"📨 Sent: {sent_count[0]}/{count}"
                )
            except Exception:
                pass
            return

        try:
            client.send_message(target_jid, msg_text)
            sent_count[0] += 1
        except Exception:
            pass

        try:
            a["interval"] = threading.Timer(interval_ms / 1000, _loop)
            a["interval"].daemon = True
            a["interval"].start()
        except Exception:
            pass

    threading.Thread(target=_loop, daemon=True).start()
    return attack_id


@command("bugmenu")
async def cmd_bugmenu(client, jid, args, sender_jid, sender_num, session_id, handler, msg, **kwargs):
    if not settings.ENABLE_BUG_COMMANDS:
        return await handler.send_reply(client, jid, "❌ Bug commands disabled.")

    anti_bug = await handler.get_session_setting("antiBug", False)
    if anti_bug and not await handler.is_user_allowed_for_bug(sender_jid):
        logs = handler._bug_logs_cache.get(session_id, [])
        logs.append({"attacker": sender_num, "command": "bugmenu", "timestamp": datetime.now().isoformat()})
        handler._bug_logs_cache[session_id] = logs
        return await handler.send_reply(client, jid, "🛡️ Anti-bug protection is enabled. You are not authorized.")

    if not await handler.is_user_allowed_for_bug(sender_jid):
        return await handler.send_reply(client, jid, "❌ Not authorized.")

    prefix = await handler.get_prefix()
    await handler.send_reply(client, jid,
        f"🐛 *BUG MENU*\n\n"
        f"{prefix}bug <number> <message> <count> <interval>\n"
        f"{prefix}stopbug\n\n"
        f"Example: {prefix}bug 254712345678 \"Hello\" 50 2"
    )
    return True


@command("bug")
async def cmd_bug(client, jid, args, sender_jid, sender_num, session_id, handler, msg, **kwargs):
    if not settings.ENABLE_BUG_COMMANDS:
        return await handler.send_reply(client, jid, "❌ Bug commands disabled.")

    anti_bug = await handler.get_session_setting("antiBug", False)
    if anti_bug and not await handler.is_user_allowed_for_bug(sender_jid):
        logs = handler._bug_logs_cache.get(session_id, [])
        logs.append({"attacker": sender_num, "command": f"bug {' '.join(args)}", "timestamp": datetime.now().isoformat()})
        handler._bug_logs_cache[session_id] = logs
        return await handler.send_reply(client, jid, "🛡️ Anti-bug protection is enabled. You are not authorized.")

    if not await handler.is_user_allowed_for_bug(sender_jid):
        return await handler.send_reply(client, jid, "❌ Not authorized.")

    prefix = await handler.get_prefix()
    if len(args) < 4:
        return await handler.send_reply(client, jid,
            f"❌ Usage: {prefix}bug <number> <message> <count> <interval>\n"
            f"Example: {prefix}bug 254712345678 \"Hello\" 50 2"
        )

    target_number = handler.format_number(args[0])
    try:
        count = int(args[-2])
        interval = float(args[-1])
    except (ValueError, IndexError):
        return await handler.send_reply(client, jid, f"❌ Count and interval must be numbers.")

    msg_text = " ".join(args[1:-2])

    if len(target_number) < 10:
        return await handler.send_reply(client, jid, "❌ Invalid phone number.")
    if not msg_text:
        return await handler.send_reply(client, jid, "❌ Please provide a message.")
    if count < 1 or count > settings.BUG_MAX_MESSAGES:
        return await handler.send_reply(client, jid, f"❌ Count must be 1-{settings.BUG_MAX_MESSAGES}.")
    if interval < 0.01 or interval > 60:
        return await handler.send_reply(client, jid, "❌ Interval must be 0.01-60 seconds.")

    target_jid = f"{target_number}@c.us"
    interval_ms = int(interval * 1000)

    _start_bug_attack(client, target_jid, msg_text, count, interval_ms, jid, session_id, handler)
    return True


@command("stopbug")
async def cmd_stopbug(client, jid, args, sender_jid, sender_num, session_id, handler, msg, **kwargs):
    if not settings.ENABLE_BUG_COMMANDS:
        return await handler.send_reply(client, jid, "❌ Bug commands disabled.")
    if not await handler.is_user_allowed_for_bug(sender_jid):
        return await handler.send_reply(client, jid, "❌ Not authorized.")

    stopped = 0
    for attack_id, attack in list(handler._active_attacks.items()):
        if attack.get("from") != jid:
            continue
        attack["stopped"] = True
        if attack.get("interval"):
            try:
                attack["interval"].cancel()
            except Exception:
                pass
        handler._active_attacks.pop(attack_id, None)
        stopped += 1

    await handler.send_reply(client, jid, f"✅ Stopped {stopped} attack(s)." if stopped else "❌ No active attacks.")
    return True


@command("addbuguser")
async def cmd_addbuguser(client, jid, args, sender_jid, sender_num, session_id, handler, msg, **kwargs):
    if not await handler.is_admin(sender_jid):
        return await handler.send_reply(client, jid, "❌ Admin only.")
    target = _get_target_number(handler, msg, args)
    if not target:
        prefix = await handler.get_prefix()
        return await handler.send_reply(client, jid, f"❌ Usage: {prefix}addbuguser <number> or reply to user")
    bug_users = await handler.get_session_setting("bugUsers", [])
    if target in bug_users:
        return await handler.send_reply(client, jid, f"❌ @{target} is already a bug user.")
    bug_users.append(target)
    await handler.set_session_setting("bugUsers", bug_users)
    await handler.send_reply(client, jid, f"✅ @{target} added to bug users.")
    return True


@command("listbugusers")
async def cmd_listbugusers(client, jid, args, sender_jid, sender_num, session_id, handler, msg, **kwargs):
    if not await handler.is_admin(sender_jid):
        return await handler.send_reply(client, jid, "❌ Admin only.")
    bug_users = await handler.get_session_setting("bugUsers", [])
    env_users = settings.BUG_ALLOWED_USERS
    all_users = list(dict.fromkeys(bug_users + env_users))
    if not all_users:
        return await handler.send_reply(client, jid, "📋 No bug users configured.")
    text = f"🐛 *Bug Users ({len(all_users)})*\n"
    for i, u in enumerate(all_users):
        source = " [ENV]" if u in env_users else ""
        text += f"{i+1}. {u}{source}\n"
    await handler.send_reply(client, jid, text)
    return True


@command("removebuguser")
async def cmd_removebuguser(client, jid, args, sender_jid, sender_num, session_id, handler, msg, **kwargs):
    if not await handler.is_admin(sender_jid):
        return await handler.send_reply(client, jid, "❌ Admin only.")
    target = _get_target_number(handler, msg, args)
    if not target:
        prefix = await handler.get_prefix()
        return await handler.send_reply(client, jid, f"❌ Usage: {prefix}removebuguser <number> or reply to user")
    bug_users = await handler.get_session_setting("bugUsers", [])
    if target not in bug_users:
        return await handler.send_reply(client, jid, f"❌ @{target} is not a bug user.")
    bug_users.remove(target)
    await handler.set_session_setting("bugUsers", bug_users)
    await handler.send_reply(client, jid, f"✅ @{target} removed from bug users.")
    return True


@command("antibug")
async def cmd_antibug(client, jid, args, sender_jid, sender_num, session_id, handler, msg, **kwargs):
    if not await handler.is_admin(sender_jid):
        return await handler.send_reply(client, jid, "❌ Admin only.")
    prefix = await handler.get_prefix()
    state = (args[0] or "").lower() if args else ""
    if state not in ("on", "off"):
        current = await handler.get_session_setting("antiBug", False)
        return await handler.send_reply(client, jid,
            f"🛡️ *Anti-Bug Protection*\nStatus: {'✅ ON' if current else '❌ OFF'}\n\nUsage: {prefix}antibug on/off"
        )
    await handler.set_session_setting("antiBug", state == "on")
    await handler.send_reply(client, jid, f"✅ Anti-bug protection {'enabled' if state == 'on' else 'disabled'}.")
    return True


@command("buglogs")
async def cmd_buglogs(client, jid, args, sender_jid, sender_num, session_id, handler, msg, **kwargs):
    if not await handler.is_admin(sender_jid):
        return await handler.send_reply(client, jid, "❌ Admin only.")
    logs = handler._bug_logs_cache.get(session_id, [])
    if not logs:
        return await handler.send_reply(client, jid, "📜 No bug logs for this session.")
    recent = logs[-10:][::-1]
    text = "🐛 *Recent Bug Logs*\n\n"
    for i, log in enumerate(recent):
        text += f"{i+1}. {log['attacker']} - {log['command']}\n   {log['timestamp']}\n\n"
    await handler.send_reply(client, jid, text)
    return True


@command("clearbuglogs")
async def cmd_clearbuglogs(client, jid, args, sender_jid, sender_num, session_id, handler, msg, **kwargs):
    if not await handler.is_super_admin(sender_jid) and not handler.is_owner(sender_jid):
        return await handler.send_reply(client, jid, "❌ Only super admins or owner can clear bug logs.")
    handler._bug_logs_cache.pop(session_id, None)
    await handler.send_reply(client, jid, "✅ Bug logs cleared.")
    return True