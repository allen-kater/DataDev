"""task_parameter：任务参数定义（推送 DS 时映射为全局参数）。"""

from typing import Optional

from sqlalchemy import Boolean, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class TaskParameter(Base):
    __tablename__ = "task_parameter"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    task_id: Mapped[int] = mapped_column(
        ForeignKey("task.id"), index=True, nullable=False
    )
    name: Mapped[str] = mapped_column(String(64), nullable=False)  # 如 biz_date
    param_type: Mapped[str] = mapped_column(
        String(16), nullable=False, default="STRING"
    )  # STRING / INT / DATE
    scope: Mapped[str] = mapped_column(
        String(16), nullable=False, default="GLOBAL"
    )  # GLOBAL / LOCAL / UPSTREAM
    default_value: Mapped[Optional[str]] = mapped_column(String(255))
    required: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
