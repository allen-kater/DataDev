"""表级血缘解析：sqlglot 解析 SQL/视图文本 → (upstream, downstream) 表清单。

MVP 只做表级血缘（架构方案 A09，列级 Phase 6 预留）。
表名统一返回 `db.table`（无库名时仅 table，由调用方结合上下文补全）。

用途：
- 采集器对视图（view_text）解析，生成 VIEW_TEXT 血缘；
- Phase 3 SQL 执行后对执行 SQL 解析，生成 SQL_PARSE 血缘；
- 支持手动录入（MANUAL，见 api 层）。
"""

from dataclasses import dataclass, field

import sqlglot
from sqlglot import exp

from app.core.logging import get_logger

logger = get_logger(__name__)


@dataclass
class LineageParse:
    upstream: list[str] = field(default_factory=list)
    downstream: list[str] = field(default_factory=list)


def _table_full_name(node: exp.Table) -> str:
    """Table 节点 → `db.table`（无 db 时仅 table）。"""
    if node.db:
        return f"{node.db}.{node.name}"
    return node.name


def parse_lineage(sql: str) -> LineageParse:
    """解析一条 SQL，返回 {upstream, downstream} 表名清单（去重保序）。

    支持语句：
    - SELECT ... FROM a JOIN b  → upstream=[a, b]
    - INSERT INTO t SELECT ... → downstream=[t], upstream=[源表]
    - CREATE TABLE t AS SELECT → downstream=[t], upstream=[源表]
    - CREATE VIEW v AS SELECT  → downstream=[v], upstream=[源表]
    - 其它（DDL 等）→ 空
    """
    if not sql or not sql.strip():
        return LineageParse()
    try:
        ast = sqlglot.parse_one(sql)
    except Exception:
        logger.warning("SQL 血缘解析失败: %s", sql[:200])
        return LineageParse()

    # 仅 SELECT / INSERT / CREATE 参与血缘（DROP/ALTER 等 DDL 不产生表依赖）
    if not isinstance(ast, (exp.Select, exp.Insert, exp.Create)):
        return LineageParse()

    downstream: list[str] = []
    if isinstance(ast, exp.Insert):
        target = ast.this
        if isinstance(target, exp.Table):
            downstream.append(_table_full_name(target))
    elif isinstance(ast, exp.Create):
        target = ast.this
        if isinstance(target, exp.Table):
            downstream.append(_table_full_name(target))
        elif isinstance(target, exp.Schema) and isinstance(target.this, exp.Table):
            downstream.append(_table_full_name(target.this))

    upstream: list[str] = []
    for node in ast.find_all(exp.Table):
        name = _table_full_name(node)
        if name not in downstream and name not in upstream:
            upstream.append(name)

    return LineageParse(upstream=upstream, downstream=downstream)


def build_ddl_snippet(sql: str, max_len: int = 2000) -> str:
    """血缘来源 SQL 片段（可回查），截断防超长。"""
    sql = (sql or "").strip()
    return sql[:max_len]
