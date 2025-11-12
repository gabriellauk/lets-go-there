from sqlalchemy.ext.asyncio import AsyncSession

from app.models.destination import Destination
from app.schemas.destination import DestinationCreate


async def create_new_destination(db: AsyncSession, request_data: DestinationCreate) -> Destination:
    destination = Destination(
        name=request_data.name,
        description=request_data.description,
        notes=request_data.notes,
        image_id=request_data.image_id,
    )
    db.add(destination)
    await db.commit()
    await db.refresh(destination)
    return destination


async def get_destination_by_id(db: AsyncSession, destination_id: int) -> Destination | None:
    result = await db.get(Destination, destination_id)
    return result
