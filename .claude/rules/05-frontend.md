# 05 前端规则（写 frontend/** 时生效）

## 工程约束

- Vue3 Composition API（`<script setup lang="ts">`），TypeScript strict，**禁 any**
- 禁引入 Redux/Tailwind/其他 CSS 框架；样式 scoped + 全局主题变量（见 03）
- 包管理 npm；依赖锁文件 `package-lock.json` 入库

## 路由与状态

- 单 SPA Shell：左侧能力导航（数据资产 / SQL 开发 / 调度 / AI / 系统），右侧内容区
- 路由在 `src/router/` 集中定义，按能力分组，懒加载 `() => import(...)`
- Pinia store：按领域拆分（user / datasource / query / task / ai），禁单一大而全 store
- 跨组件状态进 store，局部状态留在组件内；URL 参数用 router query 而非 store

## API 调用封装

- 统一 `src/api/` 封装 axios 实例：baseURL `/api/v1`、超时、统一拦截器
- 响应处理：`code === 0` 取 `data`；`code !== 0` 用 `ElMessage` 展示 `message`，抛错终止
- 分页参数固定 `page` / `page_size`；所有请求走封装的 `request<T>()` 泛型，禁裸 axios 散落
- 长轮询（SQL 状态）用封装的 `poll()` 工具：默认间隔 2s、超时上限、取消机制（组件卸载即取消）

## 组件规范

- 公共组件放 `components/`，命名 PascalCase，props/emits 用类型定义
- 表格：统一使用 Element Plus `el-table`；状态列用 token 色（见 03），不做重复内联样式
- SQL 编辑器：Monaco，等宽字体（见 03 §字体），暴露"执行 / 格式化 / 清空"操作
- 大结果集：虚拟滚动或分页渲染，禁一次性渲染 10000 行 DOM
- 所有 UI 文案进 `src/constants/`（中英文文案集中，禁组件内硬编码中文），预留 i18n（见 13）

## 样式

- 颜色/字号/间距一律用 03 章的 CSS 变量，禁组件内写死色值
- scoped 样式 + 必要深度选择器 `:deep()`；全局样式只放 `assets/styles/`（theme.scss / reset.scss）
- 响应式：后台以 1280px 为基准，不做移动端优先

## 性能

- 路由懒加载；ECharts 按需引入
- 列表页服务端分页（page/page_size），禁前端全量渲染再过滤
- 大对象（DDL、SQL 文本）避免在 store 中深拷贝；只保留必要字段
