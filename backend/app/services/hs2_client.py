"""HS2（HiveServer2）客户端：数据预览 / SHOW CREATE TABLE（pyhive Thrift，IP 直连）。

- pyhive 为同步库，统一放 `asyncio.to_thread` 执行，不阻塞 event loop（rules/04）；
- 连接参数来自 datasource（hs2_host/port/user）或回退 config.yaml；
- 只执行 SELECT / SHOW CREATE TABLE 只读语句，禁写（铁律 2 / rules/10）；
- 结果统一转换为「列名 + 行列表」JSON 形状。
"""

from __future__ import annotations

import asyncio
from typing import Any, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.logging import get_logger
from app.models.datasource import Datasource

logger = get_logger(__name__)

MAX_PREVIEW_ROWS = 100


def _hs2_params(ds: Datasource) -> dict:
    settings = get_settings()
    hs2 = settings.hs2
    return {
        "host": ds.hs2_host or hs2.host,
        "port": int(ds.hs2_port or hs2.port),
        "user": ds.hs2_user or hs2.user,
        "password": ds.hs2_password_enc or hs2.password,
    }


def _query_sync(params: dict, sql: str, limit: int) -> dict[str, Any]:
    """同步执行只读 SQL，返回 {columns, rows, truncated}。"""
    from pyhive import hive

    kwargs: dict[str, Any] = {"host": params["host"], "port": params["port"], "username": params["user"]}
    if params.get("password"):
        # 集群 HS2 实测：NONE 模式传密码会报错；配置了密码则用 CUSTOM(PLAIN) 认证
        kwargs.update(auth="CUSTOM", password=params["password"])
    conn = hive.connect(**kwargs)
    try:
        cursor = conn.cursor()
        cursor.execute(f"{sql} LIMIT {limit}" if _is_select(sql) else sql)
        col_names = [desc[0] for desc in cursor.description or []]
        rows = cursor.fetchall()
        return {
            "columns": col_names,
            "rows": [list(r) for r in rows],
            "truncated": len(rows) >= limit,
        }
    finally:
        conn.close()


def _is_select(sql: str) -> bool:
    return sql.strip().upper().startswith("SELECT")


async def preview_table(session: AsyncSession, ds: Datasource, table: str, limit: int = 20) -> dict[str, Any]:
    """预览表前 limit 行（SELECT * FROM `db`.`table` LIMIT n）。

    table 形如 `db.table`，由调用方保证来自本地元数据（无注入风险）。
    """
    if limit > MAX_PREVIEW_ROWS:
        limit = MAX_PREVIEW_ROWS
    if "." not in table:
        raise ValueError("table must be `db.table` format")
    db, name = table.split(".", 1)
    sql = f"SELECT * FROM `{db}`.`{name}`"
    params = _hs2_params(ds)
    result = await asyncio.to_thread(_query_sync, params, sql, limit)
    return result


async def show_create_table(session: AsyncSession, ds: Datasource, table: str) -> str:
    """SHOW CREATE TABLE `db`.`table`（表详情 DDL 兜底，Phase 3 复用）。"""
    if "." not in table:
        raise ValueError("table must be `db.table` format")
    db, name = table.split(".", 1)
    sql = f"SHOW CREATE TABLE `{db}`.`{name}`"
    params = _hs2_params(ds)
    result = await asyncio.to_thread(_query_sync, params, sql, 1)
    rows = result.get("rows", [])
    if not rows:
        return ""
    # SHOW CREATE TABLE 返回单行单列（或双列：完整 DDL + 操作列）
    return str(rows[0][0])
