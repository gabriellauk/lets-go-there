from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from app.database.init_db import Base


class Destination(Base):
    __tablename__ = "destination"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(30), nullable=False)
    description: Mapped[str] = mapped_column(String(250))
    notes: Mapped[str | None] = mapped_column(String(750))
    image_id: Mapped[str] = mapped_column(String(255), nullable=False)
