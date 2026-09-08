"""数据资产查询服务：库/表检索、表详情、热度、血缘、业务线、订阅。

只读查询为主（get_*）；业务线/订阅为平台自有数据写操作（本地 SQLite）。
表详情 DDL 从 HMS 元数据离线拼装（不依赖 HS2，快速可靠）；数据预览走 HS2（hs2_client）。
"""

from datetime import timedelta
from typing import Optional

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import utcnow
from app.models.business_line import BusinessLine
from app.models.column_meta import ColumnMeta
from app.models.database_meta import DatabaseMeta
from app.models.hive_partition import HivePartition
from app.models.table_business_line import TableBusinessLine
from app.models.table_lineage import TableLineage
from app.models.table_meta import TableMeta
from app.models.table_subscription import TableSubscription
from app.models.table_usage import TableUsage

# 单用户 MVP：认证未启用前统一 user_id（rules/10 预留登录后替换）
DEFAULT_USER_ID = 1


# ---------- 库 ----------

async def list_databases(session: AsyncSession, datasource_id: Optional[int] = None) -> list[dict]:
    """库列表 + 每库非软删表数。"""
    stmt = select(DatabaseMeta)
    if datasource_id:
        stmt = stmt.where(DatabaseMeta.datasource_id == datasource_id)
    dbs = (await session.execute(stmt)).scalars().all()

    db_ids = [db.id for db in dbs]
    counts: dict[int, int] = {}
    if db_ids:
        rows = (
            await session.execute(
                select(TableMeta.database_id, func.count(TableMeta.id))
                .where(TableMeta.database_id.in_(db_ids), TableMeta.is_deleted.is_(False))
                .group_by(TableMeta.database_id)
            )
        ).all()
        counts = {db_id: cnt for db_id, cnt in rows}
    return [
        {
            "id": db.id,
            "name": db.name,
            "location": db.location,
            "owner": db.owner,
            "comment": db.comment,
            "table_count": counts.get(db.id, 0),
        }
        for db in dbs
    ]


# ---------- 表搜索 ----------

