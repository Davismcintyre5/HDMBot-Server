"""
server/whatsapp/commands/ai.py — AI commands
deepseek, gemini, chatgpt, ai
"""
from whatsapp.handlers.command_handler import command, register_builtin
from config.settings import settings
from services.ai_service import ai_service


def register():
    if settings.ENABLE_AI_COMMANDS:
        builtins = [
            {"name": "deepseek", "description": "🤖 Ask DeepSeek AI", "category": "ai"},
            {"name": "gemini", "description": "🧠 Ask Gemini AI", "category": "ai"},
            {"name": "chatgpt", "description": "💬 Ask ChatGPT", "category": "ai"},
            {"name": "ai", "description": "✨ Default AI assistant", "category": "ai"},
        ]
        for cmd in builtins:
            register_builtin(cmd)


@command("deepseek")
async def cmd_deepseek(client, jid, args, sender_jid, sender_num, session_id, handler, msg, **kwargs):
    if not settings.ENABLE_AI_COMMANDS:
        return await handler.send_reply(client, jid, "❌ AI commands disabled.")
    if not args:
        prefix = await handler.get_prefix()
        return await handler.send_reply(client, jid, f"❌ Usage: {prefix}deepseek <question>")
    await handler.send_reply(client, jid, "🤖 Thinking...")
    response = ai_service.query_deepseek(" ".join(args))
    await handler.send_reply(client, jid, response)
    return True


@command("gemini")
async def cmd_gemini(client, jid, args, sender_jid, sender_num, session_id, handler, msg, **kwargs):
    if not settings.ENABLE_AI_COMMANDS:
        return await handler.send_reply(client, jid, "❌ AI commands disabled.")
    if not args:
        prefix = await handler.get_prefix()
        return await handler.send_reply(client, jid, f"❌ Usage: {prefix}gemini <question>")
    await handler.send_reply(client, jid, "🧠 Thinking...")
    response = ai_service.query_gemini(" ".join(args))
    await handler.send_reply(client, jid, response)
    return True


@command("chatgpt")
async def cmd_chatgpt(client, jid, args, sender_jid, sender_num, session_id, handler, msg, **kwargs):
    if not settings.ENABLE_AI_COMMANDS:
        return await handler.send_reply(client, jid, "❌ AI commands disabled.")
    if not args:
        prefix = await handler.get_prefix()
        return await handler.send_reply(client, jid, f"❌ Usage: {prefix}chatgpt <question>")
    await handler.send_reply(client, jid, "💬 Thinking...")
    response = ai_service.query_chatgpt(" ".join(args))
    await handler.send_reply(client, jid, response)
    return True


@command("ai")
async def cmd_ai(client, jid, args, sender_jid, sender_num, session_id, handler, msg, **kwargs):
    if not settings.ENABLE_AI_COMMANDS:
        return await handler.send_reply(client, jid, "❌ AI commands disabled.")
    if not args:
        prefix = await handler.get_prefix()
        return await handler.send_reply(client, jid, f"❌ Usage: {prefix}ai <question>")
    model = settings.DEFAULT_AI_MODEL
    if model == "gemini":
        return await cmd_gemini(client, jid, args, sender_jid, sender_num, session_id, handler, msg)
    elif model == "chatgpt":
        return await cmd_chatgpt(client, jid, args, sender_jid, sender_num, session_id, handler, msg)
    else:
        return await cmd_deepseek(client, jid, args, sender_jid, sender_num, session_id, handler, msg)