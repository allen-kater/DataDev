/** 数据源 Pinia store（rules/05：按领域拆分 store）。 */

import { computed, ref } from 'vue'
import { defineStore } from 'pinia'

import { listDatasources, type Datasource } from '@/api/asset'

export const useDatasourceStore = defineStore('datasource', () => {
  const datasources = ref<Datasource[]>([])
  const currentId = ref<number | null>(null)

  const current = computed<Datasource | null>(
    () => datasources.value.find((d) => d.id === currentId.value) ?? null,
  )

  async function fetchList() {
    datasources.value = await listDatasources()
  }

  function setCurrent(id: number | null) {
    currentId.value = id
  }

  return { datasources, currentId, current, fetchList, setCurrent }
})
