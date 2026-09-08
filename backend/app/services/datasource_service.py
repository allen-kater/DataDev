"""数据源服务：CRUD / 连接测试 / 触发采集。

- 密码字段入库前 AES 加密（rules/10），响应永不返回密文；
- 连接测试：HMS 用 pymysql 直连（3s 超时），HS2 用 pyhive（如提供 hs2 参数）；
- sync 委托 collector.run_collect（异步采集）。
"""

from __future__ import annotations

import asyncio
import time
from typing import Optional

import pymysql
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.logging import get_logger
from app.core.security import decrypt_ciphertext, encrypt_plaintext
from app.models.datasource import Datasource
from app.schemas.asset import DatasourceCreate, DatasourceUpdate

logger = get_logger(__name__)

TEST_TIMEOUT_SEC = 3


def _encrypt_fields(payload: DatasourceCreate | DatasourceUpdate) -> dict:
    """提取需要加密的密码字段（明文 → AES 密文）。"""
    data = payload.model_dump(exclude_unset=True)
    out: dict = {}
    for key in ("hms_password", "hs2_password", "jdbc_password"):
        if data.get(key):
            out[f"{key}_enc"] = encrypt_plaintext(data[key])
        out.pop(key, None)
    return out


async def create_datasource(session: AsyncSession, payload: DatasourceCreate) -> Datasource:
    secret = _encrypt_fields(payload)
    ds = Datasource(**payload.model_dump(exclude={"hms_password", "hs2_password", "jdbc_password"}), **secret)
    session.add(ds)
    await session.flush()
    return ds


async def update_datasource(session: AsyncSession, ds_id: int, payload: DatasourceUpdate) -> Optional[Datasource]:
    ds = (await session.execute(select(Datasource).where(Datasource.id == ds_id))).scalar_one_or_none()
    if ds is None:
        return None
    fields = payload.model_dump(exclude_unset=True)
    secret = _encrypt_fields(payload)
    fields.update(secret)
    for key, value in fields.items():
        if value is not None or key in {"hs2_port"}:
            setattr(ds, key, value)
    await session.flush()
    return ds


async def test_datasource(session: AsyncSession, ds_id: int) -> dict:
    """连接测试：HMS 直连（必测）+ HS2 探测（若配置）。

    返回 {ok, message, latency_ms}。
    """
    ds = (await session.execute(select(Datasource).where(Datasource.id == ds_id))).scalar_one_or_none()
    if ds is None:
        return {"ok": False, "message": "数据源不存在", "latency_ms": None}

    settings = get_settings()
    hms = settings.hms
    host = ds.host or hms.host
    port = int(hms.port)
    user = ds.hms_user or hms.user
    password = decrypt_ciphertext(ds.hms_password_enc) or hms.password

    start = time.perf_counter()
    try:
        await asyncio.to_thread(_ping_mysql, host, port, hms.database, user, password)
        latency = int((time.perf_counter() - start) * 1000)
        return {"ok": True, "message": "连接成功", "latency_ms": latency}
    except Exception as exc:
        latency = int((time.perf_counter() - start) * 1000)
        logger.warning("数据源连接测试失败 ds=%s: %s", ds.name, exc)
        return {"ok": False, "message": f"连接失败: {exc}", "latency_ms": latency}


def _ping_mysql(host: str, port: int, database: str, user: str, password: str) -> None:
    conn = pymysql.connect(
        host=host, port=port, user=user, password=password, database=database,
        connect_timeout=TEST_TIMEOUT_SEC, ssl_disabled=True,
    )
    conn.close()


async def sync_datasource(session: AsyncSession, ds_id: int) -> dict:
    """触发一次元数据采集（委托 collector）。"""
    from app.services.collector import run_collect

    return await run_collect(session, ds_id)


def _to_out(ds: Datasource) -> dict:
    """响应形状：永不返回密码密文字段（rules/10）。"""
    return {
        "id": ds.id,
        "name": ds.name,
        "type": ds.type,
        "host": ds.host,
        "hms_jdbc_url": ds.hms_jdbc_url,
        "hms_user": ds.hms_user,
        "hs2_host": ds.hs2_host,
        "hs2_port": ds.hs2_port,
        "hs2_user": ds.hs2_user,
        "jdbc_url": ds.jdbc_url,
        "jdbc_user": ds.jdbc_user,
        "last_sync_at": ds.last_sync_at,
        "enabled": ds.enabled,
    }


async def list_datasources(session: AsyncSession) -> list[dict]:
    rows = (await session.execute(select(Datasource).order_by(Datasource.id))).scalars().all()
    return [_to_out(ds) for ds in rows]


async def get_datasource(session: AsyncSession, ds_id: int) -> Optional[dict]:
    ds = (await session.execute(select(Datasource).where(Datasource.id == ds_id))).scalar_one_or_none()
    return _to_out(ds) if ds else None


async def delete_datasource(session: AsyncSession, ds_id: int) -> bool:
    ds = (await session.execute(select(Datasource).where(Datasource.id == ds_id))).scalar_one_or_none()
    if ds is None:
        return False
    await session.delete(ds)
    return True
