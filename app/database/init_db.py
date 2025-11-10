from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import declarative_base

from app.core.config import settings

engine = create_async_engine(settings.database_url)

SessionLocal = async_sessionmaker(engine, expire_on_commit=False, autoflush=False, class_=AsyncSession)

Base = declarative_base()


async def create_tables() -> None:
    # Use run_sync to run create_all synchronously in async context
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def get_db() -> AsyncGenerator[AsyncSession]:
    async with SessionLocal() as session:
        yield session
