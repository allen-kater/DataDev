# 14 时区（全栈 +08:00）

## 约定

- **全项目统一 `Asia/Shanghai`（UTC+8）**，与宿主机和集群业务时区一致
- 存储：SQLAlchemy datetime 统一 UTC 存库（`datetime.utcnow`）；数据库本地时区差异通过连接串参数统一
- 对外（API 响应 / 前端展示 / 日志时间戳）：ISO 8601 带时区偏移，如 `2026-09-08T10:30:00+08:00`
- FastAPI：Pydantic 序列化时统一转为 +08:00 字符串输出；前端不自行做时区换算（后端给什么显示什么）

## 分界

| 层 | 时区 | 说明 |
|---|---|---|
| 后端内存/ORM | UTC | 计算与比较用 UTC，避免本地夏令时/歧义 |
| API 响应 | +08:00 | ISO 8601 带偏移 |
| 前端 | 直接展示响应时间 | 不转换 |
| 日志 | +08:00 本地时间 | `core/logging.py` 统一格式化 |
| 集群侧（Hive/DS/MySQL） | 随集群配置 | 平台不假设，探测结果确认；时间类 SQL 参数显式传时间戳字符串 |

## 边界

- Cron/调度参数：传给 DolphinScheduler 的表达式按 DS 时区（默认 GMT+8），平台展示时标注时区
- `transient_lastDdlTime` 等 HMS 时间戳按集群 MySQL 时区解析，采集器在解析层统一转 UTC 再入库
- 禁在代码中混用 `time.time()` 与 `datetime.now()` 造成时区不一致；统一走 `core/config.py` 提供的 `utcnow()` / `to_shanghai()` 工具
