from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user_account import UserAccount


async def get_user_by_email(db: AsyncSession, email: str) -> UserAccount | None:
    stmt = select(UserAccount).where(UserAccount.email == email)
    result = await db.execute(stmt)
    user = result.scalars().first()
    return user
