# 13 i18n / 主题

## 当前状态（务实声明）

- 本项目为个人自用，**UI 语言固定简体中文**，暂不做多语言运行时切换
- 但文案必须**集中管理**（为未来 i18n 预留结构，不提前引入 vue-i18n 依赖）

## 文案集中规则

- 所有 UI 文案放 `frontend/src/constants/`：
  - `constants/messages.ts` —— 提示/错误文案
  - `constants/labels.ts` —— 表单/表格/按钮文案
  - `constants/status.ts` —— 状态映射（`pending→运行中` 等，与后端枚举对齐）
- 组件内**禁硬编码中文字符串**；拼接型文案用模板字符串写进 constants
- 后端错误 `message` 返回中文（API 契约 06），前端直接展示，不再二次映射

## 主题

- 浅色为唯一默认主题（03 章 token）；深色主题列为 **Phase 6 可选增强**，实现前走 ADR
- 主题切换预留：token 收敛在 `assets/styles/theme.scss`（CSS 变量），未来深色只需换变量值，组件不动
- 禁在组件内散落色值（见 03）

## 文案审核

- 状态枚举（success/failed/pending/running）前后端一致，前端 constants 映射表为唯一展示来源
- 新增枚举状态时：后端 rules/06 状态列表 + 前端 constants/status.ts + 方案第 7 章同步更新
