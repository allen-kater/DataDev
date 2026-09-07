"""table_lineage：表级血缘（列级 P2 预留）。"""

from typing import Optional

from sqlalchemy import BigInteger, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin


class TableLineage(Base, TimestampMixin):
    __tablename__ = "table_lineage"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    upstream_table_id: Mapped[int] = mapped_column(
        ForeignKey("table_meta.id"), index=True, nullable=False
    )
    downstream_table_id: Mapped[int] = mapped_column(
        ForeignKey("table_meta.id"), index=True, nullable=False
    )
    source: Mapped[str] = mapped_column(
        String(16), nullable=False, default="SQL_PARSE"
    )  # SQL_PARSE / VIEW_TEXT / MANUAL
    sql_snippet: Mapped[Optional[str]] = mapped_column(Text)  # 血缘来源 SQL（可回查）
