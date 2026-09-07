<script setup lang="ts">
import { VIEW_PLACEHOLDER } from '@/constants'
</script>

<template>
  <el-card shadow="never">
    <el-empty :description="VIEW_PLACEHOLDER.ai" />
  </el-card>
</template>
