"""
server/config/settings.py — Application configuration
"""
import os
from typing import List, Optional
from dotenv import load_dotenv

load_dotenv()


class Settings:
    """Centralized settings loaded from environment variables."""
    
    # ============ SERVER ============
    NODE_ENV: str = os.getenv("NODE_ENV", "development")
    PORT: int = int(os.getenv("PORT", 5000))
    HOST: str = os.getenv("HOST", "localhost")
    FLASK_HOST: str = os.getenv("FLASK_HOST", "0.0.0.0")
    FLASK_PORT: int = int(os.getenv("FLASK_PORT", 5000))
    FLASK_DEBUG: bool = os.getenv("FLASK_DEBUG", "False").lower() in ("true", "1", "yes")
    
    # ============ MONGODB ============
    MONGODB_URI: str = os.getenv("MONGODB_URI", "mongodb://localhost:27017/hdm-bot")
    
    # ============ JWT AUTH ============
    JWT_SECRET: str = os.getenv("JWT_SECRET", "your_jwt_secret_here_change_this")
    JWT_EXPIRE: str = os.getenv("JWT_EXPIRE", "7d")
    JWT_REFRESH_EXPIRE: str = os.getenv("JWT_REFRESH_EXPIRE", "30d")
    
    # ============ BOT ============
    BOT_NAME: str = os.getenv("BOT_NAME", "HDM BOT")
    BOT_PREFIX: str = os.getenv("BOT_PREFIX", ".")
    BOT_OWNER_NUMBER: str = os.getenv("BOT_OWNER_NUMBER", "")
    BOT_SESSION_DIR: str = os.getenv("BOT_SESSION_DIR", "./server/whatsapp/sessions")
    SESSION_NAME: str = os.getenv("SESSION_NAME", "hdm_session")
    DB_PATH: str = os.getenv("DB_PATH", "store.db")
    OWNER_JID: str = os.getenv("OWNER_JID", "")
    
    # ============ QR / PAIRING ============
    PAIRING_ENABLED: bool = os.getenv("PAIRING_ENABLED", "true").lower() in ("true", "1", "yes")
    PAIRING_CODE_EXPIRE: int = int(os.getenv("PAIRING_CODE_EXPIRE", 60))
    PAIRING_PHONE: str = os.getenv("PAIRING_PHONE", "")
    
    # ============ MESSAGE LIMITS ============
    RATE_LIMIT_WINDOW: int = int(os.getenv("RATE_LIMIT_WINDOW", 60000))
    RATE_LIMIT_MAX: int = int(os.getenv("RATE_LIMIT_MAX", 30))
    AUTOREPLY_COOLDOWN_DEFAULT: int = int(os.getenv("AUTOREPLY_COOLDOWN_DEFAULT", 10))
    COMMAND_COOLDOWN_DEFAULT: int = int(os.getenv("COMMAND_COOLDOWN_DEFAULT", 5))
    
    # ============ MEDIA ============
    UPLOAD_DIR: str = os.getenv("UPLOAD_DIR", "./server/uploads")
    MAX_FILE_SIZE: int = int(os.getenv("MAX_FILE_SIZE", 10485760))
    ALLOWED_MEDIA_TYPES: List[str] = os.getenv("ALLOWED_MEDIA_TYPES", "image/jpeg,image/png,image/webp,video/mp4,audio/mp3").split(",")
    
    # ============ CORS ============
    CORS_ORIGIN: str = os.getenv("CORS_ORIGIN", "http://localhost:3000")
    
    # ============ LOGGING ============
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "debug")
    LOG_DIR: str = os.getenv("LOG_DIR", "./server/logs")
    LOG_RETENTION_DAYS: int = int(os.getenv("LOG_RETENTION_DAYS", 30))
    
    # ============ HDM BRIDGE ============
    HDM_API_KEY: str = os.getenv("HDM_API_KEY", "")
    HDM_API_URL: str = os.getenv("HDM_API_URL", "https://api.hdmbridge.com/api")
    HDM_FROM_EMAIL: str = os.getenv("HDM_FROM_EMAIL", "notifications@theirdomain.com")
    HDM_FROM_NAME: str = os.getenv("HDM_FROM_NAME", "HDM BOT")
    
    # ============ AI PROVIDERS ============
    DEEPSEEK_API_KEY: str = os.getenv("DEEPSEEK_API_KEY", "")
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    HDM_AI_API_URL: str = os.getenv("HDM_AI_API_URL", "")
    HDM_AI_API_KEY: str = os.getenv("HDM_AI_API_KEY", "")
    ENABLE_AI_COMMANDS: bool = os.getenv("ENABLE_AI_COMMANDS", "true").lower() in ("true", "1", "yes")
    DEFAULT_AI_MODEL: str = os.getenv("DEFAULT_AI_MODEL", "deepseek")
    
    # ============ BUG SYSTEM ============
    ENABLE_BUG_COMMANDS: bool = os.getenv("ENABLE_BUG_COMMANDS", "true").lower() in ("true", "1", "yes")
    BUG_ALLOWED_USERS: List[str] = [u.strip() for u in os.getenv("BUG_ALLOWED_USERS", "").split(",") if u.strip()]
    BUG_MAX_MESSAGES: int = int(os.getenv("BUG_MAX_MESSAGES", 1000))
    
    # ============ ADMIN ============
    OWNER_NUMBER: str = os.getenv("OWNER_NUMBER", "")
    ADMIN_NUMBERS: List[str] = [a.strip() for a in os.getenv("ADMIN_NUMBERS", "").split(",") if a.strip()]
    
    # ============ DEBUG ============
    DEBUG: bool = os.getenv("DEBUG", "false").lower() in ("true", "1", "yes")

    # ============ CONSTANTS ============
    SESSION_SETTINGS_CACHE_TTL: int = 5000
    MENU_SESSION_TIMEOUT: int = 60000
    COMMANDS_CACHE_TTL: int = 10000
    WARNING_DEFAULT_LIMIT: int = 3
    MEMBERS_CACHE_TTL: int = 60000
    GROUP_SETTINGS_CACHE_TTL: int = 10000

    # ============ DEFAULTS ============
    DEFAULT_SETTINGS: dict = {
        "commandPrefix": ".",
        "mode": "public",
        "footerText": "🤖 HDM Bot • Powered by WA",
        "alwaysOnline": False,
        "autoViewStatus": False,
        "antiDelete": True,
    }

    @classmethod
    def get_allowed_media_types_list(cls) -> List[str]:
        return [t.strip() for t in cls.ALLOWED_MEDIA_TYPES if t.strip()]

    @classmethod
    def is_owner(cls, number: str) -> bool:
        """Check if a number is the owner."""
        return number == cls.OWNER_NUMBER

    @classmethod
    def is_admin(cls, number: str) -> bool:
        """Check if a number is an admin (owner or in admin list)."""
        return cls.is_owner(number) or number in cls.ADMIN_NUMBERS


# Singleton instance
settings = Settings()