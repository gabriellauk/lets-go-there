from sqlalchemy.ext.asyncio import AsyncSession

from app.models import TravelIdea, TravelIdeaGroup, UserAccount
from app.schemas.travel_idea import TravelIdeaCreate


async def create_new_travel_idea(
    db: AsyncSession, request_data: TravelIdeaCreate, current_user: UserAccount
) -> TravelIdea:
    # TODO: Replace with actual travel idea group
    travel_idea_group = await db.get(TravelIdeaGroup, 1)

    travel_idea = TravelIdea(
        name=request_data.name,
        notes=request_data.notes,
        image_url=request_data.image_url,
        created_by=current_user,
        travel_idea_group=travel_idea_group,
    )
    db.add(travel_idea)

    await db.commit()
    await db.refresh(travel_idea)
    return travel_idea


async def get_travel_idea_by_id(db: AsyncSession, travel_idea_id: int) -> TravelIdea | None:
    result = await db.get(TravelIdea, travel_idea_id)
    return result
