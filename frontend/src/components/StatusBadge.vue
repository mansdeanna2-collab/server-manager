<template>
  <el-tag
    :type="tagType"
    :size="size"
    :effect="effect"
    :round="round"
  >
    <span
      v-if="showIcon"
      class="status-icon"
    >{{ statusIcon }}</span>
    <span class="status-text">
      {{ statusText }}
      <template v-if="errorSuffix">
        / <span class="error-text">{{ errorSuffix }}</span>
      </template>
    </span>
  </el-tag>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  status: {
    type: String,
    default: 'unknown'
  },
  detail: {
    type: String,
    default: ''
  },
  errorType: {
    type: String,
    default: ''
  },
  size: {
    type: String,
    default: 'default'
  },
  effect: {
    type: String,
    default: 'light'
  },
  round: {
    type: Boolean,
    default: false
  },
  showIcon: {
    type: Boolean,
    default: true
  }
})

const tagType = computed(() => {
  switch (props.status) {
    case 'online':
      return 'success'
    case 'offline':
      return 'danger'
    case 'checking':
      return 'warning'
    case 'auth_failed':
      return 'warning'
    case 'timeout':
      return 'info'
    case 'port_closed':
      return 'danger'
    default:
      return 'info'
  }
})

const statusText = computed(() => {
  switch (props.status) {
    case 'online':
      return '在线'
    case 'offline':
      return '离线'
    case 'checking':
      return '检查中'
    case 'auth_failed':
      return '认证失败'
    case 'timeout':
      return '超时'
    case 'port_closed':
      return '端口关闭'
    default:
      return '未知'
  }
})

const statusIcon = computed(() => {
  switch (props.status) {
    case 'online':
      return '✓'
    case 'offline':
      return '✗'
    case 'checking':
      return '⟳'
    case 'auth_failed':
      return '🔒'
    case 'timeout':
      return '⏱'
    case 'port_closed':
      return '🚫'
    default:
      return '?'
  }
})

const errorSuffix = computed(() => {
  if (props.status !== 'online') return ''
  switch (props.errorType) {
    case 'auth_failed':
      return '密码错误'
    case 'port_closed':
      return '端口关闭'
    case 'timeout':
      return '连接超时'
    case 'unreachable':
      return '主机不可达'
    case 'ssh_error':
      return 'SSH错误'
    case 'connection_error':
      return '连接错误'
    default:
      return props.errorType ? props.detail || '异常' : ''
  }
})
</script>

<style scoped>
.status-icon {
  margin-right: 4px;
}

.status-text {
  display: inline-flex;
  align-items: center;
  gap: 2px;
}

.error-text {
  color: #f56c6c;
  font-weight: 600;
}
</style>
