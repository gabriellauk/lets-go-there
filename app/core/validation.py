from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.travel_idea_group import TravelIdeaGroup
from app.models.user_account import UserAccount
from app.services.travel_idea_group import (
    get_travel_idea_group_by_id,
)


async def validate_existence_and_ownership_of_travel_idea_group(
    db_session: AsyncSession, travel_idea_group_id: int, current_user: UserAccount
) -> TravelIdeaGroup:
    travel_idea_group = await get_travel_idea_group_by_id(db_session, travel_idea_group_id)
    if travel_idea_group is None:
        raise HTTPException(status_code=404, detail="Travel idea group not found")

    if current_user != travel_idea_group.owned_by:
        raise HTTPException(status_code=403, detail="Not authorised to perform this action")

    return travel_idea_group
