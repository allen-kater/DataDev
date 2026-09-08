"""元数据采集器：HMS 直读（主路径）+ HS2 兜底（DDL/预览）。

设计（rules/04 采集器约束）：
- pymysql 为同步库，HMS 查询放 `asyncio.to_thread`，不阻塞 event loop；
- 全量拉取 HMS 快照 → 与本地 upsert（按 datasource+db+table 唯一），只写变化部分；
- 本地已存在但源中已消失的表 → 软删（is_deleted）；
- 完成后更新 `datasource.last_sync_at`，并写 `collect_log`；
- 采集失败不影响已有数据（本地先读后写，异常直接抛出由调用方记录）。
"""

from __future__ import annotations

import asyncio
from datetime import datetime
from typing import Any, Optional

import pymysql
from sqlalchemy import delete, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings, utcnow
from app.core.logging import get_logger
from app.models.collect_log import CollectLog
from app.models.collect_task import CollectTask
from app.models.column_meta import ColumnMeta
from app.models.database_meta import DatabaseMeta
from app.models.datasource import Datasource
from app.models.hive_partition import HivePartition
from app.models.table_meta import TableMeta

logger = get_logger(__name__)


def _hms_conn(ds: Datasource) -> dict:
    """构造 HMS 连接参数：主 IP 来自 datasource.host，缺失回退 config.yaml（IP 直连）。"""
    settings = get_settings()
    hms = settings.hms
    return {
        "host": ds.host or hms.host,
        "port": int(hms.port),
        "database": hms.database,
        "user": ds.hms_user or hms.user,
        "password": ds.hms_password_enc or hms.password,
    }


def _fetch_hms_snapshot(conn: dict) -> dict[str, Any]:
    """同步拉取 HMS 全量快照（DBS/TBLS/SDS/SERDES/TABLE_PARAMS/COLUMNS_V2/PARTITION_KEYS/PARTITIONS）。

    返回结构：{dbs: [...], tables: [...], columns: [...], part_keys: [...], partitions: [...]}
    """
    result: dict[str, Any] = {"dbs": [], "tables": [], "columns": [], "part_keys": [], "partitions": []}
    with pymysql.connect(
        host=conn["host"],
        port=int(conn["port"]),
        user=conn["user"],
        password=conn["password"],
        database=conn["database"],
        charset="utf8mb4",
        connect_timeout=5,
        read_timeout=30,
        ssl_disabled=True,  # pymysql 2.x 默认可能协商 TLS，MySQL 5.7 无证书会失败
    ) as cur_ctx:
        with cur_ctx.cursor(pymysql.cursors.DictCursor) as cur:
            cur.execute("SELECT * FROM DBS ORDER BY DB_ID")
            result["dbs"] = list(cur.fetchall())

            cur.execute(
                """SELECT t.TBL_ID, t.TBL_NAME, t.TBL_TYPE, t.OWNER, t.CREATE_TIME,
                          t.LAST_ACCESS_TIME, t.VIEW_EXPANDED_TEXT,
                          d.NAME AS DB_NAME, t.SD_ID
                   FROM TBLS t JOIN DBS d ON t.DB_ID = d.DB_ID ORDER BY t.TBL_ID"""
            )
            tables = list(cur.fetchall())

            sd_ids = {t["SD_ID"] for t in tables if t["SD_ID"]}
            table_params: dict[int, dict[str, str]] = {}
            if tables:
                ids = ",".join(str(t["TBL_ID"]) for t in tables)
                cur.execute(f"SELECT TBL_ID, PARAM_KEY, PARAM_VALUE FROM TABLE_PARAMS WHERE TBL_ID IN ({ids})")
                for row in cur.fetchall():
                    table_params.setdefault(row["TBL_ID"], {})[row["PARAM_KEY"]] = row["PARAM_VALUE"]

            sds: dict[int, dict] = {}
            if sd_ids:
                sids = ",".join(str(x) for x in sd_ids)
                cur.execute(
                    f"""SELECT sd.SD_ID, sd.LOCATION, sd.INPUT_FORMAT, sd.OUTPUT_FORMAT, sd.CD_ID,
                               serde.SLIB AS SERDE
                        FROM SDS sd LEFT JOIN SERDES serde ON sd.SERDE_ID = serde.SERDE_ID
                        WHERE sd.SD_ID IN ({sids})"""
                )
                for row in cur.fetchall():
                    sds[row["SD_ID"]] = row

            cd_ids = {sds[sd]["CD_ID"] for sd in sds if sds[sd].get("CD_ID")}
            columns: list[dict] = []
            if cd_ids:
                cids = ",".join(str(x) for x in cd_ids)
                cur.execute(
                    f"""SELECT CD_ID, COLUMN_NAME, TYPE_NAME, INTEGER_IDX, COMMENT
                        FROM COLUMNS_V2 WHERE CD_ID IN ({cids}) ORDER BY INTEGER_IDX"""
                )
                columns = list(cur.fetchall())

            result["columns"] = columns

            for t in tables:
                t["PARAMS"] = table_params.get(t["TBL_ID"], {})
                t["SD"] = sds.get(t["SD_ID"], {})

            result["tables"] = tables

            cur.execute("SELECT * FROM PARTITION_KEYS ORDER BY INTEGER_IDX")
            result["part_keys"] = list(cur.fetchall())

            if tables:
                ids = ",".join(str(t["TBL_ID"]) for t in tables)
                cur.execute(
                    f"""SELECT PART_ID, TBL_ID, PART_NAME, CREATE_TIME, SD_ID
                        FROM PARTITIONS WHERE TBL_ID IN ({ids}) ORDER BY PART_ID"""
                )
                partitions = list(cur.fetchall())
                p_sds: dict[int, dict] = {}
                p_sd_ids = {p["SD_ID"] for p in partitions if p["SD_ID"]}
                if p_sd_ids:
                    psids = ",".join(str(x) for x in p_sd_ids)
                    cur.execute(f"SELECT SD_ID, LOCATION FROM SDS WHERE SD_ID IN ({psids})")
                    for row in cur.fetchall():
                        p_sds[row["SD_ID"]] = row
                for p in partitions:
                    p["LOCATION"] = p_sds.get(p["SD_ID"], {}).get("LOCATION")
                result["partitions"] = partitions
    return result


