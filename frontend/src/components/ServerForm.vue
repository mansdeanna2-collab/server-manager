<template>
  <el-form :model="form" :rules="rules" ref="formRef" label-width="120px">
    <el-form-item label="IP Address" prop="ip_address">
      <el-input v-model="form.ip_address" placeholder="e.g., 192.168.1.100" />
    </el-form-item>
    
    <el-form-item label="Port" prop="port">
      <el-input-number v-model="form.port" :min="1" :max="65535" />
    </el-form-item>
    
    <el-form-item label="Username" prop="username">
      <el-input v-model="form.username" placeholder="e.g., root" />
    </el-form-item>
    
    <el-form-item label="Password" prop="password">
      <el-input
        v-model="form.password"
        type="password"
        placeholder="Server password"
        show-password
      />
    </el-form-item>
    
    <el-form-item label="Notes">
      <el-input
        v-model="form.notes"
        type="textarea"
        :rows="3"
        placeholder="Optional notes about this server"
      />
    </el-form-item>
    
    <el-form-item>
      <el-button type="primary" @click="submitForm">
        {{ isEdit ? 'Update' : 'Add' }} Server
      </el-button>
      <el-button @click="$emit('cancel')">Cancel</el-button>
    </el-form-item>
  </el-form>
</template>

<script setup>
import { ref, reactive, watch } from 'vue'

const props = defineProps({
  server: {
    type: Object,
    default: null
  },
  isEdit: {
    type: Boolean,
    default: false
  }
})

const emit = defineEmits(['submit', 'cancel'])

const formRef = ref(null)

const form = reactive({
  ip_address: '',
  port: 22,
  username: '',
  password: '',
  notes: ''
})

const rules = {
  ip_address: [
    { required: true, message: 'Please input IP address', trigger: 'blur' }
  ],
  port: [
    { required: true, message: 'Please input port', trigger: 'blur' }
  ],
  username: [
    { required: true, message: 'Please input username', trigger: 'blur' }
  ],
  password: [
    { required: true, message: 'Please input password', trigger: 'blur' }
  ]
}

// Watch for server prop changes (for edit mode)
watch(() => props.server, (newServer) => {
  if (newServer) {
    form.ip_address = newServer.ip_address
    form.port = newServer.port
    form.username = newServer.username
    form.password = '' // Don't populate password for security
    form.notes = newServer.notes || ''
  }
}, { immediate: true })

const submitForm = async () => {
  if (!formRef.value) return
  
  await formRef.value.validate((valid) => {
    if (valid) {
      emit('submit', { ...form })
    }
  })
}
</script>
