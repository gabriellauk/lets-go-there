from fastapi import APIRouter, status

from app.core.dependencies import CurrentUser
from app.core.validation import check_user_can_access_travel_idea, check_user_can_access_travel_idea_group
from app.database.dependencies import DBSession
from app.schemas.enums import TravelIdeaGroupRole
from app.schemas.travel_idea import TravelIdeaCreate, TravelIdeaRead, TravelIdeaUpdate
from app.services.travel_idea import (
    create_new_travel_idea,
    delete_travel_idea_from_db,
    update_existing_travel_idea,
)

router = APIRouter(prefix="/travel-idea-group/{travel_idea_group_id}/travel-idea", tags=["travel-idea"])


@router.post("/", response_model=TravelIdeaRead)
async def create_travel_idea(
    travel_idea_group_id: int,
    request_data: TravelIdeaCreate,
    db: DBSession,
    current_user: CurrentUser,
) -> TravelIdeaRead:
    travel_idea_group, _, _ = await check_user_can_access_travel_idea_group(
        db, travel_idea_group_id, current_user, TravelIdeaGroupRole.MEMBER
    )
    return await create_new_travel_idea(db, request_data, current_user, travel_idea_group)


@router.get("/{travel_idea_id}", response_model=TravelIdeaRead)
async def get_travel_idea(
    travel_idea_group_id: int,
    travel_idea_id: int,
    db: DBSession,
    current_user: CurrentUser,
) -> TravelIdeaRead:
    travel_idea = await check_user_can_access_travel_idea(db, travel_idea_group_id, travel_idea_id, current_user)
    return travel_idea


@router.get("/", response_model=list[TravelIdeaRead])
async def get_travel_ideas(
    travel_idea_group_id: int,
    db: DBSession,
    current_user: CurrentUser,
) -> list[TravelIdeaRead]:
    travel_idea_group, _, _ = await check_user_can_access_travel_idea_group(
        db, travel_idea_group_id, current_user, TravelIdeaGroupRole.MEMBER, load_travel_ideas=True
    )
    return [travel_idea for travel_idea in travel_idea_group.travel_ideas]


@router.patch("/{travel_idea_id}", response_model=TravelIdeaRead)
async def update_travel_idea(
    travel_idea_group_id: int,
    travel_idea_id: int,
    request_data: TravelIdeaUpdate,
    db: DBSession,
    current_user: CurrentUser,
) -> TravelIdeaRead:
    travel_idea = await check_user_can_access_travel_idea(db, travel_idea_group_id, travel_idea_id, current_user)
    return await update_existing_travel_idea(db, request_data, travel_idea)


@router.delete("/{travel_idea_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_travel_idea(
    travel_idea_group_id: int,
    travel_idea_id: int,
    db: DBSession,
    current_user: CurrentUser,
) -> None:
    travel_idea = await check_user_can_access_travel_idea(db, travel_idea_group_id, travel_idea_id, current_user)
    await delete_travel_idea_from_db(db, travel_idea)
    return 204
