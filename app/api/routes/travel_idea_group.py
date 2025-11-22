from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import get_current_user
from app.database.init_db import get_db
from app.models.user_account import UserAccount
from app.schemas.travel_idea_group import TravelIdeaGroupRead, construct_travel_idea_group
from app.services.travel_idea_group import (
    delete_travel_idea_group_and_members,
    get_travel_idea_group_by_id,
    get_travel_idea_groups,
)

router = APIRouter(prefix="/travel-idea-group", tags=["travel-idea-group"])


@router.get("/", response_model=list[TravelIdeaGroupRead])
async def get_travel_idea_groups_for_user(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[UserAccount, Depends(get_current_user)],
) -> list[TravelIdeaGroupRead]:
    travel_idea_groups_from_db = await get_travel_idea_groups(db, current_user.id)

    return [construct_travel_idea_group(travel_idea_group) for travel_idea_group in travel_idea_groups_from_db]


@router.get("/{travel_idea_group_id}", response_model=TravelIdeaGroupRead)
async def get_travel_idea_group(
    travel_idea_group_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[UserAccount, Depends(get_current_user)],
) -> TravelIdeaGroupRead:
    travel_idea_group = await get_travel_idea_group_by_id(db, travel_idea_group_id)
    if travel_idea_group is None:
        raise HTTPException(status_code=404, detail="Travel idea group not found")

    members_user_accounts = [member.user_account for member in travel_idea_group.members]

    if current_user not in members_user_accounts and current_user != travel_idea_group.owned_by:
        raise HTTPException(status_code=403, detail="Not authorised to access this travel idea group")

    return construct_travel_idea_group(travel_idea_group, members_user_accounts)


@router.delete("/{travel_idea_group_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_travel_idea_group(
    travel_idea_group_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[UserAccount, Depends(get_current_user)],
) -> None:
    travel_idea_group = await get_travel_idea_group_by_id(db, travel_idea_group_id)
    if travel_idea_group is None:
        raise HTTPException(status_code=404, detail="Travel idea group not found")

    if current_user != travel_idea_group.owned_by:
        raise HTTPException(status_code=403, detail="Not authorised to perform this action")

    await delete_travel_idea_group_and_members(db, travel_idea_group)
