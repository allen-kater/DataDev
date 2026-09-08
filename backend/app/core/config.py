"""配置加载：backend/config.yaml + 环境变量注入密码字段。

规则（rules/04）：所有环境相关配置走本层，业务代码禁止直接读环境变量。
密码字段一律经 `xxx_env` 声明的环境变量注入，config.yaml 只存占位说明。
"""

import os
from datetime import datetime, timedelta, timezone
from functools import lru_cache
from pathlib import Path

import yaml
from pydantic import BaseModel

BACKEND_DIR = Path(__file__).resolve().parents[2]
PROJECT_DIR = BACKEND_DIR.parent
DATA_DIR = PROJECT_DIR / "data"
CONFIG_PATH = BACKEND_DIR / "config.yaml"

DEFAULT_DB_URL = f"sqlite+aiosqlite:///{(PROJECT_DIR / 'data' / 'dataflow.db').as_posix()}"

_SHANGHAI = timezone(timedelta(hours=8))


def utcnow() -> datetime:
    """当前 UTC 时间（rules/14：存储/比较统一 UTC）。"""
    return datetime.now(timezone.utc)


def to_shanghai(dt: datetime) -> datetime:
    """任意 aware/naive datetime 转 +08:00；naive 视为 UTC。"""
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(_SHANGHAI)


class DatabaseConfig(BaseModel):
    url: str = DEFAULT_DB_URL
    echo: bool = False


class HMSConfig(BaseModel):
    host: str = "192.168.10.102"
    port: int = 3306
    database: str = "metastore"
    user: str = "root"
    password_env: str = "DATAFLOW_HMS_PASSWORD"

    @property
    def password(self) -> str:
        return os.getenv(self.password_env, "")


class HS2Config(BaseModel):
    host: str = "192.168.10.102"
    port: int = 10000
    user: str = "hadoop"
    password_env: str = "DATAFLOW_HS2_PASSWORD"

    @property
    def password(self) -> str:
        return os.getenv(self.password_env, "")


class DSConfig(BaseModel):
    base_url: str = "http://192.168.10.102:12345"
    user: str = "admin"
    password_env: str = "DATAFLOW_DS_PASSWORD"

    @property
    def password(self) -> str:
        return os.getenv(self.password_env, "")


class OllamaConfig(BaseModel):
    base_url: str = "http://127.0.0.1:11434"
    model: str = "qwen2.5-coder:7b"
    timeout_sec: int = 120


class Settings(BaseModel):
    app_name: str = "DataDev"
    app_version: str = "0.1.0"
    host: str = "127.0.0.1"
    port: int = 8000
    debug: bool = False
    static_dir: str = str(BACKEND_DIR / "app" / "static")
    database: DatabaseConfig = DatabaseConfig()
    hms: HMSConfig = HMSConfig()
    hs2: HS2Config = HS2Config()
    ds: DSConfig = DSConfig()
    ollama: OllamaConfig = OllamaConfig()


@lru_cache
def get_settings() -> Settings:
    """加载 config.yaml（不存在时使用默认值），返回 pydantic 配置对象。"""
    raw: dict = {}
    if CONFIG_PATH.exists():
        loaded = yaml.safe_load(CONFIG_PATH.read_text(encoding="utf-8"))
        if isinstance(loaded, dict):
            raw = loaded
    return Settings.model_validate(raw)
