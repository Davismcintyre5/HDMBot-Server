"""
server/whatsapp/commands/fun.py — Fun commands
joke, quote
"""
import requests
from server.whatsapp.handlers.command_handler import command, register_builtin


def register():
    register_builtin({"name": "joke", "description": "😄 Random joke", "category": "fun"})
    register_builtin({"name": "quote", "description": "💬 Inspirational quote", "category": "fun"})


async def _get_joke() -> str:
    try:
        resp = requests.get("https://v2.jokeapi.dev/joke/Any?safe-mode", timeout=5)
        data = resp.json()
        if data.get("type") == "single":
            return data["joke"]
        return f"{data.get('setup', '')}\n\n{data.get('delivery', '')}"
    except Exception:
        return "Why did the developer go broke? Because he used up all his cache."


async def _get_quote() -> str:
    try:
        resp = requests.get("https://api.quotable.io/random", timeout=5)
        data = resp.json()
        return f"\"{data['content']}\"\n— {data['author']}"
    except Exception:
        return '"The only way to do great work is to love what you do." — Steve Jobs'


@command("joke")
async def cmd_joke(client, jid, args, sender_jid, sender_num, session_id, handler, msg, **kwargs):
    await handler.send_reply(client, jid, await _get_joke())
    return True


@command("quote")
async def cmd_quote(client, jid, args, sender_jid, sender_num, session_id, handler, msg, **kwargs):
    await handler.send_reply(client, jid, await _get_quote())
    return True