from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.init_db import Base

from .user_account import UserAccount

if TYPE_CHECKING:
    from .travel_idea_group import TravelIdeaGroup


class TravelIdeaGroupMember(Base):
    __tablename__ = "travel_idea_group_member"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_account_id: Mapped[int] = mapped_column(ForeignKey("user_account.id"), nullable=False)
    travel_idea_group_id: Mapped[int] = mapped_column(ForeignKey("travel_idea_group.id"), nullable=False)

    user_account: Mapped[UserAccount] = relationship("UserAccount")
    travel_idea_group: Mapped["TravelIdeaGroup"] = relationship("TravelIdeaGroup")
