"""
server/whatsapp/__init__.py — WhatsApp bot package
"""
from .connection import (
    build_client, send_text, get_text, jid_to_str,
    BOT_NAME, get_prefix, set_prefix, _COMMANDS,
)

__all__ = [
    "build_client", "send_text", "get_text", "jid_to_str",
    "BOT_NAME", "get_prefix", "set_prefix", "_COMMANDS",
]