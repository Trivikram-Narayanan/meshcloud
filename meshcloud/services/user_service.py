"""
User Service — business logic for user registration and authentication.
Extracted from control_plane/api_server.py.
"""
from typing import Optional

from fastapi import HTTPException

from meshcloud.security.auth import create_access_token, Token
from meshcloud.security.dependencies import get_password_hash, verify_password
from meshcloud.storage.database import get_user_by_username, create_user


def register(
    username: str,
    password: str,
    full_name: Optional[str] = None,
    email: Optional[str] = None,
):
    """Register a new user and return the DB user object."""
    existing = get_user_by_username(username)
    if existing:
        raise HTTPException(status_code=400, detail="Username already registered")

    hashed_password = get_password_hash(password)
    new_user = create_user(
        username=username,
        hashed_password=hashed_password,
        full_name=full_name,
        email=email,
    )
    return new_user


def login(username: str, password: str) -> Token:
    """Authenticate a user and return a JWT Token."""
    user = get_user_by_username(username)
    if not user or not verify_password(password, user.hashed_password):
        raise HTTPException(
            status_code=401,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token = create_access_token(data={"sub": user.username})
    return Token(access_token=access_token, token_type="bearer")
