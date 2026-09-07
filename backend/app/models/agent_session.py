"""agent_session：AI ETL Agent 会话（MVP 单 Agent 顺序执行）。"""

from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class AgentSession(Base):
    __tablename__ = "agent_session"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[Optional[int]] = mapped_column(ForeignKey("sys_user.id"))
    initial_prompt: Mapped[Optional[str]] = mapped_column(Text)
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="IN_PROGRESS"
    )  # IN_PROGRESS / AWAITING_APPROVAL / COMPLETED / FAILED
    result_workflow_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("workflow.id")
    )  # 产出工作流
    token_used: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    cost: Mapped[Optional[float]] = mapped_column(Float)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False
    )
