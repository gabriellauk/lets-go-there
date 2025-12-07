from sqlalchemy.ext.asyncio import AsyncSession

from app.models import TravelIdea, TravelIdeaGroup, UserAccount
from app.schemas.travel_idea import TravelIdeaCreate, TravelIdeaUpdate


async def create_new_travel_idea(
    db: AsyncSession, request_data: TravelIdeaCreate, current_user: UserAccount, travel_idea_group: TravelIdeaGroup
) -> TravelIdea:
    travel_idea = TravelIdea(
        name=request_data.name,
        notes=request_data.notes,
        image_url=request_data.image_url,
        created_by=current_user,
        travel_idea_group=travel_idea_group,
    )
    db.add(travel_idea)
    await db.commit()
    return travel_idea


async def get_travel_idea_by_id(db: AsyncSession, travel_idea_id: int) -> TravelIdea | None:
    result = await db.get(TravelIdea, travel_idea_id)
    return result


async def update_existing_travel_idea(
    db: AsyncSession, request_data: TravelIdeaUpdate, travel_idea: TravelIdea
) -> TravelIdea:
    if "name" in request_data.model_fields_set:
        travel_idea.name = request_data.name

    if "notes" in request_data.model_fields_set:
        travel_idea.notes = request_data.notes

    if "image_url" in request_data.model_fields_set:
        travel_idea.image_url = request_data.image_url

    await db.commit()
    return travel_idea


async def delete_travel_idea_from_db(db: AsyncSession, travel_idea: TravelIdea) -> None:
    await db.delete(travel_idea)
    await db.commit()
