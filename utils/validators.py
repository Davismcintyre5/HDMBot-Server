"""
server/utils/validators.py — Input validation utilities
"""
import re
from typing import Optional


def is_valid_phone(number: str) -> bool:
    """Check if a string looks like a valid phone number."""
    cleaned = re.sub(r"[^0-9]", "", number)
    return len(cleaned) >= 7 and len(cleaned) <= 15


def is_valid_email(email: str) -> bool:
    """Basic email validation."""
    pattern = r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$"
    return bool(re.match(pattern, email))


def is_valid_url(url: str) -> bool:
    """Basic URL validation."""
    pattern = r"^https?://[^\s/$.?#].[^\s]*$"
    return bool(re.match(pattern, url))


def sanitize_filename(filename: str) -> str:
    """Remove potentially dangerous characters from filenames."""
    return re.sub(r"[^a-zA-Z0-9_.-]", "_", filename)


def validate_count(value: int, min_val: int = 1, max_val: int = 1000) -> Tuple[bool, str]:
    """Validate a count/number is within range."""
    if not isinstance(value, (int, float)) or value < min_val:
        return False, f"Value must be at least {min_val}"
    if value > max_val:
        return False, f"Value must not exceed {max_val}"
    return True, ""


def validate_interval(value: float, min_val: float = 0.01, max_val: float = 60.0) -> Tuple[bool, str]:
    """Validate an interval value."""
    if not isinstance(value, (int, float)) or value < min_val:
        return False, f"Interval must be at least {min_val}s"
    if value > max_val:
        return False, f"Interval must not exceed {max_val}s"
    return True, ""