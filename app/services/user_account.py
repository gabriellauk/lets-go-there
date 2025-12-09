from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user_account import UserAccount


async def get_user_by_email(db: AsyncSession, email: str) -> UserAccount | None:
    stmt = select(UserAccount).where(UserAccount.email == email)
    result = await db.execute(stmt)
    user = result.scalars().first()
    return user


async def create_user_account(db: AsyncSession, email: str, name: str) -> UserAccount:
    user_account = UserAccount(email=email, name=name)
    db.add(user_account)
    await db.commit()
    await db.refresh(user_account)
    return user_account
