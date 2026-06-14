"""
server/controllers/__init__.py — Controllers package
"""
from .auth_controller import bp as auth_bp
from .command_controller import bp as command_bp
from .autoreply_controller import bp as autoreply_bp
from .message_controller import bp as message_bp
from .contact_controller import bp as contact_bp
from .broadcast_controller import bp as broadcast_bp
from .session_controller import bp as session_bp
from .setting_controller import bp as setting_bp
from .dashboard_controller import bp as dashboard_bp

__all__ = [
    "auth_bp", "command_bp", "autoreply_bp", "message_bp",
    "contact_bp", "broadcast_bp", "session_bp", "setting_bp", "dashboard_bp",
]