async def search_tables(
    session: AsyncSession,
    db_id: Optional[int] = None,
    datasource_id: Optional[int] = None,
    keyword: Optional[str] = None,
    page: int = 1,
    page_size: int = 20,
) -> tuple[int, list[dict]]:
    """表搜索：LIKE 表名+表注释+字段名+字段注释（rules/06 契约）。

    返回 (total, items)。
    """
    base = (
        select(TableMeta, DatabaseMeta.name)
        .join(DatabaseMeta, TableMeta.database_id == DatabaseMeta.id)
        .where(TableMeta.is_deleted.is_(False))
    )
    if db_id:
        base = base.where(TableMeta.database_id == db_id)
    if datasource_id:
        base = base.where(DatabaseMeta.datasource_id == datasource_id)
    if keyword:
        like = f"%{keyword}%"
        subq = (
            select(ColumnMeta.table_id)
            .where(ColumnMeta.name.like(like) | ColumnMeta.comment.like(like))
        )
        base = base.where(
            TableMeta.name.like(like)
            | TableMeta.comment.like(like)
            | TableMeta.id.in_(subq)
        )

    total = (await session.execute(select(func.count()).select_from(base.subquery()))).scalar_one()

    rows = (
        await session.execute(
            base.order_by(TableMeta.database_id, TableMeta.name)
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
    ).all()
    items = [
        {
            "id": t.id,
            "database_id": t.database_id,
            "database_name": db_name,
            "name": t.name,
            "table_type": t.table_type,
            "owner": t.owner,
            "comment": t.comment,
            "num_rows": t.num_rows,
            "total_size": t.total_size,
            "last_ddl_time": t.last_ddl_time,
        }
        for t, db_name in rows
    ]
    return total, items


# ---------- 表详情 ----------

def _build_ddl(table: TableMeta, columns: list[ColumnMeta], partitions: list) -> str:
    """由 HMS 元数据拼装 CREATE TABLE DDL（仅展示，不做文件操作）。"""
    lines = [f"CREATE {'EXTERNAL ' if table.table_type == 'EXTERNAL' else ''}TABLE `{table.name}` ("]
    col_lines = []
    for col in columns:
        if col.is_partition_key:
            continue
        comment = f" COMMENT '{col.comment}'" if col.comment else ""
        col_lines.append(f"  `{col.name}` {col.type_name or 'string'}{comment}")
    if partitions:
        pk_lines = [f"  `{p.name}` {p.type_name or 'string'}" for p in partitions]
        lines.append(",\n".join(col_lines + pk_lines))
        lines.append(")")
        lines.append("PARTITIONED BY (")
        lines.append(",\n".join(pk_lines))
        lines.append(")")
    else:
        lines.append(",\n".join(col_lines))
        lines.append(")")
    if table.comment:
        lines.append(f"COMMENT '{table.comment}'")
    if table.serde:
        lines.append(f"ROW FORMAT SERDE '{table.serde}'")
    lines.append(f"STORED AS INPUTFORMAT '{table.input_format or ''}' OUTPUTFORMAT '{table.output_format or ''}'")
    if table.location:
        lines.append(f"LOCATION '{table.location}'")
    return "\n".join(lines)


async def get_table_detail(session: AsyncSession, table_id: int) -> Optional[dict]:
    """表详情：基本信息 + 字段 + 分区 + 离线拼装 DDL。"""
    stmt = (
        select(TableMeta, DatabaseMeta)
        .join(DatabaseMeta, TableMeta.database_id == DatabaseMeta.id)
        .where(TableMeta.id == table_id)
    )
    row = (await session.execute(stmt)).first()
    if row is None:
        return None
    table, db = row

    columns = (
        await session.execute(
            select(ColumnMeta)
            .where(ColumnMeta.table_id == table_id)
            .order_by(ColumnMeta.ordinal)
        )
    ).scalars().all()

    partitions = (
        await session.execute(
            select(ColumnMeta)
            .where(ColumnMeta.table_id == table_id, ColumnMeta.is_partition_key.is_(True))
            .order_by(ColumnMeta.ordinal)
        )
    ).scalars().all()

    partition_list = (
        await session.execute(
            select(HivePartition).where(HivePartition.table_id == table_id).order_by(HivePartition.id)
        )
    ).scalars().all()

    return {
        "id": table.id,
        "database_name": db.name,
        "name": table.name,
        "table_type": table.table_type,
        "location": table.location,
        "input_format": table.input_format,
        "output_format": table.output_format,
        "serde": table.serde,
        "num_rows": table.num_rows,
        "num_files": table.num_files,
        "total_size": table.total_size,
        "create_time": table.create_time,
        "last_access_time": table.last_access_time,
        "owner": table.owner,
        "comment": table.comment,
        "view_text": table.view_text,
        "ddl": _build_ddl(table, columns, partitions),
        "columns": [
            {
                "name": c.name,
                "type_name": c.type_name,
                "ordinal": c.ordinal,
                "comment": c.comment,
                "is_partition_key": c.is_partition_key,
            }
            for c in columns
        ],
        "partitions": [
            {
                "partition_spec": p.partition_spec,
                "location": p.location,
                "num_rows": p.num_rows,
                "total_size": p.total_size,
                "created_at": p.created_at,
            }
            for p in partition_list
        ],
    }


# ---------- 热度 ----------

async def get_usage_stats(session: AsyncSession, table_id: int) -> dict:
    """近 7 天热度：总数、最近使用、按日分布。"""
    since = utcnow().replace(tzinfo=None) - timedelta(days=7)
    total = (
        await session.execute(
            select(func.count(TableUsage.id)).where(TableUsage.table_id == table_id)
        )
    ).scalar_one()
    last = (
        await session.execute(
            select(func.max(TableUsage.used_at)).where(TableUsage.table_id == table_id)
        )
    ).scalar_one_or_none()
    rows = (
        await session.execute(
            select(func.date(TableUsage.used_at), func.count(TableUsage.id))
            .where(TableUsage.table_id == table_id, TableUsage.used_at >= since)
            .group_by(func.date(TableUsage.used_at))
        )
    ).all()
    return {
        "table_id": table_id,
        "total_count": total,
        "last_used_at": last,
        "daily": [{"date": str(d), "count": c} for d, c in rows],
    }


# ---------- 血缘 ----------

async def get_lineage(session: AsyncSession, table_id: int) -> dict:
    """表级血缘：上游（产出该表）/ 下游（该表产出）。"""
    up_rows = (
        await session.execute(
            select(TableLineage.upstream_table_id, TableLineage.source, TableLineage.sql_snippet)
            .where(TableLineage.downstream_table_id == table_id)
        )
    ).all()
    down_rows = (
        await session.execute(
            select(TableLineage.downstream_table_id, TableLineage.source, TableLineage.sql_snippet)
            .where(TableLineage.upstream_table_id == table_id)
        )
    ).all()

    async def _node(tbl_id: int) -> Optional[dict]:
        row = (
            await session.execute(
                select(TableMeta.name, DatabaseMeta.name)
                .join(DatabaseMeta, TableMeta.database_id == DatabaseMeta.id)
                .where(TableMeta.id == tbl_id)
            )
        ).first()
        if row is None:
            return None
        name, db_name = row
        return {"id": tbl_id, "name": name, "database_name": db_name}

    upstream: list[dict] = []
    down_nodes: list[dict] = []
    edges: list[dict] = []
    for up_id, source, snippet in up_rows:
        node = await _node(up_id)
        if node and node not in upstream:
            upstream.append(node)
            edges.append(
                {
                    "source": source,
                    "source_sql": snippet,
                    "upstream": node,
                    "downstream": {"id": table_id, "name": "", "database_name": ""},
                }
            )
    for down_id, source, snippet in down_rows:
        node = await _node(down_id)
        if node and node not in down_nodes:
            down_nodes.append(node)
            edges.append(
                {
                    "source": source,
                    "source_sql": snippet,
                    "upstream": {"id": table_id, "name": "", "database_name": ""},
                    "downstream": node,
                }
            )
    table = (await session.get(TableMeta, table_id))
    return {
        "table_id": table_id,
        "table_name": table.name if table else "",
        "upstream": upstream,
        "downstream": down_nodes,
        "edges": edges,
    }


async def preview_table(session: AsyncSession, table_id: int, limit: int = 20) -> dict:
    """数据预览：经 HS2 SELECT 前 limit 行（A18，铁律 2 只读）。"""
    from app.models.datasource import Datasource
    from app.services.hs2_client import preview_table as _preview

    stmt = (
        select(Datasource, TableMeta, DatabaseMeta.name)
        .join(DatabaseMeta, DatabaseMeta.datasource_id == Datasource.id)
        .join(TableMeta, TableMeta.database_id == DatabaseMeta.id)
        .where(TableMeta.id == table_id)
    )
    row = (await session.execute(stmt)).first()
    if row is None:
        raise ValueError("table not found")
    ds, table, db_name = row
    return await _preview(session, ds, f"{db_name}.{table.name}", limit)


# ---------- 业务线 ----------

async def list_business_lines(session: AsyncSession) -> list[dict]:
    lines = (await session.execute(select(BusinessLine).order_by(BusinessLine.id))).scalars().all()
    ids = [line.id for line in lines]
    counts: dict[int, int] = {}
    if ids:
        rows = (
            await session.execute(
                select(TableBusinessLine.business_line_id, func.count(TableBusinessLine.table_id))
                .where(TableBusinessLine.business_line_id.in_(ids))
                .group_by(TableBusinessLine.business_line_id)
            )
        ).all()
        counts = {bl_id: cnt for bl_id, cnt in rows}
    return [
        {
            "id": line.id,
            "name": line.name,
            "parent_id": line.parent_id,
            "owner": line.owner,
            "description": line.description,
            "table_count": counts.get(line.id, 0),
        }
        for line in lines
    ]


async def create_business_line(session: AsyncSession, name: str, parent_id=None, owner=None, description=None) -> BusinessLine:
    line = BusinessLine(name=name, parent_id=parent_id, owner=owner, description=description)
    session.add(line)
    await session.flush()
    return line


async def assign_table_to_line(session: AsyncSession, table_id: int, business_line_id: int) -> None:
    exist = (
        await session.execute(
            select(TableBusinessLine).where(
                TableBusinessLine.table_id == table_id,
                TableBusinessLine.business_line_id == business_line_id,
            )
        )
    ).scalar_one_or_none()
    if exist is None:
        session.add(TableBusinessLine(table_id=table_id, business_line_id=business_line_id))
        await session.flush()


# ---------- 订阅 ----------

async def subscribe_table(session: AsyncSession, table_id: int, relation: str = "SUBSCRIBED") -> None:
    exist = (
        await session.execute(
            select(TableSubscription).where(
                TableSubscription.table_id == table_id,
                TableSubscription.user_id == DEFAULT_USER_ID,
            )
        )
    ).scalar_one_or_none()
    if exist is None:
        session.add(
            TableSubscription(user_id=DEFAULT_USER_ID, table_id=table_id, relation=relation)
        )
        await session.flush()


async def list_subscriptions(session: AsyncSession) -> list[dict]:
    stmt = (
        select(TableSubscription, TableMeta.name, DatabaseMeta.name)
        .join(TableMeta, TableSubscription.table_id == TableMeta.id)
        .join(DatabaseMeta, TableMeta.database_id == DatabaseMeta.id)
        .where(TableSubscription.user_id == DEFAULT_USER_ID)
        .order_by(TableSubscription.created_at.desc())
    )
    rows = (await session.execute(stmt)).all()
    return [
        {
            "id": sub.id,
            "table_id": sub.table_id,
            "relation": sub.relation,
            "created_at": sub.created_at,
            "table_name": table_name,
            "database_name": db_name,
        }
        for sub, table_name, db_name in rows
    ]
