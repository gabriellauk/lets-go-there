from typing import Annotated

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jwt.exceptions import InvalidTokenError
from pwdlib import PasswordHash

from app import models
from app.core.config import settings
from app.database.dependencies import DBSession
from app.schemas.user import TokenData
from app.services.user_account import get_user_by_email

password_hash = PasswordHash.recommended()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/user/token")


async def get_current_user(token: Annotated[str, Depends(oauth2_scheme)], db: DBSession) -> models.UserAccount:
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
