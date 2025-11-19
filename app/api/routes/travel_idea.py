from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import get_current_user
from app.database.init_db import get_db
from app.models.user_account import UserAccount
from app.schemas.travel_idea import TravelIdeaCreate, TravelIdeaRead
from app.services.travel_idea import create_new_travel_idea, get_travel_idea_by_id

router = APIRouter(prefix="/travel-idea", tags=["travel-idea"])


@router.post("/", response_model=TravelIdeaRead)
async def create_travel_idea(
    request_data: TravelIdeaCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[UserAccount, Depends(get_current_user)],
) -> TravelIdeaRead:
    return await create_new_travel_idea(db, request_data, current_user)


@router.get("/{travel_idea_id}", response_model=TravelIdeaRead)
async def get_travel_idea(
    travel_idea_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[UserAccount, Depends(get_current_user)],
) -> TravelIdeaRead:
    travel_idea = await get_travel_idea_by_id(db, travel_idea_id)
    if travel_idea is None:
        raise HTTPException(status_code=404, detail="Travel idea not found")
    return travel_idea
