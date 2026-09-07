# 08 分支 / Commit / MR 流程（涉及 git 时生效）

## 工作模式（个人单机项目）

- 默认单 `main` 分支，**直接小步提交**；功能较大或实验性改动可开 `feature/*` 临时分支，合并后删除
- 禁 `git push` 除非用户明确要求（红线）；本地提交随意，推送需用户确认
- 禁 force push / `--amend` / `reset --hard` 等破坏性操作（除非用户明确要求）

## Commit 规范

- 提交信息用 Conventional Commits 中文说明，格式：`<type>: <概述>`
- type：`feat`（新功能）/ `fix`（修 Bug）/ `chore`（杂务）/ `docs`（文档）/ `refactor`（重构）/ `test`（测试）/ `style`（格式）/ `perf`（性能）
- 一次提交一个逻辑变更；不混提交无关改动
- 提交前自查：不加 `config.yaml`、`.env`、密钥、日志、`.db`、`node_modules`、`dist` 等（见 .gitignore）

## MR / PR（如启用 GitHub 远程协作）

- 主题分支 `feature/xxx` → `main`；PR 标题同 commit 格式
- PR 描述包含：改动概述（1~3 条）、测试方式、影响面（涉及哪些表/端点/进程）
- 先跑本地测试与 lint 再提 PR

## 版本标签（可选）

- 里程碑完成打 tag：`v0.1.0` 起（SemVer）。开发期不强制

## 与 ECC 流程的关系

- 每个功能走 `plan → tdd → implement → code-review → testing → verify`（见 CLAUDE.md §7）
- code-review 通过才可 commit 并进入 testing；verifier 截图留证（Playwright）
