"""
server/whatsapp/handlers/status_handler.py — Status view handler
"""
from __future__ import annotations

from .base_handler import BaseHandler
from rich.console import Console

console = Console()


class StatusHandler(BaseHandler):
    """Handles WhatsApp status events."""

    async def should_view_status(self) -> bool:
        """Check if auto-view-status is enabled for this session."""
        from server.models.bot_setting import BotSetting
        return await BotSetting.get_value(self.session_id, "autoViewStatus", False)

    async def handle_status(self, client, status_msg):
        """Auto-view a status if enabled."""
        if await self.should_view_status():
            try:
                client.send_read_receipt(status_msg)
                console.print(f"[dim]Auto-viewed status[/dim]")
            except Exception:
                pass