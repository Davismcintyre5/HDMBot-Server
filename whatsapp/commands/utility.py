"""
server/whatsapp/commands/utility.py — Utility commands
poll, broadcast, pair
"""
import time
import re
from whatsapp.handlers.command_handler import command, register_builtin
from config.settings import settings


def register():
    builtins = [
        {"name": "poll", "description": "📊 Create a poll", "category": "utility"},
        {"name": "broadcast", "description": "📢 Broadcast to all groups", "category": "utility", "admin_only": True},
        {"name": "pair", "description": "🔗 Pair with code", "category": "utility"},
    ]
    for cmd in builtins:
        register_builtin(cmd)


@command("poll")
async def cmd_poll(client, jid, args, sender_jid, sender_num, session_id, handler, msg, **kwargs):
    full_text = " ".join(args)
    match = re.findall(r'"([^"]*)"', full_text)
    if len(match) < 2:
        prefix = await handler.get_prefix()
        return await handler.send_reply(client, jid,
            f"❌ Usage: {prefix}poll \"Question?\" \"Option1\" \"Option2\" \"Option3\" [duration]\n"
            f"Example: {prefix}poll \"Favorite color?\" \"Red\" \"Blue\" \"Green\" 5m"
        )
    question = match[0]
    options = match[1:6]
    poll_text = f"📊 *POLL*\n\n{question}\n\n"
    for i, opt in enumerate(options):
        poll_text += f"{i+1}️⃣ {opt}\n"
    poll_text += "\n_Reply with the number to vote!_"
    client.send_message(jid, poll_text)
    return True


@command("broadcast")
async def cmd_broadcast(client, jid, args, sender_jid, sender_num, session_id, handler, msg, **kwargs):
    if not await handler.is_admin(sender_jid):
        return await handler.send_reply(client, jid, "❌ Admin only.")
    broadcast_msg = " ".join(args) if args else ""
    if not broadcast_msg:
        prefix = await handler.get_prefix()
        return await handler.send_reply(client, jid, f"❌ Usage: {prefix}broadcast <message>")
    try:
        chats = client.get_chats()
        groups = [c for c in chats if hasattr(c, 'isGroup') and c.isGroup]
    except Exception:
        groups = []
    if not groups:
        return await handler.send_reply(client, jid, "❌ No groups found.")
    await handler.send_reply(client, jid, f"📢 Broadcasting to {len(groups)} groups...")
    sent = 0
    failed = 0
    for group in groups:
        try:
            client.send_message(group.id._serialized, f"📢 *BROADCAST*\n\n{broadcast_msg}")
            sent += 1
        except Exception:
            failed += 1
        time.sleep(1)
    await handler.send_reply(client, jid, f"✅ Broadcast complete!\n📨 Sent: {sent}\n❌ Failed: {failed}")
    return True


@command("pair")
async def cmd_pair(client, jid, args, sender_jid, sender_num, session_id, handler, msg, **kwargs):
    phone_number = args[0] if args else ""
    if not phone_number:
        prefix = await handler.get_prefix()
        return await handler.send_reply(client, jid, f"❌ Usage: {prefix}pair <phone_number>")
    formatted = handler.format_number(phone_number)
    try:
        code = client.get_pairing_code(formatted)
        handler._pairing_codes[code] = {
            "phone": formatted,
            "timestamp": time.time() * 1000,
        }
        await handler.send_reply(client, jid,
            f"🔗 *Pairing Code Generated*\n\n"
            f"📱 Phone: +{formatted}\n"
            f"🔑 Code: {code}\n\n"
            f"_This code expires in 5 minutes. Enter it on the target device to link._"
        )
    except Exception as e:
        await handler.send_reply(client, jid, f"❌ Failed to generate pairing code: {e}")
    return True