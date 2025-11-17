from datetime import UTC, datetime, timedelta

import jwt
from pwdlib import PasswordHash
from sqlalchemy.ext.asyncio import AsyncSession

from app import models
from app.core.config import settings
from app.services.user_account import get_user_by_email

password_hash = PasswordHash.recommended()


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return password_hash.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    return password_hash.hash(password)


async def authenticate_user(db: AsyncSession, email: str, password: str) -> models.UserAccount | bool:
    user = await get_user_by_email(db, email)
    if not user:
        return False
    if not verify_password(password, user.password_hash):
        return False
    return user


def create_access_token(data: dict, expires_delta: timedelta | None = None) -> str:
    to_encode = data.copy()
    expire = (
        datetime.now(UTC) + expires_delta if expires_delta else datetime.now(UTC) + settings.access_token_expire_minutes
    )
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.secret_key, algorithm=settings.algorithm)
    return encoded_jwt
