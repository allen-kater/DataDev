<script setup lang="ts">
import { onMounted, ref } from 'vue'

import {
  getTableDetail,
  listDatabases,
  previewTable,
  searchTables,
  subscribeTable,
  type DatabaseInfo,
  type TableBrief,
  type TableDetail,
} from '@/api/asset'
import { useDatasourceStore } from '@/stores/datasource'
import { ASSET_TEXT, TABLE_TYPE_LABEL } from '@/constants'
import TableDetailDrawer from '@/components/asset/TableDetailDrawer.vue'
import { ElMessage } from 'element-plus'

const datasourceStore = useDatasourceStore()

const databases = ref<DatabaseInfo[]>([])
const currentDbId = ref<number | null>(null)
const tables = ref<TableBrief[]>([])
const total = ref(0)
const keyword = ref('')
const page = ref(1)
const pageSize = ref(20)
const loading = ref(false)

const detailVisible = ref(false)
const currentTable = ref<TableDetail | null>(null)
const previewData = ref<{ columns: string[]; rows: unknown[][] } | null>(null)

async function loadDatabases() {
  databases.value = await listDatabases(datasourceStore.currentId ?? undefined)
}

async function loadTables() {
  loading.value = true
  try {
    const data = await searchTables({
      db_id: currentDbId.value ?? undefined,
      keyword: keyword.value || undefined,
      page: page.value,
      page_size: pageSize.value,
    })
    tables.value = data.items
    total.value = data.total
  } finally {
    loading.value = false
  }
}

async function onDbClick(data: DatabaseInfo) {
  currentDbId.value = data.id
  page.value = 1
  await loadTables()
}

async function onSearch() {
  page.value = 1
  await loadTables()
}

function onReset() {
  keyword.value = ''
  currentDbId.value = null
  page.value = 1
  loadTables()
}

async function onRowClick(row: TableBrief) {
  const [detail, preview] = await Promise.all([
    getTableDetail(row.id),
    previewTable(row.id, 20).catch(() => null),
  ])
  currentTable.value = detail
  previewData.value = preview
  detailVisible.value = true
}

async function onSubscribe(row: TableBrief) {
  await subscribeTable(row.id)
  ElMessage.success('已订阅')
}

function formatSize(size?: number | null): string {
  if (size == null) return '-'
  if (size >= 1024 * 1024 * 1024) return `${(size / 1024 / 1024 / 1024).toFixed(2)} GB`
  if (size >= 1024 * 1024) return `${(size / 1024 / 1024).toFixed(2)} MB`
  if (size >= 1024) return `${(size / 1024).toFixed(2)} KB`
  return `${size} B`
}

onMounted(async () => {
  await datasourceStore.fetchList()
  await loadDatabases()
  await loadTables()
})
</script>

<template>
  <div class="asset-page">
    <el-row :gutter="12">
      <el-col :span="5">
        <el-card shadow="never" class="panel">
          <template #header>
            <span>{{ ASSET_TEXT.databases }}</span>
          </template>
          <el-tree
            :data="databases"
            :props="{ label: 'name', children: 'children' }"
            node-key="id"
            highlight-current
            @node-click="onDbClick"
          >
            <template #default="{ data }">
              <span class="db-node">
                <span>{{ data.name }}</span>
                <el-tag size="small" type="info">{{ data.table_count }}</el-tag>
              </span>
            </template>
          </el-tree>
        </el-card>
      </el-col>

      <el-col :span="19">
        <el-card shadow="never" class="panel">
          <template #header>
            <div class="toolbar">
              <span>{{ ASSET_TEXT.tables }}</span>
              <div class="search-bar">
                <el-input
                  v-model="keyword"
                  :placeholder="ASSET_TEXT.searchPlaceholder"
                  clearable
                  style="width: 280px"
                  @keyup.enter="onSearch"
                />
                <el-button type="primary" @click="onSearch">{{ ASSET_TEXT.search }}</el-button>
                <el-button @click="onReset">{{ ASSET_TEXT.reset }}</el-button>
              </div>
            </div>
          </template>

          <el-table
            v-loading="loading"
            :data="tables"
            highlight-current-row
            @row-click="onRowClick"
          >
            <el-table-column prop="database_name" :label="ASSET_TEXT.databases" width="120" />
            <el-table-column prop="name" :label="ASSET_TEXT.tableName" min-width="200">
              <template #default="{ row }">
                <span class="table-name">{{ row.name }}</span>
              </template>
            </el-table-column>
            <el-table-column :label="ASSET_TEXT.tableType" width="90">
              <template #default="{ row }">
                <el-tag size="small" :type="row.table_type === 'VIRTUAL_VIEW' ? 'warning' : 'primary'">
                  {{ TABLE_TYPE_LABEL[row.table_type ?? ''] ?? row.table_type }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="owner" :label="ASSET_TEXT.owner" width="100" />
            <el-table-column prop="comment" :label="ASSET_TEXT.comment" min-width="160" show-overflow-tooltip />
            <el-table-column :label="ASSET_TEXT.rows" width="90">
              <template #default="{ row }">{{ row.num_rows ?? '-' }}</template>
            </el-table-column>
            <el-table-column :label="ASSET_TEXT.size" width="90">
              <template #default="{ row }">{{ formatSize(row.total_size) }}</template>
            </el-table-column>
            <el-table-column width="80" fixed="right">
              <template #default="{ row }">
                <el-button link type="primary" @click.stop="onSubscribe(row)">{{ ASSET_TEXT.subscribe }}</el-button>
              </template>
            </el-table-column>
          </el-table>

          <el-pagination
            v-model:current-page="page"
            v-model:page-size="pageSize"
            :total="total"
            layout="total, prev, pager, next"
            style="margin-top: 12px; justify-content: flex-end"
            @current-change="loadTables"
          />
        </el-card>
      </el-col>
    </el-row>

    <TableDetailDrawer
      v-model="detailVisible"
      :table="currentTable"
      :preview="previewData"
    />
  </div>
</template>

<style scoped>
.asset-page {
  min-height: 100%;
}

.panel {
  min-height: calc(100vh - 96px);
}

.db-node {
  display: flex;
  justify-content: space-between;
  align-items: center;
  width: 100%;
  padding-right: 8px;
}

.toolbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.search-bar {
  display: flex;
  gap: 8px;
}

.table-name {
  font-weight: 500;
  color: var(--df-primary);
}
</style>
