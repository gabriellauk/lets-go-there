from fastapi import APIRouter, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import session
from app.schemas.destination import DestinationCreate, DestinationRead
from app.services.destination import create_new_destination, get_destination_by_id

router = APIRouter(prefix="/destination", tags=["destination"])


@router.post("/", response_model=DestinationRead)
async def create_destination(request_data: DestinationCreate, db: AsyncSession = session) -> DestinationRead:
    return await create_new_destination(db, request_data)


@router.get("/{destination_id}", response_model=DestinationRead)
async def get_destination(destination_id: int, db: AsyncSession = session) -> DestinationRead:
    destination = await get_destination_by_id(db, destination_id)
    if destination is None:
        raise HTTPException(status_code=404, detail="Destination not found")
    return destination
