"""数据资产模块 Schema（与 models 分离，见 rules/02）。

覆盖：数据源（datasource）CRUD/test/sync + 资产查询（库/表/详情/热度/血缘/订阅/业务线）。
响应统一 `ApiResponse` 包装（schemas/common.py），此处定义 data 内部形状。
"""

from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, Field

DatasourceType = Literal["HIVE", "MYSQL", "POSTGRESQL"]


# ---------- 数据源 ----------

class DatasourceCreate(BaseModel):
    name: str = Field(min_length=1, max_length=128)
    type: DatasourceType = "HIVE"
    host: str = Field(min_length=1, max_length=128, description="集群 IP，禁 hostname")
    hms_jdbc_url: Optional[str] = Field(default=None, max_length=512)
    hms_user: Optional[str] = Field(default=None, max_length=64)
    hms_password: Optional[str] = Field(default=None, max_length=512, description="明文，仅用于入库加密")
    hs2_host: Optional[str] = Field(default=None, max_length=128)
    hs2_port: Optional[int] = Field(default=10000)
    hs2_user: Optional[str] = Field(default=None, max_length=64)
    hs2_password: Optional[str] = Field(default=None, max_length=512)
    jdbc_url: Optional[str] = Field(default=None, max_length=512)
    jdbc_user: Optional[str] = Field(default=None, max_length=64)
    jdbc_password: Optional[str] = Field(default=None, max_length=512)
    enabled: bool = True


class DatasourceUpdate(BaseModel):
    name: Optional[str] = Field(default=None, max_length=128)
    host: Optional[str] = Field(default=None, max_length=128)
    hms_jdbc_url: Optional[str] = Field(default=None, max_length=512)
    hms_user: Optional[str] = Field(default=None, max_length=64)
    hms_password: Optional[str] = Field(default=None, max_length=512)
    hs2_host: Optional[str] = Field(default=None, max_length=128)
    hs2_port: Optional[int] = None
    hs2_user: Optional[str] = Field(default=None, max_length=64)
    hs2_password: Optional[str] = Field(default=None, max_length=512)
    jdbc_url: Optional[str] = Field(default=None, max_length=512)
    jdbc_user: Optional[str] = Field(default=None, max_length=64)
    jdbc_password: Optional[str] = Field(default=None, max_length=512)
    enabled: Optional[bool] = None


class DatasourceOut(BaseModel):
    id: int
    name: str
    type: str
    host: str
    hms_jdbc_url: Optional[str] = None
    hms_user: Optional[str] = None
    hs2_host: Optional[str] = None
    hs2_port: Optional[int] = None
    hs2_user: Optional[str] = None
    jdbc_url: Optional[str] = None
    jdbc_user: Optional[str] = None
    last_sync_at: Optional[datetime] = None
    enabled: bool


class DatasourceTestResult(BaseModel):
    ok: bool
    message: str
    latency_ms: Optional[int] = None


# ---------- 资产查询 ----------

class DatabaseOut(BaseModel):
    id: int
    name: str
    location: Optional[str] = None
    owner: Optional[str] = None
    comment: Optional[str] = None
    table_count: int = 0


class TableBrief(BaseModel):
    id: int
    database_id: int
    database_name: str
    name: str
    table_type: Optional[str] = None
    owner: Optional[str] = None
    comment: Optional[str] = None
    num_rows: Optional[int] = None
    total_size: Optional[int] = None
    last_ddl_time: Optional[datetime] = None


class ColumnOut(BaseModel):
    name: str
    type_name: Optional[str] = None
    ordinal: int
    comment: Optional[str] = None
    is_partition_key: bool = False


class PartitionOut(BaseModel):
    partition_spec: str
    location: Optional[str] = None
    num_rows: Optional[int] = None
    total_size: Optional[int] = None
    created_at: Optional[datetime] = None


class TableDetail(BaseModel):
    id: int
    database_name: str
    name: str
    table_type: Optional[str] = None
    location: Optional[str] = None
    input_format: Optional[str] = None
    output_format: Optional[str] = None
    serde: Optional[str] = None
    num_rows: Optional[int] = None
    num_files: Optional[int] = None
    total_size: Optional[int] = None
    create_time: Optional[datetime] = None
    last_access_time: Optional[datetime] = None
    owner: Optional[str] = None
    comment: Optional[str] = None
    view_text: Optional[str] = None
    ddl: Optional[str] = None
    columns: list[ColumnOut] = []
    partitions: list[PartitionOut] = []


class UsageStat(BaseModel):
    table_id: int
    total_count: int = 0
    last_used_at: Optional[datetime] = None
    daily: list[dict] = []  # [{"date": "2026-09-08", "count": 3}]


class LineageNode(BaseModel):
    id: int
    name: str
    database_name: str


class LineageEdge(BaseModel):
    source: str
    source_sql: Optional[str] = None
    upstream: LineageNode
    downstream: LineageNode


class LineageOut(BaseModel):
    table_id: int
    table_name: str
    upstream: list[LineageNode] = []
    downstream: list[LineageNode] = []
    edges: list[LineageEdge] = []


class BusinessLineCreate(BaseModel):
    name: str = Field(min_length=1, max_length=128)
    parent_id: Optional[int] = None
    owner: Optional[str] = None
    description: Optional[str] = None


class BusinessLineOut(BaseModel):
    id: int
    name: str
    parent_id: Optional[int] = None
    owner: Optional[str] = None
    description: Optional[str] = None
    table_count: int = 0


class SubscriptionCreate(BaseModel):
    relation: Literal["CREATED", "SUBSCRIBED", "FOLLOWED"] = "SUBSCRIBED"
