from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

from app.database.init_db import Base


class TravelIdeaGroupMember(Base):
    __tablename__ = "travel_idea_group_member"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_account_id: Mapped[int] = mapped_column(ForeignKey("user_account.id"), nullable=False)
    travel_idea_group_id: Mapped[int] = mapped_column(ForeignKey("travel_idea_group.id"), nullable=False)
