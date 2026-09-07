"""workflow_execution：工作流运行实例（DS process-instance 镜像，仅存最新状态展示）。"""

from datetime import datetime
from typing import Optional

from sqlalchemy import BigInteger, DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class WorkflowExecution(Base):
    __tablename__ = "workflow_execution"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    workflow_id: Mapped[int] = mapped_column(
        ForeignKey("workflow.id"), index=True, nullable=False
    )
    ds_instance_id: Mapped[Optional[str]] = mapped_column(String(64))
    trigger_type: Mapped[str] = mapped_column(
        String(16), nullable=False, default="MANUAL"
    )  # CRON / MANUAL / COMPLEMENT
    status: Mapped[Optional[str]] = mapped_column(String(16))
    start_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    end_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    raw_payload: Mapped[Optional[str]] = mapped_column(Text)  # DS 返回原始 JSON
