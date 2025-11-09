from sqlalchemy.orm import Session

from app.models.destination import Destination
from app.schemas.destination import DestinationCreate


def create_new_destination(db: Session, request_data: DestinationCreate) -> Destination:
    destination = Destination(
        name=request_data.name,
        description=request_data.description,
        notes=request_data.notes,
        image_id=request_data.image_id,
    )
    db.add(destination)
    db.commit()
    db.refresh(destination)
    return destination
