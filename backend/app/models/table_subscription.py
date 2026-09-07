"""table_subscription：用户与表的订阅/收藏关系。"""

from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin


class TableSubscription(Base, TimestampMixin):
    __tablename__ = "table_subscription"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("sys_user.id"), nullable=False)
    table_id: Mapped[int] = mapped_column(
        ForeignKey("table_meta.id"), index=True, nullable=False
    )
    relation: Mapped[str] = mapped_column(
        String(16), nullable=False, default="SUBSCRIBED"
    )  # CREATED / SUBSCRIBED / FOLLOWED
