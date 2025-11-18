from sqlalchemy.ext.asyncio import AsyncSession

from app.models.travel_idea import TravelIdea
from app.models.user_account import UserAccount
from app.schemas.travel_idea import TravelIdeaCreate


async def create_new_travel_idea(db: AsyncSession, request_data: TravelIdeaCreate) -> TravelIdea:
    #  TODO: Replace with actual user
    password_hash = "$argon2id$v=19$m=65536,t=3,p=4$wagCPXjifgvUFBzq4hqe3w$CYaIb8sB+wtD+Vu/P4uod1+Qof8h+1g7bbDlBID48Rc"
    user_account = UserAccount(email="somebody@somewhere.com", password_hash=password_hash, name="Somebody")

    travel_idea = TravelIdea(
        name=request_data.name,
        notes=request_data.notes,
        image_url=request_data.image_url,
        created_by=user_account,
    )
    db.add(travel_idea)

    await db.commit()
    await db.refresh(travel_idea)
    return travel_idea


async def get_travel_idea_by_id(db: AsyncSession, travel_idea_id: int) -> TravelIdea | None:
    result = await db.get(TravelIdea, travel_idea_id)
    return result
