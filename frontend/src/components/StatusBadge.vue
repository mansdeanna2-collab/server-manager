<template>
  <el-tag :type="tagType" size="large">
    {{ statusText }}
  </el-tag>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  status: {
    type: String,
    default: 'unknown'
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
    default:
      return 'info'
  }
})

const statusText = computed(() => {
  switch (props.status) {
    case 'online':
      return 'Online'
    case 'offline':
      return 'Offline'
    case 'checking':
      return 'Checking'
    default:
      return 'Unknown'
  }
})
</script>
