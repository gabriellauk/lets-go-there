from fastapi import APIRouter
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import session
from app.schemas.destination import DestinationCreate, DestinationRead
from app.services.destination_service import create_new_destination

router = APIRouter(prefix="/destination", tags=["destination"])


@router.post("/", response_model=DestinationRead)
async def create_destination(request_data: DestinationCreate, db: AsyncSession = session) -> DestinationRead:
    return await create_new_destination(db, request_data)
