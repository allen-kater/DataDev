/** 数据资产 API 封装（rules/05：统一走 request<T>()）。 */

import { request } from './http'
import type { PageData } from './types'

/** 数据源 */
export interface Datasource {
  id: number
  name: string
  type: string
  host: string
  hms_jdbc_url?: string | null
  hms_user?: string | null
  hs2_host?: string | null
  hs2_port?: number | null
  hs2_user?: string | null
  jdbc_url?: string | null
  jdbc_user?: string | null
  last_sync_at?: string | null
  enabled: boolean
}

export interface DatasourcePayload {
  name: string
  type: 'HIVE' | 'MYSQL' | 'POSTGRESQL'
  host: string
  hms_jdbc_url?: string
  hms_user?: string
  hms_password?: string
  hs2_host?: string
  hs2_port?: number
  hs2_user?: string
  hs2_password?: string
  jdbc_url?: string
  jdbc_user?: string
  jdbc_password?: string
  enabled?: boolean
}

export interface TestResult {
  ok: boolean
  message: string
  latency_ms?: number | null
}

export interface SyncResult {
  tables_scanned: number
  cost_sec: number
  status: string
  error_msg?: string | null
}

export function listDatasources(): Promise<Datasource[]> {
  return request<Datasource[]>({ url: '/datasources', method: 'get' })
}

export function createDatasource(payload: DatasourcePayload): Promise<{ id: number }> {
  return request<{ id: number }>({ url: '/datasources', method: 'post', data: payload })
}

export function updateDatasource(id: number, payload: Partial<DatasourcePayload>): Promise<{ id: number }> {
  return request<{ id: number }>({ url: `/datasources/${id}`, method: 'put', data: payload })
}

export function deleteDatasource(id: number): Promise<{ id: number }> {
  return request<{ id: number }>({ url: `/datasources/${id}`, method: 'delete' })
}

export function testDatasource(id: number): Promise<TestResult> {
  return request<TestResult>({ url: `/datasources/${id}/test`, method: 'post' })
}

export function syncDatasource(id: number): Promise<SyncResult> {
  return request<SyncResult>({ url: `/datasources/${id}/sync`, method: 'post' })
}

/** 资产 */
export interface DatabaseInfo {
  id: number
  name: string
  location?: string | null
  owner?: string | null
  comment?: string | null
  table_count: number
}

export interface TableBrief {
  id: number
  database_id: number
  database_name: string
  name: string
  table_type?: string | null
  owner?: string | null
  comment?: string | null
  num_rows?: number | null
  total_size?: number | null
}

export interface ColumnInfo {
  name: string
  type_name?: string | null
  ordinal: number
  comment?: string | null
  is_partition_key: boolean
}

export interface PartitionInfo {
  partition_spec: string
  location?: string | null
  num_rows?: number | null
  total_size?: number | null
  created_at?: string | null
}

export interface TableDetail {
  id: number
  database_name: string
  name: string
  table_type?: string | null
  location?: string | null
  input_format?: string | null
  output_format?: string | null
  serde?: string | null
  num_rows?: number | null
  num_files?: number | null
  total_size?: number | null
  create_time?: string | null
  last_access_time?: string | null
  owner?: string | null
  comment?: string | null
  view_text?: string | null
  ddl?: string | null
  columns: ColumnInfo[]
  partitions: PartitionInfo[]
}

export interface UsageStat {
  table_id: number
  total_count: number
  last_used_at?: string | null
  daily: { date: string; count: number }[]
}

export interface LineageNode {
  id: number
  name: string
  database_name: string
}

export interface LineageOut {
  table_id: number
  table_name: string
  upstream: LineageNode[]
  downstream: LineageNode[]
  edges: {
    source: string
    source_sql?: string | null
    upstream: LineageNode
    downstream: LineageNode
  }[]
}

export function listDatabases(datasourceId?: number): Promise<DatabaseInfo[]> {
  return request<DatabaseInfo[]>({
    url: '/asset/databases',
    method: 'get',
    params: datasourceId ? { datasource_id: datasourceId } : {},
  })
}

export function searchTables(params: {
  db_id?: number
  datasource_id?: number
  keyword?: string
  page?: number
  page_size?: number
}): Promise<PageData<TableBrief>> {
  return request<PageData<TableBrief>>({ url: '/asset/tables', method: 'get', params })
}

export function getTableDetail(id: number): Promise<TableDetail> {
  return request<TableDetail>({ url: `/asset/tables/${id}`, method: 'get' })
}

export function getTableUsage(id: number): Promise<UsageStat> {
  return request<UsageStat>({ url: `/asset/tables/${id}/usage`, method: 'get' })
}

export function getTableLineage(id: number): Promise<LineageOut> {
  return request<LineageOut>({ url: `/asset/tables/${id}/lineage`, method: 'get' })
}

export function previewTable(id: number, limit = 20): Promise<{ columns: string[]; rows: unknown[][]; truncated: boolean }> {
  return request<{ columns: string[]; rows: unknown[][]; truncated: boolean }>({
    url: `/asset/tables/${id}/preview`,
    method: 'post',
    params: { limit },
  })
}

export function subscribeTable(id: number, relation = 'SUBSCRIBED'): Promise<{ table_id: number }> {
  return request<{ table_id: number }>({ url: `/asset/tables/${id}/subscribe`, method: 'post', data: { relation } })
}

export function listSubscriptions(): Promise<
  { id: number; table_id: number; relation: string; created_at: string; table_name: string; database_name: string }[]
> {
  return request({ url: '/asset/subscriptions', method: 'get' })
}

export function listBusinessLines(): Promise<
  { id: number; name: string; parent_id?: number | null; owner?: string | null; description?: string | null; table_count: number }[]
> {
  return request({ url: '/asset/business-lines', method: 'get' })
}

export function createBusinessLine(payload: { name: string; description?: string }): Promise<{ id: number }> {
  return request<{ id: number }>({ url: '/asset/business-lines', method: 'post', data: payload })
}