def _parse_ddl_time(params: dict) -> Optional[int]:
    """transient_lastDdlTime 秒级时间戳 → int。"""
    raw = params.get("transient_lastDdlTime")
    return int(raw) if raw and str(raw).isdigit() else None


def _hive_ts_to_dt(ts: Optional[int]) -> Optional[datetime]:
    if not ts:
        return None
    return datetime.utcfromtimestamp(ts)


async def _upsert_snapshot(session: AsyncSession, ds: Datasource, snap: dict[str, Any]) -> int:
    """快照落库（upsert 语义：存在则更新变化，不存在则插入），返回处理表数。

    不删除源中已消失的表，仅对本地残留标记 is_deleted（软删，见架构方案 7.2）。
    """
    now = utcnow()

    # 1. 库：按 (datasource_id, name) upsert
    db_id_map: dict[str, int] = {}
    for db in snap["dbs"]:
        name = db["NAME"]
        stmt = select(DatabaseMeta).where(
            DatabaseMeta.datasource_id == ds.id, DatabaseMeta.name == name
        )
        dbm = (await session.execute(stmt)).scalar_one_or_none()
        if dbm is None:
            dbm = DatabaseMeta(
                datasource_id=ds.id,
                name=name,
                location=db.get("DB_LOCATION_URI"),
                owner=db.get("OWNER_NAME"),
                comment=db.get("DESC"),
                last_sync_at=now,
            )
            session.add(dbm)
        else:
            dbm.location = db.get("DB_LOCATION_URI")
            dbm.owner = db.get("OWNER_NAME")
            dbm.comment = db.get("DESC")
            dbm.last_sync_at = now
        await session.flush()
        db_id_map[name] = dbm.id

    # 2. 分区键：按表分组（字段 is_partition_key 依据）
    part_key_of: dict[int, set[str]] = {}
    for pk in snap["part_keys"]:
        part_key_of.setdefault(pk["TBL_ID"], set()).add(pk["PKEY_NAME"])

    # 3. 表 + 字段 + 分区
    scanned = 0
    for t in snap["tables"]:
        db_name = t["DB_NAME"]
        db_id = db_id_map.get(db_name)
        if db_id is None:
            continue
        params = t.get("PARAMS", {})
        sd = t.get("SD", {})
        scanned += 1

        tbl = (
            await session.execute(
                select(TableMeta).where(
                    TableMeta.database_id == db_id, TableMeta.name == t["TBL_NAME"]
                )
            )
        ).scalar_one_or_none()
        ddl_time = _parse_ddl_time(params)
        if tbl is None:
            tbl = TableMeta(database_id=db_id, name=t["TBL_NAME"], last_sync_at=now)
            session.add(tbl)
        else:
            tbl.is_deleted = False
            tbl.last_sync_at = now
        # 全量覆盖基础属性（简单可靠，本地规模秒级）
        tbl.table_type = {"MANAGED_TABLE": "MANAGED", "EXTERNAL_TABLE": "EXTERNAL", "VIRTUAL_VIEW": "VIRTUAL_VIEW"}.get(t["TBL_TYPE"], t["TBL_TYPE"])
        tbl.owner = t.get("OWNER")
        tbl.create_time = _hive_ts_to_dt(t.get("CREATE_TIME"))
        tbl.last_access_time = _hive_ts_to_dt(t.get("LAST_ACCESS_TIME"))
        tbl.view_text = t.get("VIEW_EXPANDED_TEXT")
        tbl.location = sd.get("LOCATION")
        tbl.input_format = sd.get("INPUT_FORMAT")
        tbl.output_format = sd.get("OUTPUT_FORMAT")
        tbl.serde = sd.get("SERDE")
        tbl.last_ddl_time = ddl_time
        tbl.num_rows = int(params["numRows"]) if str(params.get("numRows", "")).isdigit() else None
        tbl.num_files = int(params["numFiles"]) if str(params.get("numFiles", "")).isdigit() else None
        tbl.total_size = int(params["totalSize"]) if str(params.get("totalSize", "")).isdigit() else None
        tbl.comment = params.get("comment")
        await session.flush()

        # 字段：全量替换（先删该表旧列，再插入新列；本地规模行数小）
        await session.execute(delete(ColumnMeta).where(ColumnMeta.table_id == tbl.id))
        cd_id = sd.get("CD_ID")
        pks = part_key_of.get(t["TBL_ID"], set())
        for col in snap["columns"]:
            if col["CD_ID"] != cd_id:
                continue
            session.add(
                ColumnMeta(
                    table_id=tbl.id,
                    name=col["COLUMN_NAME"],
                    type_name=col["TYPE_NAME"],
                    ordinal=col["INTEGER_IDX"],
                    comment=col.get("COMMENT"),
                    is_partition_key=col["COLUMN_NAME"] in pks,
                )
            )
        # 分区（按 partition_spec upsert）
        for p in snap["partitions"]:
            if p["TBL_ID"] != t["TBL_ID"]:
                continue
            exist = (
                await session.execute(
                    select(HivePartition).where(
                        HivePartition.table_id == tbl.id,
                        HivePartition.partition_spec == p["PART_NAME"],
                    )
                )
            ).scalar_one_or_none()
            if exist is None:
                session.add(
                    HivePartition(
                        table_id=tbl.id,
                        partition_spec=p["PART_NAME"],
                        location=p.get("LOCATION"),
                        created_at=_hive_ts_to_dt(p.get("CREATE_TIME")),
                    )
                )

    # 4. 软删：源中已消失的表（按库分别比对，避免跨库同名误删）
    names_by_db: dict[int, set[str]] = {}
    for t in snap["tables"]:
        db_id = db_id_map.get(t["DB_NAME"])
        if db_id is not None:
            names_by_db.setdefault(db_id, set()).add(t["TBL_NAME"])
    for db_id, alive_names in names_by_db.items():
        await session.execute(
            update(TableMeta)
            .where(TableMeta.database_id == db_id, TableMeta.is_deleted.is_(False))
            .where(TableMeta.name.notin_(alive_names))
            .values(is_deleted=True)
        )
    return scanned


