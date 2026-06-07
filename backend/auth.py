"""
Simple in-memory auth: signup, login, session management.
"""
import hashlib
import secrets
from typing import Optional

# In-memory stores
_users: dict[str, dict] = {}
_sessions: dict[str, str] = {}   # token → username

# Seed a default admin account
_hashed_default = hashlib.sha256("admin123".encode()).hexdigest()
_users["admin"] = {"username": "admin", "password": _hashed_default, "role": "admin"}


def _hash(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()


def signup(username: str, password: str) -> dict:
    if username in _users:
        return {"success": False, "message": "Username already exists."}
    if len(password) < 6:
        return {"success": False, "message": "Password must be at least 6 characters."}
    _users[username] = {"username": username, "password": _hash(password), "role": "user"}
    return {"success": True, "message": "Account created successfully."}


def login(username: str, password: str) -> dict:
    user = _users.get(username)
    if not user or user["password"] != _hash(password):
        return {"success": False, "message": "Invalid credentials."}
    token = secrets.token_hex(32)
    _sessions[token] = username
    return {"success": True, "token": token, "username": username, "role": user["role"]}


def logout(token: str) -> None:
    _sessions.pop(token, None)


def get_user_from_token(token: Optional[str]) -> Optional[dict]:
    if not token:
        return None
    username = _sessions.get(token)
    if not username:
        return None
    return _users.get(username)
