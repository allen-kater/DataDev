"""SQLAlchemy async engine / session 与建表初始化。

规则（rules/04）：数据库操作一律 async session，禁同步阻塞调用。
sync_engine 仅用于 SQLite 外键 PRAGMA 与建表（rules/01 允许）。
"""

from collections.abc import AsyncIterator

from sqlalchemy import event
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.core.config import get_settings

settings = get_settings()

engine = create_async_engine(settings.database.url, echo=settings.database.echo)

SessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


@event.listens_for(engine.sync_engine, "connect")
def _enable_sqlite_foreign_keys(dbapi_connection, _connection_record) -> None:
    """SQLite 默认不强制外键，统一打开（仅对 SQLite 方言生效）。"""
    if settings.database.url.startswith("sqlite"):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()


async def get_session() -> AsyncIterator[AsyncSession]:
    async with SessionLocal() as session:
        yield session


async def init_db() -> None:
    """建库建表（幂等）。导入 Base 会连带注册全部模型（见 app/models/__init__.py）。"""
    from app.models.base import Base  # noqa: F401

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
