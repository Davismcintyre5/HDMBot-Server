"""
server/whatsapp/handlers/group_handler.py — Group join/leave events
"""
from __future__ import annotations

from .base_handler import BaseHandler
from rich.console import Console

console = Console()


class GroupHandler(BaseHandler):
    """Handles group-related events (join, leave)."""

    async def handle_join(self, client, chat_id: str, new_members: list):
        """Send welcome message when members join."""
        try:
            from server.models.bot_setting import BotSetting
            enabled = await BotSetting.get_value(chat_id, "welcomeEnabled", False)
            if not enabled:
                return

            msg_template = await BotSetting.get_value(
                chat_id, "welcomeMessage",
                "👋 Welcome to the group!"
            )

            for member_id in new_members:
                try:
                    contact = client.get_contact(member_id)
                    name = contact.pushname or contact.number or self.get_user_number(member_id)
                    msg = msg_template.replace("@user", f"@{name}")
                    client.send_message(chat_id, msg)
                except Exception as e:
                    console.print(f"[yellow]Welcome failed for {member_id}: {e}[/yellow]")
        except Exception as e:
            console.print(f"[yellow]Group join handler error: {e}[/yellow]")

    async def handle_leave(self, client, chat_id: str, leaver_id: str):
        """Send goodbye message when a member leaves."""
        try:
            from server.models.bot_setting import BotSetting
            enabled = await BotSetting.get_value(chat_id, "goodbyeEnabled", False)
            if not enabled:
                return

            msg_template = await BotSetting.get_value(
                chat_id, "goodbyeMessage",
                "😢 @user has left the group. We'll miss you!"
            )

            try:
                contact = client.get_contact(leaver_id)
                name = contact.pushname or contact.number or self.get_user_number(leaver_id)
                msg = msg_template.replace("@user", f"@{name}")
                client.send_message(chat_id, msg)
            except Exception as e:
                console.print(f"[yellow]Goodbye failed for {leaver_id}: {e}[/yellow]")
        except Exception as e:
            console.print(f"[yellow]Group leave handler error: {e}[/yellow]")