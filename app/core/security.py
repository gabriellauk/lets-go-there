from datetime import UTC, datetime, timedelta
from typing import Annotated

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jwt.exceptions import InvalidTokenError
from pwdlib import PasswordHash
from sqlalchemy.ext.asyncio import AsyncSession

from app import models
from app.core.config import settings
from app.database.init_db import get_db
from app.schemas.user import TokenData
from app.services.user_account import get_user_by_email

password_hash = PasswordHash.recommended()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


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


async def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)], db: Annotated[AsyncSession, Depends(get_db)]
) -> models.UserAccount:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
        email = payload.get("sub")
        if email is None:
            raise credentials_exception
        token_data = TokenData(email=email)
    except InvalidTokenError as err:
        raise credentials_exception from err

    user = await get_user_by_email(db, token_data.email)
    if user is None:
        raise credentials_exception
    return user
