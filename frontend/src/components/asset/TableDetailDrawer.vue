<script setup lang="ts">
import { computed, ref } from 'vue'

import { getTableLineage, getTableUsage, type LineageOut, type TableDetail, type UsageStat } from '@/api/asset'
import { ASSET_TEXT } from '@/constants'

const props = defineProps<{
  table: TableDetail | null
  preview: { columns: string[]; rows: unknown[][] } | null
}>()

const visible = defineModel<boolean>({ required: true })

const activeTab = ref('overview')
const lineage = ref<LineageOut | null>(null)
const usage = ref<UsageStat | null>(null)
const lineageLoading = ref(false)

const displayName = computed(() =>
  props.table ? `${props.table.database_name}.${props.table.name}` : '',
)

async function onTabChange(name: string | number) {
  if (!props.table) return
  if (name === 'lineage' && !lineage.value) {
    lineageLoading.value = true
    try {
      lineage.value = await getTableLineage(props.table.id)
    } finally {
      lineageLoading.value = false
    }
  }
  if (name === 'usage' && !usage.value) {
    usage.value = await getTableUsage(props.table.id)
  }
}

function formatBytes(size?: number | null): string {
  if (size == null) return '-'
  if (size >= 1024 * 1024 * 1024) return `${(size / 1024 / 1024 / 1024).toFixed(2)} GB`
  if (size >= 1024 * 1024) return `${(size / 1024 / 1024).toFixed(2)} MB`
  return `${size} B`
}
</script>

<template>
  <el-drawer
    v-model="visible"
    :title="displayName"
    size="70%"
    destroy-on-close
  >
    <template v-if="table">
      <el-descriptions :column="3" border size="small">
        <el-descriptions-item :label="ASSET_TEXT.tableType">{{ table.table_type ?? '-' }}</el-descriptions-item>
        <el-descriptions-item :label="ASSET_TEXT.owner">{{ table.owner ?? '-' }}</el-descriptions-item>
        <el-descriptions-item :label="ASSET_TEXT.rows">{{ table.num_rows ?? '-' }}</el-descriptions-item>
        <el-descriptions-item :label="ASSET_TEXT.size">{{ formatBytes(table.total_size) }}</el-descriptions-item>
        <el-descriptions-item :label="'文件数'">{{ table.num_files ?? '-' }}</el-descriptions-item>
        <el-descriptions-item :label="ASSET_TEXT.comment" :span="3">{{ table.comment ?? '-' }}</el-descriptions-item>
      </el-descriptions>

      <el-tabs v-model="activeTab" style="margin-top: 16px" @tab-change="onTabChange">
        <el-tab-pane :label="ASSET_TEXT.columns" name="overview">
          <el-table :data="table.columns" size="small" max-height="400">
            <el-table-column prop="name" label="字段" min-width="140" />
            <el-table-column prop="type_name" label="类型" width="140" />
            <el-table-column prop="comment" label="注释" min-width="180" show-overflow-tooltip />
            <el-table-column label="分区键" width="80">
              <template #default="{ row }">
                <el-tag v-if="row.is_partition_key" size="small" type="warning">PK</el-tag>
              </template>
            </el-table-column>
          </el-table>
        </el-tab-pane>

        <el-tab-pane :label="ASSET_TEXT.partitions" name="partitions">
          <el-table v-if="table.partitions.length" :data="table.partitions" size="small" max-height="400">
            <el-table-column prop="partition_spec" label="分区" min-width="200" />
            <el-table-column prop="location" label="路径" min-width="260" show-overflow-tooltip />
          </el-table>
          <el-empty v-else :description="ASSET_TEXT.noData" />
        </el-tab-pane>

        <el-tab-pane :label="ASSET_TEXT.ddl" name="ddl">
          <pre class="ddl-block">{{ table.ddl || table.view_text || '-' }}</pre>
        </el-tab-pane>

        <el-tab-pane :label="ASSET_TEXT.preview" name="preview">
          <el-table v-if="preview && preview.columns.length" :data="preview.rows" size="small" max-height="400">
            <el-table-column
              v-for="(col, i) in preview.columns"
              :key="col"
              :prop="String(i)"
              :label="col"
              min-width="120"
              show-overflow-tooltip
            />
          </el-table>
          <el-empty v-else :description="ASSET_TEXT.noData" />
        </el-tab-pane>

        <el-tab-pane :label="ASSET_TEXT.lineage" name="lineage">
          <div v-loading="lineageLoading">
            <template v-if="lineage">
              <el-divider content-position="left">{{ ASSET_TEXT.upstream }}</el-divider>
              <el-tag
                v-for="node in lineage.upstream"
                :key="node.id"
                style="margin: 4px"
                type="info"
              >
                {{ node.database_name }}.{{ node.name }}
              </el-tag>
              <el-empty v-if="!lineage.upstream.length" :description="ASSET_TEXT.noData" />
              <el-divider content-position="left">{{ ASSET_TEXT.downstream }}</el-divider>
              <el-tag
                v-for="node in lineage.downstream"
                :key="node.id"
                style="margin: 4px"
                type="success"
              >
                {{ node.database_name }}.{{ node.name }}
              </el-tag>
              <el-empty v-if="!lineage.downstream.length" :description="ASSET_TEXT.noData" />
            </template>
          </div>
        </el-tab-pane>

        <el-tab-pane :label="ASSET_TEXT.usage" name="usage">
          <template v-if="usage">
            <p>总使用次数：{{ usage.total_count }}</p>
            <el-empty v-if="!usage.daily.length" :description="ASSET_TEXT.noData" />
          </template>
        </el-tab-pane>
      </el-tabs>
    </template>
  </el-drawer>
</template>

<style scoped>
.ddl-block {
  background: var(--df-bg);
  border: 1px solid var(--df-border);
  border-radius: 4px;
  padding: 12px;
  font-family: var(--df-font-mono, 'JetBrains Mono', Consolas, monospace);
  font-size: 12px;
  overflow: auto;
  max-height: 500px;
  white-space: pre-wrap;
  word-break: break-all;
}
</style>