async def run_collect(session: AsyncSession, ds_id: int) -> dict[str, Any]:
    """执行一次采集（手动触发或 APScheduler 调用）。

    返回 {tables_scanned, cost_sec, status, error_msg}，并写 collect_log。
    """
    ds = (
        await session.execute(select(Datasource).where(Datasource.id == ds_id))
    ).scalar_one_or_none()
    if ds is None:
        raise ValueError(f"datasource {ds_id} not found")
    if not ds.enabled:
        raise ValueError(f"datasource {ds_id} disabled")

    start = utcnow()
    # collect_log.task_id 为 FK 非空：手动触发无任务时自动建一条（schedule 为空）
    task = (
        await session.execute(
            select(CollectTask)
            .where(CollectTask.datasource_id == ds_id)
            .order_by(CollectTask.id)
            .limit(1)
        )
    ).scalar_one_or_none()
    if task is None:
        task = CollectTask(datasource_id=ds_id, enabled=True)
        session.add(task)
        await session.flush()
    log = CollectLog(task_id=task.id, start_at=start, status="running")
    session.add(log)
    await session.flush()

    try:
        conn = _hms_conn(ds)
        snap = await asyncio.to_thread(_fetch_hms_snapshot, conn)
        scanned = await _upsert_snapshot(session, ds, snap)
        ds.last_sync_at = utcnow()
        end = utcnow()
        cost = int((end - start).total_seconds())
        log.end_at = end
        log.cost_sec = cost
        log.tables_scanned = scanned
        log.status = "success"
        await session.commit()
        logger.info("采集完成 ds=%s scanned=%s cost=%ss", ds.name, scanned, cost)
        return {"tables_scanned": scanned, "cost_sec": cost, "status": "success", "error_msg": None}
    except Exception as exc:  # 采集失败不影响已有数据
        await session.rollback()
        logger.error("采集失败 ds=%s: %s", ds.name, exc)
        log.status = "failed"
        log.error_msg = str(exc)[:2000]
        await session.commit()
        raise
