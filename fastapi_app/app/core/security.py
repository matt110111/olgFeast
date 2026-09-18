from datetime import datetime, timedelta, timezone
import hashlib
import secrets
from typing import Optional
from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerificationError
from jose import JWTError, jwt
from .config import settings

password_hasher = PasswordHasher(time_cost=2, memory_cost=19456, parallelism=1)


def verify_password(password: str, hashed: str) -> bool:
    if hashed.startswith('$argon2'):
        try:
            return password_hasher.verify(hashed, password)
        except (InvalidHashError, VerificationError):
            return False
    # Upgrade existing installations on their next successful login.
    try:
        salt, _ = hashed.split(':', 1)
        return secrets.compare_digest(hash_password(password, salt), hashed)
    except (ValueError, TypeError):
        return False


def hash_password(password: str, salt: str) -> str:
    return f'{salt}:{hashlib.sha256((password + salt).encode()).hexdigest()}'


def get_password_hash(password: str) -> str:
    return password_hasher.hash(password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    return jwt.encode({**data, 'type': 'access', 'exp': datetime.now(timezone.utc) +
        (expires_delta or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES))},
        settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def create_refresh_token(data: dict) -> str:
    return jwt.encode({**data, 'type': 'refresh', 'exp': datetime.now(timezone.utc) +
        timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)}, settings.SECRET_KEY,
        algorithm=settings.ALGORITHM)


def verify_token(token: str, token_type: str = 'access') -> Optional[dict]:
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM],
            options={'require_exp': True, 'require_sub': True})
        return payload if payload.get('type') == token_type else None
    except JWTError:
        return None


def get_user_from_token(token: str) -> Optional[dict]:
    payload = verify_token(token)
    return {'username': payload['sub'], 'user_id': payload.get('user_id')} if payload else None
