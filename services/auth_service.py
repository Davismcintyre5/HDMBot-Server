"""
server/services/auth_service.py — Authentication service
"""
import logging
import hashlib
import secrets
from datetime import datetime, timedelta
from typing import Optional
from models.user import User
from config.settings import settings

logger = logging.getLogger(__name__)


class AuthService:
    """Service for user authentication."""

    @staticmethod
    def hash_password(password: str) -> str:
        """Hash a password with SHA-256 (use bcrypt in production)."""
        salt = settings.JWT_SECRET
        return hashlib.sha256(f"{salt}{password}".encode()).hexdigest()

    @staticmethod
    def verify_password(password: str, hash_str: str) -> bool:
        """Verify a password against its hash."""
        return AuthService.hash_password(password) == hash_str

    @staticmethod
    async def register(username: str, email: str, password: str, role: str = "admin") -> Optional[dict]:
        """Register a new user."""
        existing = await User.find_by_email(email) or await User.find_by_username(username)
        if existing:
            return None
        
        user = User(
            username=username,
            email=email,
            password_hash=AuthService.hash_password(password),
            role=role,
        )
        await user.save()
        return user.to_dict()

    @staticmethod
    async def login(email: str, password: str) -> Optional[dict]:
        """Authenticate a user and return user data with token."""
        user = await User.find_by_email(email)
        if not user or not AuthService.verify_password(password, user.password_hash):
            return None
        
        if not user.is_active:
            return None
        
        user.last_login = datetime.utcnow()
        await user.save()
        
        return {
            "user": user.to_dict(),
            "token": AuthService.generate_token(user),
        }

    @staticmethod
    def generate_token(user: User) -> str:
        """Generate a simple token (use JWT in production)."""
        import base64
        import json
        payload = {
            "user_id": user._id,
            "username": user.username,
            "email": user.email,
            "role": user.role,
            "exp": (datetime.utcnow() + timedelta(days=7)).isoformat(),
        }
        return base64.b64encode(json.dumps(payload).encode()).decode()

    @staticmethod
    async def get_user_by_id(user_id: str) -> Optional[dict]:
        from bson import ObjectId
        from config.database import users_col
        doc = await users_col().find_one({"_id": ObjectId(user_id)})
        return User.from_dict(doc).to_dict() if doc else None


auth_service = AuthService()