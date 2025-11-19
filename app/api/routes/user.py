from datetime import timedelta
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.security import authenticate_user, create_access_token, get_password_hash
from app.database.init_db import get_db
from app.schemas.user import Token, UserCreate, UserRead
from app.services.user_account import create_user_account, get_user_by_email

router = APIRouter(prefix="/user", tags=["user"])


@router.post("/token")
async def login_for_access_token(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()], db: Annotated[AsyncSession, Depends(get_db)]
) -> Token:
    user = await authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=settings.access_token_expire_minutes)
    access_token = create_access_token(data={"sub": user.email}, expires_delta=access_token_expires)
    return Token(access_token=access_token, token_type="bearer")


@router.post("/register", status_code=status.HTTP_201_CREATED, response_model=UserRead)
async def create_user(user_create: UserCreate, db: Annotated[AsyncSession, Depends(get_db)]) -> UserRead:
    user = await get_user_by_email(db, user_create.email)

    if user:
        raise HTTPException(
            status_code=400,
            detail="An unexpected error occurred.",
        )

    password_hash = get_password_hash(user_create.password)
    user = await create_user_account(db, user_create.email, password_hash, user_create.name)

    return UserRead(email=user.email, name=user.name)
