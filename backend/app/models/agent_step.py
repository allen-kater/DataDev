"""agent_step：Agent 会话内的执行步骤。"""

from typing import Optional

from sqlalchemy import ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class AgentStep(Base):
    __tablename__ = "agent_step"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    session_id: Mapped[int] = mapped_column(
        ForeignKey("agent_session.id"), index=True, nullable=False
    )
    step_no: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    step_name: Mapped[str] = mapped_column(String(64), nullable=False)  # 需求解析/探测源/生成DDL/生成SQL/编排DAG
    model: Mapped[Optional[str]] = mapped_column(String(64))
    prompt: Mapped[Optional[str]] = mapped_column(Text)
    response: Mapped[Optional[str]] = mapped_column(Text)
    latency_ms: Mapped[Optional[int]] = mapped_column(Integer)
    tokens: Mapped[Optional[int]] = mapped_column(Integer)
