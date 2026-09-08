"""数据资产管理路由（Phase 2 完整实现）。

端点契约见 rules/06 与 CLAUDE.md 第 5 节：
- /api/v1/datasources       数据源 CRUD / test / sync
- /api/v1/asset             库 / 表 / 详情 / usage / lineage / 订阅 / 业务线 / 预览
"""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_session
from app.schemas.asset import (
    BusinessLineCreate,
    DatasourceCreate,
    DatasourceUpdate,
    SubscriptionCreate,
)
from app.schemas.common import ApiResponse, PageData, fail, ok
from app.services import asset_service, datasource_service

router = APIRouter(prefix="/asset", tags=["asset"])
datasource_router = APIRouter(prefix="/datasources", tags=["datasource"])


# ---------- 数据源 ----------

@datasource_router.post("", response_model=ApiResponse)
async def create_datasource(
    payload: DatasourceCreate,
    session: AsyncSession = Depends(get_session),
) -> ApiResponse:
    ds = await datasource_service.create_datasource(session, payload)
    await session.commit()
    return ok({"id": ds.id})


@datasource_router.get("", response_model=ApiResponse)
async def list_datasources(
    session: AsyncSession = Depends(get_session),
) -> ApiResponse:
    items = await datasource_service.list_datasources(session)
    return ok(items)


@datasource_router.get("/{ds_id}", response_model=ApiResponse)
async def get_datasource(
    ds_id: int,
    session: AsyncSession = Depends(get_session),
) -> ApiResponse:
    ds = await datasource_service.get_datasource(session, ds_id)
    if ds is None:
        return fail(40401, "数据源不存在")
    return ok(ds)


@datasource_router.put("/{ds_id}", response_model=ApiResponse)
async def update_datasource(
    ds_id: int,
    payload: DatasourceUpdate,
    session: AsyncSession = Depends(get_session),
) -> ApiResponse:
    ds = await datasource_service.update_datasource(session, ds_id, payload)
    if ds is None:
        return fail(40401, "数据源不存在")
    await session.commit()
    return ok({"id": ds.id})


@datasource_router.delete("/{ds_id}", response_model=ApiResponse)
async def delete_datasource(
    ds_id: int,
    session: AsyncSession = Depends(get_session),
) -> ApiResponse:
    removed = await datasource_service.delete_datasource(session, ds_id)
    if not removed:
        return fail(40401, "数据源不存在")
    await session.commit()
    return ok({"id": ds_id})


@datasource_router.post("/{ds_id}/test", response_model=ApiResponse)
async def test_datasource(
    ds_id: int,
    session: AsyncSession = Depends(get_session),
) -> ApiResponse:
    result = await datasource_service.test_datasource(session, ds_id)
    return ok(result)


@datasource_router.post("/{ds_id}/sync", response_model=ApiResponse)
async def sync_datasource(
    ds_id: int,
    session: AsyncSession = Depends(get_session),
) -> ApiResponse:
    try:
        result = await datasource_service.sync_datasource(session, ds_id)
        return ok(result)
    except Exception as exc:
        return fail(50001, f"采集失败: {exc}")


# ---------- 数据资产 ----------

@router.get("/databases", response_model=ApiResponse)
async def list_databases(
    datasource_id: int | None = Query(default=None),
    session: AsyncSession = Depends(get_session),
) -> ApiResponse:
    items = await asset_service.list_databases(session, datasource_id)
    return ok(items)


@router.get("/tables", response_model=ApiResponse)
async def search_tables(
    db_id: int | None = Query(default=None),
    datasource_id: int | None = Query(default=None),
    keyword: str | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    session: AsyncSession = Depends(get_session),
) -> ApiResponse:
    total, items = await asset_service.search_tables(
        session, db_id=db_id, datasource_id=datasource_id,
        keyword=keyword, page=page, page_size=page_size,
    )
    return ok(PageData(total=total, page=page, page_size=page_size, items=items))


@router.get("/tables/{table_id}", response_model=ApiResponse)
async def get_table_detail(
    table_id: int,
    session: AsyncSession = Depends(get_session),
) -> ApiResponse:
    detail = await asset_service.get_table_detail(session, table_id)
    if detail is None:
        return fail(40401, "表不存在")
    return ok(detail)


@router.get("/tables/{table_id}/usage", response_model=ApiResponse)
async def get_table_usage(
    table_id: int,
    session: AsyncSession = Depends(get_session),
) -> ApiResponse:
    return ok(await asset_service.get_usage_stats(session, table_id))


@router.get("/tables/{table_id}/lineage", response_model=ApiResponse)
async def get_table_lineage(
    table_id: int,
    session: AsyncSession = Depends(get_session),
) -> ApiResponse:
    return ok(await asset_service.get_lineage(session, table_id))


@router.post("/tables/{table_id}/subscribe", response_model=ApiResponse)
async def subscribe_table(
    table_id: int,
    payload: SubscriptionCreate | None = None,
    session: AsyncSession = Depends(get_session),
) -> ApiResponse:
    relation = payload.relation if payload else "SUBSCRIBED"
    try:
        await asset_service.subscribe_table(session, table_id, relation)
        await session.commit()
        return ok({"table_id": table_id})
    except Exception as exc:
        return fail(40001, f"订阅失败: {exc}")


@router.get("/subscriptions", response_model=ApiResponse)
async def list_subscriptions(
    session: AsyncSession = Depends(get_session),
) -> ApiResponse:
    return ok(await asset_service.list_subscriptions(session))


# ---------- 业务线 ----------

@router.get("/business-lines", response_model=ApiResponse)
async def list_business_lines(
    session: AsyncSession = Depends(get_session),
) -> ApiResponse:
    return ok(await asset_service.list_business_lines(session))


@router.post("/business-lines", response_model=ApiResponse)
async def create_business_line(
    payload: BusinessLineCreate,
    session: AsyncSession = Depends(get_session),
) -> ApiResponse:
    line = await asset_service.create_business_line(
        session, payload.name, payload.parent_id, payload.owner, payload.description
    )
    await session.commit()
    return ok({"id": line.id})


@router.post("/tables/{table_id}/business-line", response_model=ApiResponse)
async def assign_table_to_line(
    table_id: int,
    business_line_id: int = Query(...),
    session: AsyncSession = Depends(get_session),
) -> ApiResponse:
    try:
        await asset_service.assign_table_to_line(session, table_id, business_line_id)
        await session.commit()
        return ok({"table_id": table_id, "business_line_id": business_line_id})
    except Exception as exc:
        return fail(40001, f"归属失败: {exc}")


# ---------- 数据预览（HS2） ----------

@router.post("/tables/{table_id}/preview", response_model=ApiResponse)
async def preview_table(
    table_id: int,
    limit: int = Query(default=20, ge=1, le=100),
    session: AsyncSession = Depends(get_session),
) -> ApiResponse:
    try:
        result = await asset_service.preview_table(session, table_id, limit)
        return ok(result)
    except Exception as exc:
        return fail(50101, f"预览失败: {exc}")
