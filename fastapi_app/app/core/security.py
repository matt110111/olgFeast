from datetime import datetime, timedelta
from typing import Optional, Union
from jose import JWTError, jwt
import hashlib
import secrets
from fastapi import HTTPException, status
from .config import settings


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plain password against its hash"""
    salt, hash_part = hashed_password.split(':')
    return hash_password(plain_password, salt) == hashed_password


def get_password_hash(password: str) -> str:
    """Hash a password with a random salt"""
    salt = secrets.token_hex(16)
    return hash_password(password, salt)


def hash_password(password: str, salt: str) -> str:
    """Hash a password with a given salt"""
    return f"{salt}:{hashlib.sha256((password + salt).encode()).hexdigest()}"


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create a JWT access token"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt


def create_refresh_token(data: dict) -> str:
    """Create a JWT refresh token"""
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode.update({"exp": expire, "type": "refresh"})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt


def verify_token(token: str) -> Optional[dict]:
    """Verify and decode a JWT token"""
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        return payload
    except JWTError:
        return None


def get_user_from_token(token: str) -> Optional[dict]:
    """Extract user information from token"""
    payload = verify_token(token)
    if payload is None:
        return None
    
    username: str = payload.get("sub")
    if username is None:
        return None
    
    return {"username": username, "user_id": payload.get("user_id")}
