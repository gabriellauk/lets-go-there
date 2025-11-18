from fastapi import APIRouter, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import session
from app.schemas.travel_idea import TravelIdeaCreate, TravelIdeaRead
from app.services.travel_idea import create_new_travel_idea, get_travel_idea_by_id

router = APIRouter(prefix="/travel-idea", tags=["travel-idea"])


@router.post("/", response_model=TravelIdeaRead)
async def create_travel_idea(request_data: TravelIdeaCreate, db: AsyncSession = session) -> TravelIdeaRead:
    return await create_new_travel_idea(db, request_data)


@router.get("/{travel_idea_id}", response_model=TravelIdeaRead)
async def get_travel_idea(travel_idea_id: int, db: AsyncSession = session) -> TravelIdeaRead:
    travel_idea = await get_travel_idea_by_id(db, travel_idea_id)
    if travel_idea is None:
        raise HTTPException(status_code=404, detail="Travel idea not found")
    return travel_idea
