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

/** 资产页文案 */
export const ASSET_TEXT = {
  databases: '数据库',
  tables: '表',
  searchPlaceholder: '搜索表名 / 注释 / 字段',
  search: '搜索',
  reset: '重置',
  tableName: '表名',
  tableType: '类型',
  owner: 'Owner',
  comment: '注释',
  rows: '行数',
  size: '大小',
  detail: '表详情',
  preview: '数据预览',
  lineage: '血缘',
  usage: '热度',
  subscribe: '订阅',
  businessLine: '业务线',
  createBusinessLine: '新建业务线',
  columns: '字段',
  partitions: '分区',
  ddl: 'DDL',
  noData: '暂无数据',
  upstream: '上游',
  downstream: '下游',
  lastSync: '最近采集',
  syncNow: '立即采集',
  testConn: '测试连接',
  addDatasource: '新增数据源',
  datasource: '数据源',
  confirmDelete: '确定删除该数据源吗？',
} as const

/** 数据源类型 */
export const DATASOURCE_TYPES = [
  { value: 'HIVE', label: 'Hive' },
  { value: 'MYSQL', label: 'MySQL' },
  { value: 'POSTGRESQL', label: 'PostgreSQL' },
] as const

/** 表类型展示映射 */
export const TABLE_TYPE_LABEL: Record<string, string> = {
  MANAGED: '内部表',
  EXTERNAL: '外部表',
  VIRTUAL_VIEW: '视图',
}
