"""血缘解析单元测试（rules/09：核心链路必须测）。"""

import pytest

from app.services.lineage import parse_lineage


@pytest.mark.parametrize(
    "sql,up,down",
    [
        ("SELECT * FROM a", ["a"], []),
        ("SELECT * FROM db.a JOIN db.b ON a.id = b.id", ["db.a", "db.b"], []),
        ("INSERT INTO t SELECT * FROM s", ["s"], ["t"]),
        ("INSERT INTO db.t SELECT x FROM db.s", ["db.s"], ["db.t"]),
        ("CREATE TABLE t AS SELECT * FROM s", ["s"], ["t"]),
        ("CREATE VIEW v AS SELECT id FROM s", ["s"], ["v"]),
        ("DROP TABLE x", [], []),
        ("ALTER TABLE x ADD COLUMN y INT", [], []),
        ("", [], []),
        ("  ", [], []),
        ("SELECT 1", [], []),  # 无表引用
    ],
)
def test_parse_lineage(sql, up, down):
    r = parse_lineage(sql)
    assert r.upstream == up, f"upstream mismatch: {r.upstream}"
    assert r.downstream == down, f"downstream mismatch: {r.downstream}"
