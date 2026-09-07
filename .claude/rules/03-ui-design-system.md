# 03 UI 设计系统（写前端时生效）

> 适用：`frontend/**`。UI 库为 Element Plus，主题通过 CSS 变量覆盖，禁散落硬编码颜色/字号。

## 设计基调

数据密集型后台（参考 DolphinScheduler / EasyData 类产品）：**浅色为主、信息密度高、中性色层级清晰、主色克制**。默认浅色主题；深色为可选增强（Phase 6，见 13 章）。

## 配色

| Token | 值 | 用途 |
|---|---|---|
| `--brand-primary` | `#3370FF` | 主色：主按钮、选中态、链接 |
| `--brand-hover` | `#4C7FFF` | 主色 hover |
| `--brand-active` | `#2B5EE8` | 主色 active / pressed |
| `--brand-light` | `#E8F0FF` | 主色浅底：标签、选中行底色 |
| `--success` | `#18A058` | 成功态：任务 SUCCESS |
| `--warning` | `#F0A020` | 警告态：运行中/待重试 |
| `--danger` | `#D03050` | 失败态：FAILED、错误 |
| `--text-1` | `#1F2329` | 主文本 |
| `--text-2` | `#646A73` | 次级文本 |
| `--text-3` | `#8F959E` | 占位/禁用文本 |
| `--border-color` | `#E5E6EB` | 边框 |
| `--bg-page` | `#F5F7FA` | 页面底色 |
| `--bg-card` | `#FFFFFF` | 卡片/表格底色 |

> 上述 token 同时映射到 Element Plus 变量（`--el-color-primary` 等），在 `assets/styles/theme.scss` 中统一覆盖，组件内不再写死色值。

## 字体

| 场景 | 字体栈 |
|---|---|
| 中文正文/UI | `"Segoe UI", "PingFang SC", "Microsoft YaHei", "Helvetica Neue", Arial, sans-serif` |
| 英文/数字 | `"Segoe UI", "Helvetica Neue", Arial, sans-serif` |
| 代码 / SQL 编辑器 / 日志 | `"JetBrains Mono", "Cascadia Code", Consolas, "Courier New", monospace`（Monaco 内配置 `fontFamily`，字号 14px） |

## 字号与间距

| Token | 值 | 用途 |
|---|---|---|
| `--font-xs` | 12px | 辅助文本、表头 |
| `--font-sm` | 13px | 次级信息 |
| `--font-md` | 14px | 正文（默认） |
| `--font-lg` | 16px | 页面标题 |
| `--font-xl` | 20px | 弹窗标题 |
| `--radius-sm` | 4px | 标签/输入框 |
| `--radius-md` | 8px | 卡片/弹窗 |
| 间距 | 4 的倍数（4/8/12/16/24） | 统一栅格节奏 |

## 通用规则

- 行高 1.5；正文颜色用 `--text-1`，次级用 `--text-2`，不用纯黑 `#000`
- 表格：密度适中（行高默认 40px），表头背景 `--bg-page`，文本 `--text-2`
- 状态色只用于状态（任务/连接/同步），不在普通 UI 元素滥用
- 长 SQL/结果集区域固定等宽字体；结果集超宽用横向滚动，不做压缩
- 所有 UI 文案放 `frontend/src/constants/`（i18n 预留，见 13）
- 图标统一 Element Plus 内置 `el-icon`，不引入图标库
