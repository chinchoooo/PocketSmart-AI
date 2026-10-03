"""Authentication helpers: password hashing, JWT tokens, session tracking.

Tokens travel in an HttpOnly cookie (browser) or an `Authorization: Bearer`
header (API clients). Logged-out tokens are blacklisted until they expire.
"""
import logging
from datetime import datetime, timedelta, timezone
from typing import Dict, Optional

import bcrypt
from fastapi import Depends, HTTPException, Request, status
from jose import JWTError, jwt

import config
import database
from models import UserInDB, UserSession

logger = logging.getLogger("pocketsmart.auth")

active_sessions: Dict[str, UserSession] = {}
blacklisted_tokens: Dict[str, float] = {}  # token -> unix expiry (pruned by cleanup task)


# ------------------------------- passwords ------------------------------------
def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8")[:72], bcrypt.gensalt()).decode("utf-8")


def verify_password(password: str, hashed: str) -> bool:
    try:
        return bcrypt.checkpw(password.encode("utf-8")[:72], hashed.encode("utf-8"))
    except ValueError:
        return False


def authenticate_user(username: str, password: str) -> Optional[UserInDB]:
    record = database.get_user(username)
    if record and verify_password(password, record["hashed_password"]):
        return UserInDB(**record)
    return None


# --------------------------------- tokens -------------------------------------
def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    expire = datetime.now(timezone.utc) + (expires_delta or timedelta(minutes=config.ACCESS_TOKEN_EXPIRE_MINUTES))
    return jwt.encode({**data, "exp": expire}, config.SECRET_KEY, algorithm=config.ALGORITHM)


def get_token(request: Request) -> Optional[str]:
    """Read the JWT from the cookie first, then the Authorization header."""
    token = request.cookies.get("access_token")
    if token:
        return token
    header = request.headers.get("Authorization", "")
    if header.lower().startswith("bearer "):
        return header[7:].strip()
    return None


def blacklist_token(token: str) -> None:
    try:
        payload = jwt.decode(token, config.SECRET_KEY, algorithms=[config.ALGORITHM])
        blacklisted_tokens[token] = float(payload.get("exp", 0))
    except JWTError:
        blacklisted_tokens[token] = 0.0


def get_current_user(token: Optional[str]) -> UserInDB:
    """Resolve a JWT to a user or raise 401."""
    unauthorized = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Not authenticated",
        headers={"WWW-Authenticate": "Bearer"},
    )
    if not token or token in blacklisted_tokens:
        raise unauthorized
    try:
        payload = jwt.decode(token, config.SECRET_KEY, algorithms=[config.ALGORITHM])
    except JWTError:
        raise unauthorized
    record = database.get_user(payload.get("sub", ""))
    if not record:
        raise unauthorized
    return UserInDB(**record)


# ----------------------------- sessions / deps --------------------------------
def start_session(username: str, token: str) -> None:
    """Create a fresh session, invalidating the user's previous token."""
    previous = active_sessions.get(username)
    if previous:
        blacklist_token(previous.token)
    now = datetime.now(timezone.utc)
    carried = previous.user_data if previous else {}
    active_sessions[username] = UserSession(username, now, now, token, carried)


def get_current_active_user(request: Request) -> UserInDB:
    """FastAPI dependency for every protected route."""
    token = get_token(request)
    user = get_current_user(token)
    session = active_sessions.get(user.username)
    if session is None:  # e.g. cleaned up while idle, or server restarted
        start_session(user.username, token)
        session = active_sessions[user.username]
    session.last_activity = datetime.now(timezone.utc)
    return user


def get_optional_user(request: Request) -> Optional[UserInDB]:
    """Like the dependency above, but returns None instead of raising."""
    try:
        return get_current_active_user(request)
    except HTTPException:
        return None


def cleanup_expired() -> None:
    """Drop idle sessions and expired blacklist entries (called periodically)."""
    now = datetime.now(timezone.utc)
    for name in [n for n, s in active_sessions.items()
                 if (now - s.last_activity).total_seconds() > config.SESSION_IDLE_SECONDS]:
        logger.info("Removing expired session for %s", name)
        del active_sessions[name]
    cutoff = now.timestamp()
    for tok in [t for t, exp in blacklisted_tokens.items() if exp < cutoff]:
        del blacklisted_tokens[tok]
