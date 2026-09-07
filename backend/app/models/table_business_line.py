"""table_business_line：表与业务线关联表（复合主键）。"""

from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class TableBusinessLine(Base):
    __tablename__ = "table_business_line"

    table_id: Mapped[int] = mapped_column(
        ForeignKey("table_meta.id"), primary_key=True, nullable=False
    )
    business_line_id: Mapped[int] = mapped_column(
        ForeignKey("business_line.id"), primary_key=True, nullable=False
    )
