from app.schemas.shared import BaseSchema


class DestinationBase(BaseSchema):
    name: str
    description: str | None = None
    notes: str | None = None
    image_id: str


class DestinationCreate(DestinationBase):
    pass


class DestinationUpdate(DestinationBase):
    name: str | None = None
    image_id: str | None = None


class DestinationRead(DestinationBase):
    id: int
