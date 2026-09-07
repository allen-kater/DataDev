# DataDev —— 一站式数据开发平台（本地单机版）

> 本地数据开发平台：**管、写、调、问**。Windows 11 宿主机负责管理面，VMware 3 节点大数据集群（hadoop102/103/104）负责计算与存储。

## 平台四大能力

| 能力 | 说明 | 集群对接方式 |
|---|---|---|
| 数据资产管理 | 元数据自动采集、数据地图、表/字段检索、血缘关系、资产概览 | HMS MySQL 直读（只读）+ HS2 兜底 |
| SQL 在线开发 | Web SQL IDE（语法高亮、多数据源、执行历史、结果预览、执行计划） | HiveServer2 Thrift / JDBC |
| 任务调度 | 任务编排、依赖管理、运行监控、失败告警 | 复用 DolphinScheduler OpenAPI |
| AI 智能层 | Text2SQL、SQL 优化建议、慢 SQL 诊断、智能数据字典 | Ollama 本地模型 + 元数据 RAG |

## 目录结构

```
DataDev/
├── backend/          # FastAPI 后端（app/api、app/services、app/models、app/core）
├── frontend/         # Vue3 + Vite 前端（src/）
├── scripts/          # start.ps1 / stop.ps1 / common.ps1（进程编排）
├── data/             # SQLite 元数据库、结果集落盘、PID 文件
│   ├── results/
│   ├── uploads/
│   └── run/          # 运行期 PID（不入库）
├── logs/             # 各服务日志（运行期生成，不入库）
└── docs/             # 架构设计与环境探测记录
```

## 设计文档

- [架构设计方案](docs/架构设计方案.md)：整体架构、技术选型、原生部署方案、数据模型、风险清单、分阶段计划（Phase 0 ~ Phase 6）。
- [环境探测结果](docs/环境探测结果.md)：Phase 0 环境探测记录（版本 / 端口 / 网络 / 账号）。

## 当前进度

- [x] Phase 0 前置：仓库初始化、目录骨架
- [ ] Phase 0：环境探测（见 docs/环境探测结果.md）
- [ ] Phase 1：平台骨架（后端 health / 前端 Shell / 启动脚本 / SQLite 建表）

## 快速开始（待 Phase 1 完成）

```powershell
# 开发模式
.\scripts\start.ps1 -mode dev
# 生产模式
.\scripts\start.ps1 -mode prod
# 停止
.\scripts\stop.ps1
```

## 约束（不可违背）

1. 不使用 Docker，全部原生进程运行于 Windows 宿主机
2. 平台不做计算，所有 SQL 下发 VM 集群执行
3. 平台侧禁用 HDFS 客户端，禁止直连 DataNode RPC（仅走 HS2 / HMS MySQL / DS API 单端口协议）
4. 不部署第二套调度引擎，复用 DolphinScheduler OpenAPI
5. 平台常驻内存 ≤ 2GB（不含 Ollama 模型）
6. 不改动 VM 集群任何现有配置与数据
