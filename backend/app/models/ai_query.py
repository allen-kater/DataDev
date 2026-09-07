"""ai_query：AI 问答记录（Text2SQL / Explain / Optimize / Diagnose / Dict）。"""

from datetime import datetime
from typing import Optional

from sqlalchemy import BigInteger, DateTime, Float, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class AiQuery(Base):
    __tablename__ = "ai_query"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    user_id: Mapped[Optional[int]] = mapped_column(ForeignKey("sys_user.id"))
    query_type: Mapped[str] = mapped_column(
        String(16), nullable=False
    )  # TEXT2SQL / EXPLAIN / OPTIMIZE / DIAGNOSE / DICT
    input_text: Mapped[Optional[str]] = mapped_column(Text)  # 自然语言或 SQL
    output_text: Mapped[Optional[str]] = mapped_column(Text)
    generated_sql: Mapped[Optional[str]] = mapped_column(Text)  # Text2SQL 产物
    execution_id: Mapped[Optional[int]] = mapped_column(
        BigInteger, ForeignKey("task_execution.id")
    )  # 用户执行生成 SQL 时关联
    context_tables: Mapped[Optional[str]] = mapped_column(Text)  # RAG 命中表清单
    model: Mapped[Optional[str]] = mapped_column(String(64))
    tokens: Mapped[Optional[int]] = mapped_column(Integer)
    cost: Mapped[Optional[float]] = mapped_column(Float)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False
    )
