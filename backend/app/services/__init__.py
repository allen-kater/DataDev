"""业务服务包：Phase 2+ 按模块填充。

规划（rules/02）：
- collector.py    元数据采集（APScheduler 后台任务）
- sql_executor.py SQL 执行器（ThreadPoolExecutor 跑 pyhive）
- ds_client.py    DolphinScheduler OpenAPI 客户端
- ai_service.py   AI 服务（Ollama）
- lineage.py      血缘解析（sqlglot）
"""
