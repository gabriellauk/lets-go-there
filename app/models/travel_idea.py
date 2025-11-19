from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.init_db import Base

from .travel_idea_group import TravelIdeaGroup
from .user_account import UserAccount


class TravelIdea(Base):
    __tablename__ = "travel_idea"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(50), nullable=False)
    notes: Mapped[str | None] = mapped_column(String(750))
    image_url: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    created_by_id: Mapped[int] = mapped_column(ForeignKey("user_account.id"), nullable=False)
    travel_idea_group_id: Mapped[int] = mapped_column(ForeignKey("travel_idea_group.id"), nullable=False)

    created_by: Mapped[UserAccount] = relationship("UserAccount")
    travel_idea_group: Mapped[TravelIdeaGroup] = relationship("TravelIdeaGroup")
