from datetime import datetime, timedelta, timezone
import secrets
from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm, HTTPAuthorizationCredentials
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from ...core.database import get_db
from ...core.security import verify_password, get_password_hash, create_access_token, create_refresh_token, verify_token
from ...core.config import settings
from ...models.user import User, Profile, AuthSession
from ...schemas.user import UserCreate, Token, User as UserSchema
from ...api.deps import get_current_user, security

router = APIRouter()


def tokens(user, session):
    claims = {'sub': user.username, 'user_id': user.id, 'sid': session.id}
    return {'access_token': create_access_token(claims), 'refresh_token': create_refresh_token(
        {**claims, 'jti': session.refresh_id}), 'token_type': 'bearer'}


@router.post('/register', response_model=UserSchema)
def register(data: UserCreate, db: Session = Depends(get_db)):
    if db.query(User).filter((User.username == data.username) | (User.email == data.email)).first():
        raise HTTPException(400, 'Username or email already registered')
    user = User(username=data.username, email=data.email,
                hashed_password=get_password_hash(data.password), is_active=True)
    db.add(user)
    db.flush()
    db.add(Profile(user_id=user.id))
    db.commit()
    db.refresh(user)
    return user


@router.post('/login', response_model=Token)
def login(form: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == form.username).first()
    if not user or not verify_password(form.password, user.hashed_password):
        raise HTTPException(401, 'Incorrect username or password', headers={'WWW-Authenticate': 'Bearer'})
    if not user.is_active:
        raise HTTPException(403, 'Account disabled')
    if not user.hashed_password.startswith('$argon2'):
        user.hashed_password = get_password_hash(form.password)
    session = AuthSession(id=secrets.token_hex(24), user_id=user.id,
        refresh_id=secrets.token_hex(24), revoked=False,
        expires_at=datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS))
    db.add(session)
    db.commit()
    return tokens(user, session)


class RefreshRequest(BaseModel):
    refresh_token: str


@router.post('/refresh', response_model=Token)
def refresh(data: RefreshRequest, db: Session = Depends(get_db)):
    payload = verify_token(data.refresh_token, 'refresh')
    if not payload:
        raise HTTPException(401, 'Session expired')
    session = db.query(AuthSession).filter(AuthSession.id == payload.get('sid')).with_for_update().first()
    if not session or session.revoked or session.refresh_id != payload.get('jti'):
        raise HTTPException(401, 'Session expired')
    user = db.get(User, session.user_id)
    if not user or not user.is_active or session.expires_at.replace(tzinfo=timezone.utc) <= datetime.now(timezone.utc):
        raise HTTPException(401, 'Session expired')
    session.refresh_id = secrets.token_hex(24)
    db.commit()
    return tokens(user, session)


@router.get('/me', response_model=UserSchema)
def me(user: User = Depends(get_current_user)):
    return user


@router.post('/logout')
def logout(user: User = Depends(get_current_user), credentials: HTTPAuthorizationCredentials = Depends(security), db: Session = Depends(get_db)):
    payload = verify_token(credentials.credentials)
    session = db.get(AuthSession, payload['sid'])
    session.revoked = True
    db.commit()
    return {'message': 'Signed out'}


class PasswordChange(BaseModel):
    current_password: str
    new_password: str = Field(min_length=10, max_length=128)


@router.post('/password')
def change_password(data: PasswordChange, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if not verify_password(data.current_password, user.hashed_password):
        raise HTTPException(400, 'Current password is incorrect')
    user.hashed_password = get_password_hash(data.new_password)
    db.query(AuthSession).filter(AuthSession.user_id == user.id).update({'revoked': True})
    db.commit()
    return {'message': 'Password updated. Please sign in again.'}


class VolunteerInput(BaseModel):
    username: str = Field(min_length=3, max_length=40, pattern='^[a-zA-Z0-9_.-]+$')
    password: str = Field(min_length=10, max_length=128)


@router.post('/guest-stations', response_model=UserSchema)
def create_guest_station(data: VolunteerInput, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return create_station(data, db, user, staff=False)


@router.post('/volunteers', response_model=UserSchema)
def create_volunteer(data: VolunteerInput, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return create_station(data, db, user, staff=True)


def create_station(data, db, user, staff):
    if not user.is_admin:
        raise HTTPException(403, 'Organizer access required')
    if db.query(User).filter_by(username=data.username).first():
        raise HTTPException(409, 'Username already exists')
    volunteer = User(username=data.username, email=f'{data.username}@volunteers.example.org',
        hashed_password=get_password_hash(data.password), is_active=True, is_staff=staff)
    db.add(volunteer)
    db.commit()
    db.refresh(volunteer)
    return volunteer
