<template>
  <el-form :model="form" :rules="rules" ref="formRef" label-width="120px">
    <el-form-item label="IP地址" prop="ip_address">
      <el-input v-model="form.ip_address" placeholder="例如：192.168.1.100" />
    </el-form-item>
    
    <el-form-item label="端口" prop="port">
      <el-input-number v-model="form.port" :min="1" :max="65535" />
    </el-form-item>
    
    <el-form-item label="用户名" prop="username">
      <el-input v-model="form.username" placeholder="例如：root" />
    </el-form-item>
    
    <el-form-item label="密码" prop="password">
      <el-input
        v-model="form.password"
        type="password"
        placeholder="服务器密码"
        show-password
      />
    </el-form-item>
    
    <el-form-item label="备注">
      <el-input
        v-model="form.notes"
        type="textarea"
        :rows="3"
        placeholder="关于该服务器的可选备注"
      />
    </el-form-item>
    
    <el-form-item>
      <el-button type="primary" @click="submitForm">
        {{ isEdit ? '更新' : '新增' }}服务器
      </el-button>
      <el-button @click="$emit('cancel')">取消</el-button>
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
    { required: true, message: '请输入IP地址', trigger: 'blur' }
  ],
  port: [
    { required: true, message: '请输入端口', trigger: 'blur' }
  ],
  username: [
    { required: true, message: '请输入用户名', trigger: 'blur' }
  ],
  password: [
    { required: true, message: '请输入密码', trigger: 'blur' }
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
