from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.travel_idea import TravelIdea
from app.models.travel_idea_group import TravelIdeaGroup
from app.models.user_account import UserAccount
from app.schemas.enums import TravelIdeaGroupRole
from app.services.travel_idea import get_travel_idea_by_id
from app.services.travel_idea_group import (
    get_travel_idea_group_by_id,
)


async def check_user_can_access_travel_idea_group(
    db_session: AsyncSession,
    travel_idea_group_id: int,
    user: UserAccount,
    required_access_level: TravelIdeaGroupRole,
    load_travel_ideas: bool = False,
) -> tuple[TravelIdeaGroup, list[UserAccount], UserAccount]:
    travel_idea_group = await get_travel_idea_group_by_id(db_session, travel_idea_group_id, load_travel_ideas)
    if travel_idea_group is None:
        raise HTTPException(status_code=404, detail="Travel idea group not found")

    members = [member.user_account for member in travel_idea_group.members]
    owner = travel_idea_group.owned_by

    if required_access_level == TravelIdeaGroupRole.OWNER and user != owner:
        raise HTTPException(status_code=403, detail="Not authorised to perform this action")

    if required_access_level == TravelIdeaGroupRole.MEMBER and user not in members and user != owner:
        raise HTTPException(status_code=403, detail="Not authorised to access this travel idea group")

    return travel_idea_group, members, owner


async def check_user_can_access_travel_idea(
    db_session: AsyncSession,
    travel_idea_group_id: int,
    travel_idea_id: int,
    user: UserAccount,
) -> TravelIdea:
    await check_user_can_access_travel_idea_group(db_session, travel_idea_group_id, user, TravelIdeaGroupRole.MEMBER)

    travel_idea = await get_travel_idea_by_id(db_session, travel_idea_id)
    if travel_idea is None:
        raise HTTPException(status_code=404, detail="Travel idea not found")

    return travel_idea
