<script setup lang="ts">
import { onMounted, reactive, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import type { FormInstance, FormRules } from 'element-plus'

import {
  createDatasource,
  deleteDatasource,
  syncDatasource,
  testDatasource,
  updateDatasource,
  type Datasource,
  type DatasourcePayload,
} from '@/api/asset'
import { useDatasourceStore } from '@/stores/datasource'
import { ASSET_TEXT, DATASOURCE_TYPES } from '@/constants'

const datasourceStore = useDatasourceStore()

const dialogVisible = ref(false)
const editingId = ref<number | null>(null)
const testingId = ref<number | null>(null)
const syncingId = ref<number | null>(null)
const formRef = ref<FormInstance>()

const form = reactive<DatasourcePayload>({
  name: '',
  type: 'HIVE',
  host: '',
  hms_user: '',
  hms_password: '',
  hs2_host: '',
  hs2_port: 10000,
  hs2_user: '',
  hs2_password: '',
  enabled: true,
})

const rules: FormRules = {
  name: [{ required: true, message: '请输入名称', trigger: 'blur' }],
  host: [{ required: true, message: '请输入 IP 地址', trigger: 'blur' }],
}

function openCreate() {
  editingId.value = null
  Object.assign(form, {
    name: '',
    type: 'HIVE',
    host: '',
    hms_user: '',
    hms_password: '',
    hs2_host: '',
    hs2_port: 10000,
    hs2_user: '',
    hs2_password: '',
    enabled: true,
  })
  dialogVisible.value = true
}

function openEdit(row: Datasource) {
  editingId.value = row.id
  Object.assign(form, {
    name: row.name,
    type: row.type as DatasourcePayload['type'],
    host: row.host,
    hms_user: row.hms_user ?? '',
    hms_password: '',
    hs2_host: row.hs2_host ?? '',
    hs2_port: row.hs2_port ?? 10000,
    hs2_user: row.hs2_user ?? '',
    hs2_password: '',
    enabled: row.enabled,
  })
  dialogVisible.value = true
}

async function onSubmit() {
  const valid = await formRef.value?.validate().catch(() => false)
  if (!valid) return
  const payload = { ...form }
  if (editingId.value) {
    await updateDatasource(editingId.value, payload)
    ElMessage.success('已更新')
  } else {
    await createDatasource(payload)
    ElMessage.success('已创建')
  }
  dialogVisible.value = false
  await datasourceStore.fetchList()
}

async function onRemove(row: Datasource) {
  await ElMessageBox.confirm(ASSET_TEXT.confirmDelete, '提示', { type: 'warning' })
  await deleteDatasource(row.id)
  ElMessage.success('已删除')
  await datasourceStore.fetchList()
}

async function onTest(row: Datasource) {
  testingId.value = row.id
  try {
    const r = await testDatasource(row.id)
    ElMessage[r.ok ? 'success' : 'error'](r.message)
  } finally {
    testingId.value = null
  }
}

async function onSync(row: Datasource) {
  syncingId.value = row.id
  try {
    const r = await syncDatasource(row.id)
    ElMessage.success(`采集完成：${r.tables_scanned} 张表，耗时 ${r.cost_sec}s`)
  } catch {
    ElMessage.error('采集失败，请查看日志')
  } finally {
    syncingId.value = null
    await datasourceStore.fetchList()
  }
}

function formatTime(t?: string | null): string {
  return t ? t.replace('T', ' ').slice(0, 19) : '-'
}

onMounted(() => datasourceStore.fetchList())
</script>

<template>
  <div>
    <el-card shadow="never">
      <template #header>
        <div class="header">
          <span>{{ ASSET_TEXT.datasource }}</span>
          <el-button type="primary" @click="openCreate">{{ ASSET_TEXT.addDatasource }}</el-button>
        </div>
      </template>

      <el-table :data="datasourceStore.datasources" stripe>
        <el-table-column prop="id" label="ID" width="60" />
        <el-table-column prop="name" label="名称" min-width="140" />
        <el-table-column prop="type" label="类型" width="90" />
        <el-table-column prop="host" label="地址" min-width="140" />
        <el-table-column :label="ASSET_TEXT.lastSync" min-width="160">
          <template #default="{ row }">{{ formatTime(row.last_sync_at) }}</template>
        </el-table-column>
        <el-table-column label="状态" width="90">
          <template #default="{ row }">
            <el-tag :type="row.enabled ? 'success' : 'info'" size="small">
              {{ row.enabled ? '启用' : '停用' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="260" fixed="right">
          <template #default="{ row }">
            <el-button link type="primary" :loading="testingId === row.id" @click="onTest(row)">
              {{ ASSET_TEXT.testConn }}
            </el-button>
            <el-button link type="primary" :loading="syncingId === row.id" @click="onSync(row)">
              {{ ASSET_TEXT.syncNow }}
            </el-button>
            <el-button link type="primary" @click="openEdit(row)">编辑</el-button>
            <el-button link type="danger" @click="onRemove(row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <el-dialog
      v-model="dialogVisible"
      :title="editingId ? '编辑数据源' : '新增数据源'"
      width="560px"
    >
      <el-form ref="formRef" :model="form" :rules="rules" label-width="110px">
        <el-form-item label="名称" prop="name">
          <el-input v-model="form.name" placeholder="如：Hive 集群" />
        </el-form-item>
        <el-form-item label="类型" prop="type">
          <el-select v-model="form.type" style="width: 100%">
            <el-option v-for="t in DATASOURCE_TYPES" :key="t.value" :label="t.label" :value="t.value" />
          </el-select>
        </el-form-item>
        <el-form-item label="HMS 地址" prop="host">
          <el-input v-model="form.host" placeholder="192.168.10.102" />
        </el-form-item>
        <el-form-item label="HMS 账号">
          <el-input v-model="form.hms_user" placeholder="root" />
        </el-form-item>
        <el-form-item label="HMS 密码">
          <el-input v-model="form.hms_password" type="password" show-password />
        </el-form-item>
        <el-form-item label="HS2 地址">
          <el-input v-model="form.hs2_host" placeholder="192.168.10.102" />
        </el-form-item>
        <el-form-item label="HS2 端口">
          <el-input-number v-model="form.hs2_port" :min="1" :max="65535" />
        </el-form-item>
        <el-form-item label="HS2 账号">
          <el-input v-model="form.hs2_user" placeholder="hadoop" />
        </el-form-item>
        <el-form-item label="HS2 密码">
          <el-input v-model="form.hs2_password" type="password" show-password />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="onSubmit">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<style scoped>
.header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
</style>
