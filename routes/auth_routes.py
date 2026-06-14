"""
server/routes/auth_routes.py — Authentication API routes
"""
import hashlib
import jwt
from datetime import datetime, timedelta
from functools import wraps
from flask import Blueprint, request, jsonify

bp = Blueprint("auth", __name__, url_prefix="/api/auth")

JWT_SECRET = None
JWT_EXPIRE_HOURS = 168


def init_auth(secret: str, expire: str = "7d"):
    global JWT_SECRET, JWT_EXPIRE_HOURS
    JWT_SECRET = secret
    if "d" in expire:
        JWT_EXPIRE_HOURS = int(expire.replace("d", "")) * 24
    else:
        JWT_EXPIRE_HOURS = int(expire.replace("h", ""))


def _get_db():
    from config.database import get_db as db_get
    return db_get()


def _hash_password(password: str) -> str:
    salt = JWT_SECRET or "hdm_bot_secret"
    return hashlib.sha256(f"{salt}{password}".encode()).hexdigest()


def _create_token(user: dict) -> str:
    payload = {
        "sub": str(user.get("_id", "")),
        "email": user.get("email", ""),
        "username": user.get("username", ""),
        "role": user.get("role", ""),
        "iat": datetime.utcnow(),
        "exp": datetime.utcnow() + timedelta(hours=JWT_EXPIRE_HOURS),
    }
    return jwt.encode(payload, JWT_SECRET, algorithm="HS256")


def _decode_token(token: str) -> dict | None:
    try:
        return jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
    except (jwt.ExpiredSignatureError, jwt.InvalidTokenError):
        return None


def require_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth = request.headers.get("Authorization", "")
        if not auth.startswith("Bearer "):
            return jsonify({"error": "Missing or invalid token"}), 401
        payload = _decode_token(auth[7:])
        if payload is None:
            return jsonify({"error": "Token expired or invalid"}), 401
        request.user = payload
        return f(*args, **kwargs)
    return decorated


def require_role(*roles: str):
    def decorator(f):
        @wraps(f)
        @require_auth
        def decorated(*args, **kwargs):
            if request.user.get("role") not in roles:
                return jsonify({"error": "Insufficient permissions"}), 403
            return f(*args, **kwargs)
        return decorated
    return decorator


@bp.post("/login")
def login():
    data = request.get_json(force=True, silent=True) or {}
    email = data.get("email", "").strip()
    password = data.get("password", "")
    if not email or not password:
        return jsonify({"error": "Email and password are required"}), 400
    db = _get_db()
    if db is None:
        return jsonify({"error": "Database not connected"}), 500
    user = db["users"].find_one({"email": email})
    if user is None or not user.get("is_active", True):
        return jsonify({"error": "Invalid email or password"}), 401
    if _hash_password(password) != user.get("password_hash", ""):
        return jsonify({"error": "Invalid email or password"}), 401
    db["users"].update_one({"_id": user["_id"]}, {"$set": {"last_login": datetime.utcnow()}})
    token = _create_token(user)
    return jsonify({
        "ok": True, "token": token, "expires_in": f"{JWT_EXPIRE_HOURS}h",
        "user": {"id": str(user["_id"]), "email": user["email"], "username": user["username"], "role": user["role"]}
    })


@bp.post("/register")
def register():
    data = request.get_json(force=True, silent=True) or {}
    email = data.get("email", "").strip()
    username = data.get("username", "").strip()
    password = data.get("password", "")
    role = data.get("role", "viewer")
    if not email or not username or not password:
        return jsonify({"error": "Email, username, and password are required"}), 400
    if len(password) < 6:
        return jsonify({"error": "Password must be at least 6 characters"}), 400
    db = _get_db()
    if db is None:
        return jsonify({"error": "Database not connected"}), 500
    if db["users"].find_one({"$or": [{"email": email}, {"username": username}]}):
        return jsonify({"error": "Email or username already exists"}), 409
    if role not in ("owner", "super_admin", "admin", "viewer"):
        role = "viewer"
    doc = {"email": email, "username": username, "password_hash": _hash_password(password), "role": role,
           "phone_number": "", "is_active": True, "permissions": [], "created_at": datetime.utcnow(),
           "updated_at": datetime.utcnow(), "last_login": None}
    result = db["users"].insert_one(doc)
    user = db["users"].find_one({"_id": result.inserted_id})
    return jsonify({"ok": True, "message": "Registration successful",
        "user": {"id": str(user["_id"]), "email": user["email"], "username": user["username"], "role": user["role"]}}), 201


