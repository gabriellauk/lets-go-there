from pydantic import field_validator

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

    @field_validator("name", "image_url", mode="after")
    @classmethod
    def reject_null(cls, v: str | None) -> str | None:
        if v is None:
            raise ValueError("If field is set, it cannot be null")
        return v


class TravelIdeaRead(TravelIdeaBase):
    id: int
