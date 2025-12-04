<template>
  <el-card class="server-card" shadow="hover">
    <template #header>
      <div class="card-header">
        <span class="server-name">{{ server.ip_address }}</span>
        <StatusBadge :status="server.status" />
      </div>
    </template>
    <div class="server-info">
      <div class="info-item">
        <el-icon><Connection /></el-icon>
        <span>Port: {{ server.port }}</span>
      </div>
      <div class="info-item">
        <el-icon><User /></el-icon>
        <span>User: {{ server.username }}</span>
      </div>
      <div class="info-item" v-if="server.os_info">
        <el-icon><Monitor /></el-icon>
        <span>{{ server.os_info }}</span>
      </div>
      <div class="info-item" v-if="server.notes">
        <el-icon><Document /></el-icon>
        <span>{{ server.notes }}</span>
      </div>
    </div>
    <div class="card-actions">
      <el-button size="small" @click="$emit('view', server)">
        <el-icon><View /></el-icon>
        View
      </el-button>
      <el-button size="small" type="primary" @click="$emit('check', server)">
        <el-icon><Refresh /></el-icon>
        Check
      </el-button>
    </div>
  </el-card>
</template>

<script setup>
import StatusBadge from './StatusBadge.vue'
import { Connection, User, Monitor, Document, View, Refresh } from '@element-plus/icons-vue'

defineProps({
  server: {
    type: Object,
    required: true
  }
})

defineEmits(['view', 'check'])
</script>

<style scoped>
.server-card {
  margin-bottom: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.server-name {
  font-weight: bold;
  font-size: 16px;
}

.server-info {
  margin: 15px 0;
}

.info-item {
  display: flex;
  align-items: center;
  margin-bottom: 8px;
  color: #606266;
}

.info-item .el-icon {
  margin-right: 8px;
}

.card-actions {
  display: flex;
  gap: 10px;
  justify-content: flex-end;
}
</style>
