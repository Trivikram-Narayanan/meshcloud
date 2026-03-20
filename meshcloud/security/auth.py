"""Authentication and authorization utilities for MeshCloud."""
import hashlib
import os
import secrets
from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
import jwt
from pydantic import BaseModel

# JWT Configuration
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", secrets.token_hex(32))
JWT_ALGORITHM = "HS256"
JWT_ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("JWT_ACCESS_TOKEN_EXPIRE_MINUTES", "30"))

# Password hashing - using simple hash for demo (use bcrypt in production)

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


# Mock user database - In production, use a real database
fake_users_db = {
    "admin": {
        "username": "admin",
        "full_name": "Administrator",
        "email": "admin@meshcloud.local",
        "hashed_password": hashlib.sha256("admin".encode()).hexdigest(),  # Simple hash for demo
        "disabled": False,
    }
}


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash."""
    return hashlib.sha256(plain_password.encode()).hexdigest() == hashed_password


def get_password_hash(password: str) -> str:
    """Hash a password."""
    return hashlib.sha256(password.encode()).hexdigest()


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


async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Get current authenticated user from JWT token."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(credentials.credentials, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        token_data = TokenData(username=username)
    except jwt.PyJWTError:
        raise credentials_exception

    user = get_user(fake_users_db, username=token_data.username)
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
    expected_token = os.getenv("MESH_NODE_TOKEN", "meshcloud_secret_token")
    if not x_meshcloud_token:
        return False
    return x_meshcloud_token == expected_token


def validate_file_size(file_size: int, max_size: int = 100 * 1024 * 1024) -> bool:
    """Validate file size is within limits (default 100MB)."""
    return file_size <= max_size


def sanitize_filename(filename: str) -> str:
    """Sanitize filename to prevent path traversal attacks."""
    # Remove any path separators and dangerous characters
    import re

    filename = re.sub(r'[<>:"/\\|?*]', "", filename)
    filename = filename.strip()
    # Limit filename length
    if len(filename) > 255:
        filename = filename[:255]
    return filename
