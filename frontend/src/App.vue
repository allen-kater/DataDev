<script setup lang="ts">
import { computed } from 'vue'
import { useRoute } from 'vue-router'

import { APP_NAME, NAV_MENU } from '@/constants'

const route = useRoute()
const activeMenu = computed(() => {
  const first = String(route.path.split('/')[1] ?? '')
  return `/${first}`
})
</script>

<template>
  <el-container class="app-shell">
    <el-aside width="220px" class="app-aside">
      <div class="app-logo">{{ APP_NAME }}</div>
      <el-menu :default-active="activeMenu" router class="app-menu">
        <el-menu-item v-for="item in NAV_MENU" :key="item.path" :index="item.path">
          <span>{{ item.label }}</span>
        </el-menu-item>
      </el-menu>
    </el-aside>

    <el-container>
      <el-main class="app-main">
        <router-view />
      </el-main>
    </el-container>
  </el-container>
</template>

<style scoped>
.app-shell {
  height: 100%;
}

.app-aside {
  border-right: 1px solid var(--df-border);
  background-color: #fff;
}

.app-logo {
  height: 56px;
  line-height: 56px;
  padding-left: 20px;
  font-size: 18px;
  font-weight: 600;
  color: var(--df-primary);
  border-bottom: 1px solid var(--df-border);
}

.app-menu {
  border-right: none;
}

.app-main {
  background-color: var(--df-bg);
  padding: 16px;
}
</style>
