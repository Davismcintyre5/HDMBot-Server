"""
server/whatsapp/commands/__init__.py — Command registry & built-in registration
"""
from .general import register as register_general
from .fun import register as register_fun
from .settings import register as register_settings
from .admin import register as register_admin
from .ai import register as register_ai
from .media import register as register_media
from .bug import register as register_bug
from .utility import register as register_utility
from .group import register as register_group


def register_all_commands():
    """Register all built-in commands and their metadata."""
    register_general()
    register_fun()
    register_settings()
    register_admin()
    register_ai()
    register_media()
    register_bug()
    register_utility()
    register_group()