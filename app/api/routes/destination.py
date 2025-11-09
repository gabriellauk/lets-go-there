from fastapi import APIRouter
from sqlalchemy.orm import Session

from app.api.dependencies import session
from app.schemas.destination import DestinationCreate, DestinationRead
from app.services.destination_service import create_new_destination

router = APIRouter(prefix="/destination", tags=["destination"])


@router.post("/", response_model=DestinationRead)
def create_destination(request_data: DestinationCreate, db: Session = session) -> DestinationRead:
    return create_new_destination(db, request_data)
