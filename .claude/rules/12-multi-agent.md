# 12 多 Agent 协作（ECC）

> 适用：开启多 Agent / Claude Code Team 模式时。个人单机环境可退化为"单主会话 + 顺序执行"，但阶段顺序不变。

## 强制阶段顺序（任一失败即停止，不跳步）

```
plan → tdd → implement → code-review → testing → verify
```

## 角色委派表

| 场景 | 委派角色 | 输入 → 输出 |
|---|---|---|
| 新功能 / 复杂改动 | planner | 需求 → 任务拆分 + 风险清单（对齐方案契约） |
| 新功能 / 修 Bug 起步 | tdd-guide | 功能 → 红绿测试先行 |
| 改 backend/frontend | 主会话 / impl | 任务 → 代码（遵守 rules/01-06） |
| 刚改完代码 | code-reviewer | diff → 规范/安全/API 形状审查结论 |
| 核心链路 | tester | 代码 → pytest/Vitest 结果 |
| 交付验证 | verifier | 应用 → Playwright 截图留证 |

## 并行与收敛

- 无依赖子任务可并行多 Agent（如"数据源 CRUD"与"SQL 执行器"可并行）；有依赖（如先表设计后采集器）必须串行
- 每功能建 `ecc-{feature}` 会话/Team，结束清理；**不并行超过 3~4 个**（本地资源）
- 主会话负责汇总各 Agent 产出、保持与 `CLAUDE.md` / 方案一致，防止各 Agent 各自为政

## 上下文纪律

- 每个 Agent 开场必须读：`CLAUDE.md` + 相关 rules（按角色路径，见 00）+ 涉及的设计章节
- Agent 产出必须回写：新增端点 → CLAUDE.md §5 + rules/06；新表 → 方案第 7 章（走 ADR）

## 可观测（可选）

- `scripts/tmux-ecc.sh` 类工具仅用于观察输出；主会话仍在前台跑，不做黑盒
