"""
server/whatsapp/handlers/message_handler.py — Main message router
"""
from __future__ import annotations

from rich.console import Console

from .base_handler import BaseHandler
from .command_handler import CommandHandler
from .autoreply_handler import AutoReplyHandler
from .group_handler import GroupHandler

console = Console()


class MessageHandler(BaseHandler):
    """Routes incoming messages to the appropriate handler."""

    def __init__(self, session_id: str = "default"):
        super().__init__(session_id)
        self.command_handler = CommandHandler(session_id)
        self.autoreply_handler = AutoReplyHandler(session_id)
        self.group_handler = GroupHandler(session_id)

    async def handle(self, client, msg, session_id: str = None) -> bool:
        """Process an incoming message. Returns True if handled."""
        sid = session_id or self.session_id
        self.session_id = sid
        self.command_handler.session_id = sid
        self.autoreply_handler.session_id = sid
        self.group_handler.session_id = sid

        # Parse message info — keep JIDs as raw objects
        try:
            src = msg.Info.MessageSource
            chat_jid = src.Chat      # Raw JID object
            sender_jid = src.Sender  # Raw JID object
            is_from_me = src.IsFromMe
        except Exception as e:
            console.print(f"[red][MSG] Failed to parse Info: {e}[/red]")
            return False

        body = self.get_text(msg)

        # Convert to strings for display only
        try:
            sender_str = self.jid_to_str(sender_jid)
        except Exception:
            sender_str = str(sender_jid)
        try:
            chat_str = self.jid_to_str(chat_jid)
        except Exception:
            chat_str = str(chat_jid)

        # Log message
        from whatsapp.connection import print_msg
        print_msg("out" if is_from_me else "in", sender_str, chat_str, body or "[media/no text]")

        if not body:
            return False

        # Try command — pass raw JID objects
        try:
            is_cmd = await self.command_handler.execute(
                client, chat_jid, msg, body, sender_jid, is_from_me
            )
            if is_cmd:
                return True
        except Exception as e:
            console.print(f"[red]Command error: {e}[/red]")

        # Try auto-reply
        if not is_from_me:
            try:
                matched = await self.autoreply_handler.match(client, chat_jid, body, msg)
                if matched:
                    return True
            except Exception as e:
                console.print(f"[red]Auto-reply error: {e}[/red]")

        return False