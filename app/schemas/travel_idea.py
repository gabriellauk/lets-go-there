from app.schemas.shared import BaseSchema


class TravelIdeaBase(BaseSchema):
    name: str
    notes: str | None = None
    image_url: str


class TravelIdeaCreate(TravelIdeaBase):
    pass


class TravelIdeaUpdate(TravelIdeaBase):
    name: str | None = None
    image_url: str | None = None


class TravelIdeaRead(TravelIdeaBase):
    id: int
