"""
server/whatsapp/handlers/command_handler.py — Command registry & dispatcher
"""
from __future__ import annotations

import time
import re
from typing import Callable, Dict, Optional

from rich.console import Console

from .base_handler import BaseHandler
from .command_registry import _COMMANDS, _BUILTIN_COMMANDS, _commands_cache, _last_commands_load
from config.settings import settings

console = Console()


def command(name: str, *aliases: str):
    """Decorator to register a command handler."""
    def decorator(fn: Callable):
        for key in [name, *aliases]:
            _COMMANDS[key.lower()] = fn
        return fn
    return decorator


def register_builtin(cmd_info: dict):
    """Register a built-in command's metadata."""
    if not any(c["name"] == cmd_info["name"] for c in _BUILTIN_COMMANDS):
        _BUILTIN_COMMANDS.append(cmd_info)


def get_all_commands() -> list[dict]:
    return sorted(_BUILTIN_COMMANDS, key=lambda c: c["name"])


class CommandHandler(BaseHandler):
    """Handles command parsing, caching, and execution."""

    async def load_commands(self) -> Dict[str, dict]:
        """Load commands from DB + built-ins into cache."""
        global _commands_cache, _last_commands_load

        now = time.time() * 1000
        if now - _last_commands_load < settings.COMMANDS_CACHE_TTL:
            return _commands_cache

        _commands_cache.clear()

        try:
            from models.command import Command
            db_commands = await Command.find_all_enabled(self.session_id)
            for cmd in db_commands:
                data = {
                    "name": cmd.name, "description": cmd.description or "No description",
                    "response": cmd.response, "category": cmd.category or "general",
                    "admin_only": cmd.admin_only, "aliases": cmd.aliases or [],
                    "is_dynamic": True, "times_used": cmd.times_used or 0, "_id": cmd._id,
                }
                _commands_cache[cmd.name] = data
                for alias in cmd.aliases:
                    _commands_cache[alias] = {**data, "is_alias": True, "parent": cmd.name}
        except Exception as e:
            console.print(f"[yellow]Failed to load DB commands: {e}[/yellow]")

        for cmd_info in _BUILTIN_COMMANDS:
            name = cmd_info["name"]
            if name not in _commands_cache:
                _commands_cache[name] = {**cmd_info, "is_builtin": True}

        _last_commands_load = now
        console.print(f"[dim]📦 Loaded {len(_commands_cache)} commands for {self.session_id}[/dim]")
        return _commands_cache

    async def execute(
        self, client, jid, message, body: str, sender_jid: str, is_self: bool = False
    ) -> bool:
        """Execute a command from a message body. Returns True if executed."""
        if not body:
            return False

        if await self._handle_menu_reply(client, jid, body, message):
            return True

        await self.load_commands()
        prefix = await self.get_prefix()
        sender_num = self.get_user_number(sender_jid)

        if not body.startswith(prefix):
            return False

        command_body = body[len(prefix):]
        parts = command_body.strip().split()
        if not parts:
            return False

        cmd_name = parts[0].lower()
        args = parts[1:]

        cmd_data = _commands_cache.get(cmd_name)
        if not cmd_data:
            return False

        if cmd_data.get("admin_only") and not await self.is_admin(sender_jid):
            await self.send_reply(client, jid, "❌ This command is for admins only.")
            return True

        if cmd_data.get("is_alias") and cmd_data.get("parent"):
            parent = _commands_cache.get(cmd_data["parent"])
            if parent:
                cmd_data = parent

        # Use raw JID object — never convert to string
        # For self-messages, use bot's real JID object so send_message works
        reply_jid = jid
        if is_self:
            try:
                if hasattr(client, 'info') and client.info and hasattr(client.info, 'wid'):
                    reply_jid = client.info.wid  # Raw JID object, no str()
            except Exception:
                pass

        try:
            if cmd_data.get("is_dynamic"):
                return await self._execute_dynamic(client, reply_jid, cmd_name, cmd_data)

            handler_fn = _COMMANDS.get(cmd_name)
            if handler_fn:
                console.print(
                    f"[dim]{self.ts()}[/dim] [bold cyan][CMD][/bold cyan] "
                    f"{prefix}{cmd_name} from {sender_num}"
                )
                await handler_fn(
                    client=client, jid=reply_jid, args=args,
                    sender_jid=sender_jid, sender_num=sender_num,
                    session_id=self.session_id, handler=self, msg=message,
                )
                return True

        except Exception as e:
            console.print(f"[red]Command error ({cmd_name}): {e}[/red]")
            console.print_exception()
            try:
                await self.send_reply(client, reply_jid, f"❌ Command error: {e}")
            except Exception:
                pass

        return False

    async def _execute_dynamic(self, client, jid, cmd_name: str, cmd_data: dict) -> bool:
        try:
            from models.command import Command
            if cmd_data.get("_id"):
                await Command.increment_usage(cmd_data["_id"])
            await self.send_reply(client, jid, cmd_data["response"])
            return True
        except Exception:
            return False

    async def _handle_menu_reply(self, client, jid, body: str, message) -> bool:
        user_num = self.get_user_number(str(jid))
        session = self.get_menu_session(jid)

        if not session:
            return False

        match = re.match(r"^(\d+)$", body.strip())
        if not match:
            return False

        num = int(match.group(1))
        items = session.get("items", [])
        item = next((i for i in items if i["number"] == num), None)

        if not item:
            await self.send_reply(client, jid, f"❌ Invalid number. Choose 1-{len(items)}")
            return True

        self.clear_menu_session(jid)
        cmd = item["command"]

        try:
            if cmd.get("is_dynamic"):
                await self._execute_dynamic(client, jid, cmd["name"], cmd)
            else:
                handler_fn = _COMMANDS.get(cmd["name"])
                if handler_fn:
                    await handler_fn(
                        client=client, jid=jid, args=[],
                        sender_jid=jid, sender_num=user_num,
                        session_id=self.session_id, handler=self, msg=message,
                    )
        except Exception as e:
            await self.send_reply(client, jid, f"❌ Failed: {e}")

        return True