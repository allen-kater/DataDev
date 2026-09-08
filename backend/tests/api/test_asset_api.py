"""数据资产 API 契约测试（rules/06：统一响应 code===0、分页、错误码分段）。

seed 数据经 async fixture 注入（asyncio_mode=auto，避免手工 run_until_complete）。
"""

import pytest
from sqlalchemy import select

from app.models.database_meta import DatabaseMeta
from app.models.datasource import Datasource
from app.models.table_meta import TableMeta


@pytest.fixture()
async def seeded_session(session):
    ds = Datasource(
        name="hive-cluster", type="HIVE", host="192.168.10.102", enabled=True,
        hms_user="root", hms_password_enc="gcm$x$y", hs2_host="192.168.10.102",
        hs2_port=10000, hs2_user="hadoop",
    )
    session.add(ds)
    await session.flush()
    db = DatabaseMeta(datasource_id=ds.id, name="gmall", last_sync_at=None)
    session.add(db)
    await session.flush()
    session.add_all(
        [
            TableMeta(database_id=db.id, name="ods_order", table_type="MANAGED", comment="订单明细"),
            TableMeta(database_id=db.id, name="dwd_order", table_type="EXTERNAL", comment="订单宽表"),
        ]
    )
    await session.commit()
    return session


# ---------- 数据源 CRUD ----------

async def test_datasource_create(client, session):
    resp = client.post("/api/v1/datasources", json={
        "name": "new-hive", "type": "HIVE", "host": "192.168.10.102",
        "hms_user": "root", "hms_password": "secret", "enabled": True,
    })
    body = resp.json()
    assert body["code"] == 0
    assert "id" in body["data"]

    row = (await session.execute(select(Datasource))).scalar_one()
    assert row.hms_password_enc.startswith("gcm$")
    assert row.hms_password_enc != "secret"


def test_datasource_list_never_returns_password(client, seeded_session):
    resp = client.get("/api/v1/datasources")
    body = resp.json()
    assert body["code"] == 0
    items = body["data"]
    assert len(items) == 1
    for key in ("hms_password_enc", "hs2_password_enc", "jdbc_password_enc"):
        assert key not in items[0]


def test_datasource_delete_unknown_returns_404(client):
    resp = client.delete("/api/v1/datasources/999")
    body = resp.json()
    assert body["code"] == 40401


# ---------- 资产查询 ----------

def test_databases_returns_table_count(client, seeded_session):
    resp = client.get("/api/v1/asset/databases")
    body = resp.json()
    assert body["code"] == 0
    dbs = body["data"]
    assert len(dbs) == 1
    assert dbs[0]["name"] == "gmall"
    assert dbs[0]["table_count"] == 2


def test_search_tables_paginated_and_keyword(client, seeded_session):
    resp = client.get("/api/v1/asset/tables?keyword=order&page=1&page_size=10")
    body = resp.json()
    assert body["code"] == 0
    data = body["data"]
    assert data["total"] == 2
    assert data["page"] == 1
    assert data["page_size"] == 10
    assert all("order" in t["name"] for t in data["items"])


def test_search_tables_by_comment(client, seeded_session):
    resp = client.get("/api/v1/asset/tables?keyword=宽表")
    body = resp.json()
    assert body["code"] == 0
    assert body["data"]["total"] == 1
    assert body["data"]["items"][0]["name"] == "dwd_order"


async def test_table_detail(client, seeded_session):
    table = (await seeded_session.execute(select(TableMeta))).scalars().first()
    tid = table.id
    resp = client.get(f"/api/v1/asset/tables/{tid}")
    body = resp.json()
    assert body["code"] == 0
    detail = body["data"]
    assert detail["name"] == table.name
    assert detail["database_name"] == "gmall"
    assert "ddl" in detail
    assert "CREATE" in detail["ddl"]


def test_table_detail_not_found(client):
    resp = client.get("/api/v1/asset/tables/999")
    assert resp.json()["code"] == 40401


async def test_table_usage(client, seeded_session):
    table = (await seeded_session.execute(select(TableMeta))).scalars().first()
    resp = client.get(f"/api/v1/asset/tables/{table.id}/usage")
    body = resp.json()
    assert body["code"] == 0
    assert body["data"]["total_count"] == 0
    assert body["data"]["daily"] == []


async def test_table_lineage_empty(client, seeded_session):
    table = (await seeded_session.execute(select(TableMeta))).scalars().first()
    resp = client.get(f"/api/v1/asset/tables/{table.id}/lineage")
    body = resp.json()
    assert body["code"] == 0
    assert body["data"]["upstream"] == []
    assert body["data"]["downstream"] == []


async def test_subscribe_and_list(client, seeded_session):
    table = (await seeded_session.execute(select(TableMeta))).scalars().first()
    resp = client.post(f"/api/v1/asset/tables/{table.id}/subscribe", json={"relation": "SUBSCRIBED"})
    assert resp.json()["code"] == 0
    resp2 = client.get("/api/v1/asset/subscriptions")
    assert resp2.json()["code"] == 0
    subs = resp2.json()["data"]
    assert len(subs) == 1
    assert subs[0]["table_name"] == table.name


def test_business_line_create_and_list(client):
    resp = client.post("/api/v1/asset/business-lines", json={"name": "电商", "description": "电商业务"})
    assert resp.json()["code"] == 0
    resp2 = client.get("/api/v1/asset/business-lines")
    lines = resp2.json()["data"]
    assert len(lines) == 1
    assert lines[0]["name"] == "电商"
