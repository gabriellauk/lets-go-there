from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.init_db import get_db

DBSession = Annotated[AsyncSession, Depends(get_db)]