@bp.get("/me")
@require_auth
def me():
    db = _get_db()
    if db is None:
        return jsonify({"error": "Database not connected"}), 500
    user = db["users"].find_one({"email": request.user["email"]})
    if user is None:
        return jsonify({"error": "User not found"}), 404
    return jsonify({"ok": True, "user": {
        "id": str(user["_id"]), "email": user["email"], "username": user["username"],
        "role": user["role"], "phone_number": user.get("phone_number", ""),
        "is_active": user.get("is_active", True), "created_at": str(user.get("created_at", "")),
        "last_login": str(user.get("last_login", ""))
    }})


@bp.post("/change-password")
@require_auth
def change_password():
    data = request.get_json(force=True, silent=True) or {}
    cp = data.get("current_password", "")
    np = data.get("new_password", "")
    if not cp or not np:
        return jsonify({"error": "Current and new password are required"}), 400
    if len(np) < 6:
        return jsonify({"error": "New password must be at least 6 characters"}), 400
    db = _get_db()
    if db is None:
        return jsonify({"error": "Database not connected"}), 500
    user = db["users"].find_one({"email": request.user["email"]})
    if user is None:
        return jsonify({"error": "User not found"}), 404
    if _hash_password(cp) != user.get("password_hash", ""):
        return jsonify({"error": "Current password is incorrect"}), 401
    db["users"].update_one({"_id": user["_id"]}, {"$set": {"password_hash": _hash_password(np), "updated_at": datetime.utcnow()}})
    return jsonify({"ok": True, "message": "Password changed successfully"})


@bp.post("/reset-password")
@require_role("owner", "super_admin", "admin")
def reset_password():
    data = request.get_json(force=True, silent=True) or {}
    email = data.get("email", "").strip()
    np = data.get("new_password", "")
    if not email or not np:
        return jsonify({"error": "Email and new password are required"}), 400
    if len(np) < 6:
        return jsonify({"error": "New password must be at least 6 characters"}), 400
    db = _get_db()
    if db is None:
        return jsonify({"error": "Database not connected"}), 500
    target = db["users"].find_one({"email": email})
    if target is None:
        return jsonify({"error": "User not found"}), 404
    if request.user.get("role") not in ("owner", "super_admin"):
        if target.get("role") in ("owner", "super_admin"):
            return jsonify({"error": "Cannot reset password for higher role"}), 403
    db["users"].update_one({"_id": target["_id"]}, {"$set": {"password_hash": _hash_password(np), "updated_at": datetime.utcnow()}})
    return jsonify({"ok": True, "message": f"Password reset for {email}"})


@bp.get("/users")
@require_role("owner", "super_admin", "admin")
def list_users():
    db = _get_db()
    if db is None:
        return jsonify({"error": "Database not connected"}), 500
    users = list(db["users"].find({}, {"password_hash": 0}))
    result = [{"id": str(u["_id"]), "email": u.get("email",""), "username": u.get("username",""),
               "role": u.get("role",""), "is_active": u.get("is_active",True),
               "last_login": str(u.get("last_login","")), "created_at": str(u.get("created_at",""))} for u in users]
    return jsonify({"ok": True, "users": result, "total": len(result)})


@bp.put("/users/<user_id>")
@require_role("owner", "super_admin")
def update_user(user_id: str):
    data = request.get_json(force=True, silent=True) or {}
    db = _get_db()
    if db is None:
        return jsonify({"error": "Database not connected"}), 500
    from bson import ObjectId
    try:
        oid = ObjectId(user_id)
    except Exception:
        return jsonify({"error": "Invalid user ID"}), 400
    user = db["users"].find_one({"_id": oid})
    if user is None:
        return jsonify({"error": "User not found"}), 404
    update = {}
    if "role" in data and data["role"] in ("admin","viewer"): update["role"] = data["role"]
    if "is_active" in data: update["is_active"] = bool(data["is_active"])
    if "username" in data: update["username"] = data["username"]
    if "phone_number" in data: update["phone_number"] = data["phone_number"]
    if update:
        update["updated_at"] = datetime.utcnow()
        db["users"].update_one({"_id": oid}, {"$set": update})
    u = db["users"].find_one({"_id": oid})
    return jsonify({"ok": True, "user": {"id": str(u["_id"]), "email": u.get("email",""),
        "username": u.get("username",""), "role": u.get("role",""), "is_active": u.get("is_active",True)}})


@bp.delete("/users/<user_id>")
@require_role("owner")
def delete_user(user_id: str):
    db = _get_db()
    if db is None:
        return jsonify({"error": "Database not connected"}), 500
    from bson import ObjectId
    try:
        oid = ObjectId(user_id)
    except Exception:
        return jsonify({"error": "Invalid user ID"}), 400
    user = db["users"].find_one({"_id": oid})
    if user is None:
        return jsonify({"error": "User not found"}), 404
    if user.get("role") == "owner":
        return jsonify({"error": "Cannot delete owner"}), 403
    db["users"].delete_one({"_id": oid})
    return jsonify({"ok": True, "message": "User deleted"})