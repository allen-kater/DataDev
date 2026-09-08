"""pytest 公共夹具：内存 SQLite + FastAPI TestClient 依赖覆盖。

规则（rules/09）：测试隔离，不污染 data/dataflow.db。
"""

import asyncio
import os
from pathlib import Path

import pytest

os.environ.setdefault("DATAFLOW_SECRET_KEY", "MDAwMDAwMDAwMDAwMDAwMDAwMDAwMDAwMDAwMDAwMDA=")  # 测试固定密钥

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.database import get_session
from app.models.base import Base


@pytest.fixture(scope="session")
def event_loop():
    """pytest-asyncio 会话级事件循环。"""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture()
async def db_engine(tmp_path):
    """每个用例独立的内存 SQLite 引擎 + 全表建表。"""
    url = f"sqlite+aiosqlite:///{Path(tmp_path) / 'test.db'}"
    engine = create_async_engine(url)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    await engine.dispose()


@pytest.fixture()
async def session_factory(db_engine):
    return async_sessionmaker(db_engine, class_=AsyncSession, expire_on_commit=False)


@pytest.fixture()
async def session(session_factory):
    async with session_factory() as s:
        yield s


@pytest.fixture()
def client(session_factory):
    """独立 FastAPI TestClient：仅挂载被测路由，依赖覆盖为测试库。

    不引入 app.main（避免 lifespan 触碰真实 DB 与启动调度器）。
    """
    from fastapi import FastAPI
    from fastapi.testclient import TestClient

    from app.api import asset

    test_app = FastAPI()
    test_app.include_router(asset.router, prefix="/api/v1")
    test_app.include_router(asset.datasource_router, prefix="/api/v1")

    async def override_get_session():
        async with session_factory() as s:
            yield s

    test_app.dependency_overrides[get_session] = override_get_session
    with TestClient(test_app) as c:
        yield c
