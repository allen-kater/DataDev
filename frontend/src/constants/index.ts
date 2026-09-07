/** UI 文案集中地：所有中文文案放本文件，组件内禁硬编码中文（rules/05、13）。 */

export const APP_NAME = 'DataDev'

export interface NavItem {
  path: string
  label: string
}

/** 左侧能力导航（单 SPA Shell） */
export const NAV_MENU: NavItem[] = [
  { path: '/asset', label: '数据资产' },
  { path: '/sql', label: 'SQL 开发' },
  { path: '/schedule', label: '任务调度' },
  { path: '/ai', label: 'AI 智能' },
  { path: '/system', label: '系统设置' },
]

/** 各能力页占位文案 */
export const VIEW_PLACEHOLDER = {
  asset: '数据资产管理：元数据采集 / 数据地图 / 血缘（Phase 2 开发中）',
  sql: 'SQL 在线开发：Monaco 编辑器 / 结果预览（Phase 3 开发中）',
  schedule: '任务调度：对接 DolphinScheduler（Phase 4 开发中）',
  ai: 'AI 智能：Text2SQL / SQL 优化 / 字典（Phase 5 开发中）',
  system: '系统设置：数据源 / 账号（后续开放）',
} as const
