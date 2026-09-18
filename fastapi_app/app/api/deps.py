from datetime import datetime, timezone
from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from ..core.database import get_db
from ..core.security import verify_token
from ..models.user import User, AuthSession

security = HTTPBearer(auto_error=False)


def user_for_token(token: str, db: Session):
    payload = verify_token(token)
    if not payload:
        return None
    session = db.get(AuthSession, payload.get('sid', ''))
    if not session or session.revoked:
        return None
    expires = session.expires_at.replace(tzinfo=timezone.utc)
    if expires <= datetime.now(timezone.utc):
        return None
    user = db.get(User, session.user_id)
    return user if user and user.is_active and user.username == payload['sub'] else None


def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security),
                     db: Session = Depends(get_db)) -> User:
    user = user_for_token(credentials.credentials, db) if credentials else None
    if not user:
        raise HTTPException(401, 'Please sign in again', headers={'WWW-Authenticate': 'Bearer'})
    return user


def get_current_staff_user(user: User = Depends(get_current_user)) -> User:
    if not user.is_staff:
        raise HTTPException(403, 'Staff access required')
    return user


get_current_active_user = get_current_user


async def get_current_user_websocket(token: str, db: Session):
    return user_for_token(token, db)


def get_current_admin_user(user: User = Depends(get_current_staff_user)) -> User:
    if not user.is_admin:
        raise HTTPException(403, 'Organizer access required')
    return user
