"""
server/whatsapp/handlers/command_registry.py — Shared command registry
Separated to avoid circular imports between commands and command_handler.
"""
from typing import Callable, Dict

# Global command function registry (populated by @command decorator)
_COMMANDS: Dict[str, Callable] = {}

# Built-in command metadata (for menu, help, etc.)
_BUILTIN_COMMANDS: list[dict] = []

# Command cache (populated at runtime, like JS commandsCache Map)
_commands_cache: Dict[str, dict] = {}
_last_commands_load: float = 0