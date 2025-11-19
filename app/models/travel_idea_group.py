from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.init_db import Base
from app.models.user_account import UserAccount


class TravelIdeaGroup(Base):
    __tablename__ = "travel_idea_group"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(50), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    owned_by_id: Mapped[int] = mapped_column(ForeignKey("user_account.id"), nullable=False)

    owned_by: Mapped[UserAccount] = relationship("UserAccount")
