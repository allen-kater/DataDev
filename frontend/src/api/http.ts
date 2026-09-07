/** axios 统一封装：baseURL /api/v1、超时、code===0 取 data、错误统一 ElMessage。 */

import axios, { type AxiosRequestConfig, type AxiosResponse } from 'axios'
import { ElMessage } from 'element-plus'

import type { ApiResponse } from './types'

const http = axios.create({
  baseURL: '/api/v1',
  timeout: 30000,
})

http.interceptors.response.use(
  (resp: AxiosResponse<unknown>) => {
    const body = resp.data
    if (body !== null && typeof body === 'object' && 'code' in body) {
      const apiResp = body as ApiResponse<unknown>
      if (apiResp.code === 0) {
        return apiResp.data as unknown as AxiosResponse
      }
      ElMessage.error(apiResp.message || '请求失败')
      return Promise.reject(new Error(apiResp.message || '请求失败'))
    }
    return body as unknown as AxiosResponse
  },
  (error: unknown) => {
    const msg = error instanceof Error ? error.message : '网络错误'
    ElMessage.error(msg)
    return Promise.reject(error)
  },
)

/** 统一请求入口：返回值 T 为后端 data 字段类型（拦截器已解包）。 */
export function request<T>(config: AxiosRequestConfig): Promise<T> {
  return http.request(config) as unknown as Promise<T>
}
