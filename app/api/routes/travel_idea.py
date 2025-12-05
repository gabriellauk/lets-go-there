from fastapi import APIRouter, HTTPException

from app.core.dependencies import CurrentUser
from app.database.dependencies import DBSession
from app.schemas.travel_idea import TravelIdeaCreate, TravelIdeaRead
from app.services.travel_idea import create_new_travel_idea, get_travel_idea_by_id

router = APIRouter(prefix="/travel-idea", tags=["travel-idea"])


@router.post("/", response_model=TravelIdeaRead)
async def create_travel_idea(
    request_data: TravelIdeaCreate,
    db: DBSession,
    current_user: CurrentUser,
) -> TravelIdeaRead:
    return await create_new_travel_idea(db, request_data, current_user)


@router.get("/{travel_idea_id}", response_model=TravelIdeaRead)
async def get_travel_idea(
    travel_idea_id: int,
    db: DBSession,
    current_user: CurrentUser,
) -> TravelIdeaRead:
    travel_idea = await get_travel_idea_by_id(db, travel_idea_id)
    if travel_idea is None:
        raise HTTPException(status_code=404, detail="Travel idea not found")
    return travel_idea
