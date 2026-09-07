/** 后端统一响应 / 分页契约（与 rules/06 对齐）。 */

export interface ApiResponse<T = unknown> {
  code: number
  message: string
  data: T | null
}

export interface PageData<T> {
  total: number
  page: number
  page_size: number
  items: T[]
}
