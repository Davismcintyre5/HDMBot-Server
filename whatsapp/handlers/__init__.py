"""
server/whatsapp/handlers/__init__.py — Handlers package
"""
from .base_handler import BaseHandler
from .command_handler import CommandHandler, command, register_builtin
from .command_registry import _COMMANDS, _BUILTIN_COMMANDS, _commands_cache, _last_commands_load
from .message_handler import MessageHandler
from .autoreply_handler import AutoReplyHandler
from .group_handler import GroupHandler
from .status_handler import StatusHandler

__all__ = [
    "BaseHandler",
    "CommandHandler",
    "command",
    "register_builtin",
    "_COMMANDS",
    "_BUILTIN_COMMANDS",
    "_commands_cache",
    "_last_commands_load",
    "MessageHandler",
    "AutoReplyHandler",
    "GroupHandler",
    "StatusHandler",
]