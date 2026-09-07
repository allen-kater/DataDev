"""workflow：工作流定义（DolphinScheduler process-definition 镜像 + 本地增强）。"""

from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class Workflow(Base):
    __tablename__ = "workflow"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    project_id: Mapped[Optional[int]] = mapped_column(Integer)  # 项目分组（B22，预留）
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    cron_expr: Mapped[Optional[str]] = mapped_column(String(32))
    dag_json: Mapped[Optional[str]] = mapped_column(Text)  # 节点+连线，对齐 DS schema
    ds_project_code: Mapped[Optional[str]] = mapped_column(String(64))
    ds_definition_code: Mapped[Optional[str]] = mapped_column(String(64))
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="DRAFT"
    )  # DRAFT / PUBLISHED / OFFLINE
    current_version: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False
    )
