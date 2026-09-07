"""column_meta：字段元数据。"""

from typing import Optional

from sqlalchemy import Boolean, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class ColumnMeta(Base):
    __tablename__ = "column_meta"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    table_id: Mapped[int] = mapped_column(
        ForeignKey("table_meta.id"), index=True, nullable=False
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    type_name: Mapped[Optional[str]] = mapped_column(String(128))  # Hive 类型
    ordinal: Mapped[int] = mapped_column(Integer, nullable=False, default=0)  # 序号
    comment: Mapped[Optional[str]] = mapped_column(String(512))
    is_partition_key: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
