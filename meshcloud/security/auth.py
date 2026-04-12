"""Authentication and authorization utilities for MeshCloud."""
import os
import re
import secrets
from datetime import datetime, timedelta, timezone
from typing import Optional

import jwt
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from loguru import logger
from pydantic import BaseModel

# JWT Configuration
# WARNING: If JWT_SECRET_KEY is not set, a random key is generated at startup.
# This means all tokens are invalidated on every restart. Set this env var to a
# stable, secret value (e.g. `openssl rand -hex 32`) for any persistent deployment.
_jwt_env = os.getenv("JWT_SECRET_KEY")
if not _jwt_env:
    logger.warning(
        "JWT_SECRET_KEY is not set. A temporary key has been generated — all "
        "sessions will be lost on restart. Set JWT_SECRET_KEY for production use."
    )
JWT_SECRET_KEY = _jwt_env or secrets.token_hex(32)
JWT_ALGORITHM = "HS256"
JWT_ACCESS_TOKEN_EXPIRE_MINUTES = int(
    os.getenv("JWT_ACCESS_TOKEN_EXPIRE_MINUTES", "30")
)

_ph = PasswordHasher()

# Security schemes
security = HTTPBearer()


class Token(BaseModel):
    """JWT token response model."""

    access_token: str
    token_type: str


class TokenData(BaseModel):
    """JWT token payload data."""

    username: Optional[str] = None


class User(BaseModel):
    """User model for authentication."""

    username: str
    email: Optional[str] = None
    full_name: Optional[str] = None
    disabled: Optional[bool] = None


class UserInDB(User):
    """User model with hashed password."""

    hashed_password: str


# Demo user database — replace with a real persistent store before production.
# The default admin password is read from ADMIN_PASSWORD env var (default: "admin").
# Do NOT ship with the "admin"/"admin" default in production.
_admin_password = os.getenv("ADMIN_PASSWORD", "admin")
if _admin_password == "admin":
    logger.warning(
        "ADMIN_PASSWORD is using the insecure default 'admin'. "
        "Set the ADMIN_PASSWORD environment variable for production deployments."
    )
fake_users_db = {
    "admin": {
        "username": "admin",
        "full_name": "Administrator",
        "email": "admin@meshcloud.local",
        "hashed_password": _ph.hash(_admin_password),
        "disabled": False,
    }
}


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its Argon2 hash."""
    try:
        return _ph.verify(hashed_password, plain_password)
    except VerifyMismatchError:
        return False


def get_password_hash(password: str) -> str:
    """Hash a password with Argon2."""
    return _ph.hash(password)


def get_user(db, username: str) -> Optional[UserInDB]:
    """Get user from database."""
    if username in db:
        user_dict = db[username]
        return UserInDB(**user_dict)
    return None


def authenticate_user(fake_db, username: str, password: str) -> Optional[User]:
    """Authenticate a user."""
    user = get_user(fake_db, username)
    if not user:
        return None
    if not verify_password(password, user.hashed_password):
        return None
    return user


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """Create a JWT access token."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)
    return encoded_jwt


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
):
    """Get current authenticated user from JWT token."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(
            credentials.credentials, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM]
        )
        username: Optional[str] = payload.get("sub")
        if username is None:
            raise credentials_exception
        token_data = TokenData(username=username)
    except jwt.PyJWTError as err:
        raise credentials_exception from err

    user = get_user(fake_users_db, username=token_data.username or "")
    if user is None:
        raise credentials_exception
    return user


async def get_current_active_user(current_user: User = Depends(get_current_user)):
    """Get current active user."""
    if current_user.disabled:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user


def require_node_token(x_meshcloud_token: Optional[str] = None) -> bool:
    """Validate node-to-node authentication token."""
    expected_token = os.getenv("MESH_NODE_TOKEN", "")
    if not expected_token:
        logger.warning(
            "MESH_NODE_TOKEN is not set. Node-to-node requests are unauthenticated. "
            "Set MESH_NODE_TOKEN to a strong secret shared across all nodes."
        )
    if not x_meshcloud_token:
        return False
    return x_meshcloud_token == expected_token


def validate_file_size(file_size: int, max_size: int = 100 * 1024 * 1024) -> bool:
    """Validate file size is within limits (default 100MB)."""
    return file_size <= max_size


def sanitize_filename(filename: str) -> str:
    """Sanitize filename to prevent path traversal attacks."""
    filename = re.sub(r'[<>:"/\\|?*]', "", filename)
    filename = filename.strip()
    if len(filename) > 255:
        filename = filename[:255]
    return filename
