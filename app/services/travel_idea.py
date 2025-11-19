from sqlalchemy.ext.asyncio import AsyncSession

from app.models.travel_idea import TravelIdea
from app.models.user_account import UserAccount
from app.schemas.travel_idea import TravelIdeaCreate


async def create_new_travel_idea(
    db: AsyncSession, request_data: TravelIdeaCreate, current_user: UserAccount
) -> TravelIdea:
    travel_idea = TravelIdea(
        name=request_data.name,
        notes=request_data.notes,
        image_url=request_data.image_url,
        created_by=current_user,
    )
    db.add(travel_idea)

    await db.commit()
    await db.refresh(travel_idea)
    return travel_idea


async def get_travel_idea_by_id(db: AsyncSession, travel_idea_id: int) -> TravelIdea | None:
    result = await db.get(TravelIdea, travel_idea_id)
    return result
