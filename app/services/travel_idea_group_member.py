from sqlalchemy.ext.asyncio import AsyncSession

from app.models import TravelIdeaGroup, TravelIdeaGroupMember, UserAccount


async def create_new_travel_idea_group_member(
    db: AsyncSession, travel_idea_group: TravelIdeaGroup, user_account: UserAccount
) -> TravelIdeaGroupMember:
    travel_idea_group_member = TravelIdeaGroupMember(travel_idea_group=travel_idea_group, user_account=user_account)
    db.add(travel_idea_group_member)
    return travel_idea_group_member
