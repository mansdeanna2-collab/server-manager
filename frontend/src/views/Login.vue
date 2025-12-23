<template>
  <div class="login-container">
    <!-- 背景装饰 -->
    <div class="bg-decoration">
      <div class="bg-circle circle-1" />
      <div class="bg-circle circle-2" />
      <div class="bg-circle circle-3" />
      <div class="bg-circle circle-4" />
    </div>
    
    <el-card class="login-card">
      <template #header>
        <div class="login-header">
          <div class="logo-wrapper">
            <el-icon :size="48">
              <Monitor />
            </el-icon>
          </div>
          <h2>服务器管理系统</h2>
          <p class="login-subtitle">
            安全、高效的服务器管理平台
          </p>
        </div>
      </template>
      
      <el-form
        ref="formRef"
        :model="loginForm"
        :rules="rules"
        class="login-form"
        @submit.prevent="handleLogin"
      >
        <el-form-item prop="username">
          <el-input
            v-model="loginForm.username"
            placeholder="请输入用户名"
            size="large"
            :prefix-icon="User"
            class="login-input"
            :disabled="totpRequired"
          />
        </el-form-item>
        
        <el-form-item prop="password">
          <el-input
            v-model="loginForm.password"
            type="password"
            placeholder="请输入密码"
            size="large"
            :prefix-icon="Lock"
            show-password
            class="login-input"
            :disabled="totpRequired"
            @keyup.enter="handleLogin"
          />
        </el-form-item>
        
        <!-- TOTP验证码输入框 -->
        <el-form-item
          v-if="totpRequired"
          prop="totp_code"
        >
          <el-input
            v-model="loginForm.totp_code"
            placeholder="请输入谷歌验证码"
            size="large"
            :prefix-icon="Key"
            maxlength="6"
            class="login-input totp-input"
            @keyup.enter="handleLogin"
          />
          <div class="totp-hint">
            <el-icon><InfoFilled /></el-icon>
            <span>请打开Google Authenticator输入6位验证码</span>
          </div>
        </el-form-item>
        
        <el-form-item>
          <el-button
            type="primary"
            size="large"
            class="login-btn"
            :loading="loading"
            @click="handleLogin"
          >
            <el-icon
              v-if="!loading"
              class="login-btn-icon"
            >
              <Unlock />
            </el-icon>
            {{ loading ? '登录中...' : (totpRequired ? '验证并登录' : '立即登录') }}
          </el-button>
        </el-form-item>
        
        <!-- 返回按钮（当需要TOTP验证时显示） -->
        <el-form-item v-if="totpRequired">
          <el-button
            type="default"
            size="large"
            class="back-btn"
            @click="resetTotpState"
          >
            <el-icon><Back /></el-icon>
            返回重新登录
          </el-button>
        </el-form-item>
      </el-form>
      
      <div class="login-footer">
        <div class="login-divider">
          <span>快捷登录</span>
        </div>
        <div class="login-hint">
          <el-tag
            type="info"
            effect="plain"
            round
          >
            💡 默认账号：admin / admin123
          </el-tag>
        </div>
      </div>
    </el-card>
    
    <!-- 版权信息 -->
    <div class="copyright">
      <p>© {{ new Date().getFullYear() }} Server Manager. All rights reserved.</p>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { Back, InfoFilled, Key, Lock, Monitor, Unlock, User } from '@element-plus/icons-vue'
import { authAPI } from '@/api'

const router = useRouter()
const formRef = ref(null)
const loading = ref(false)
const totpRequired = ref(false)

const loginForm = reactive({
  username: '',
  password: '',
  totp_code: ''
})

const rules = {
  username: [
    { required: true, message: '请输入用户名', trigger: 'blur' }
  ],
  password: [
    { required: true, message: '请输入密码', trigger: 'blur' }
  ],
  totp_code: [
    { required: false, message: '请输入验证码', trigger: 'blur' },
    { len: 6, message: '验证码为6位数字', trigger: 'blur' }
  ]
}

const resetTotpState = () => {
  totpRequired.value = false
  loginForm.totp_code = ''
}

const handleLogin = async () => {
  if (!formRef.value) return
  
  await formRef.value.validate(async (valid) => {
    if (valid) {
      // If TOTP is required but code is empty, don't proceed
      if (totpRequired.value && !loginForm.totp_code) {
        ElMessage.warning('请输入谷歌验证码')
        return
      }
      
      loading.value = true
      try {
        const response = await authAPI.login(loginForm)
        
        // Check if TOTP verification is required
        if (response.data.totp_required) {
          totpRequired.value = true
          ElMessage.info('请输入谷歌验证码')
          loading.value = false
          return
        }
        
        localStorage.setItem('token', response.data.token)
        localStorage.setItem('user', JSON.stringify(response.data.user))
        
        ElMessage.success('登录成功')
        router.push('/dashboard')
      } catch (error) {
        ElMessage.error(error.response?.data?.message || '登录失败')
      } finally {
        loading.value = false
      }
    }
  })
}
</script>

<style scoped>
.login-container {
  min-height: 100vh;
  display: flex;
  justify-content: center;
  align-items: center;
  position: relative;
  overflow: hidden;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}

/* 背景装饰圆 */
.bg-decoration {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  overflow: hidden;
  pointer-events: none;
}

.bg-circle {
  position: absolute;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.1);
  animation: float 15s infinite ease-in-out;
}

.circle-1 {
  width: 300px;
  height: 300px;
  top: -100px;
  left: -100px;
  animation-delay: 0s;
}

.circle-2 {
  width: 200px;
  height: 200px;
  top: 60%;
  right: -50px;
  animation-delay: -5s;
}

.circle-3 {
  width: 150px;
  height: 150px;
  bottom: -50px;
  left: 30%;
  animation-delay: -7s;
}

.circle-4 {
  width: 100px;
  height: 100px;
  top: 30%;
  left: 10%;
  animation-delay: -3s;
}

@keyframes float {
  0%, 100% {
    transform: translateY(0) rotate(0deg);
  }
  33% {
    transform: translateY(-20px) rotate(5deg);
  }
  66% {
    transform: translateY(10px) rotate(-5deg);
  }
}

/* 登录卡片 */
.login-card {
  width: 420px;
  border-radius: 20px;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
  backdrop-filter: blur(10px);
  border: none;
  position: relative;
  z-index: 1;
}

.login-card :deep(.el-card__header) {
  border-bottom: none;
  padding: 30px 30px 10px;
}

.login-card :deep(.el-card__body) {
  padding: 10px 30px 30px;
}

/* 登录头部 */
.login-header {
  display: flex;
  flex-direction: column;
  align-items: center;
  text-align: center;
}

.logo-wrapper {
  width: 80px;
  height: 80px;
  border-radius: 20px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  margin-bottom: 16px;
  box-shadow: 0 10px 30px rgba(102, 126, 234, 0.4);
}

.login-header h2 {
  margin: 0;
  color: #303133;
  font-size: 26px;
  font-weight: 600;
}

.login-subtitle {
  margin: 8px 0 0;
  color: #909399;
  font-size: 14px;
}

/* 登录表单 */
.login-form {
  margin-top: 20px;
}

.login-input :deep(.el-input__wrapper) {
  border-radius: 12px;
  box-shadow: 0 0 0 1px #e4e7ed inset;
  transition: all 0.3s;
}

.login-input :deep(.el-input__wrapper:hover) {
  box-shadow: 0 0 0 1px #c0c4cc inset;
}

.login-input :deep(.el-input__wrapper.is-focus) {
  box-shadow: 0 0 0 2px rgba(102, 126, 234, 0.3) inset;
}

/* TOTP输入框特殊样式 */
.totp-input :deep(.el-input__wrapper) {
  border-color: #67C23A;
}

.totp-input :deep(.el-input__wrapper.is-focus) {
  box-shadow: 0 0 0 2px rgba(103, 194, 58, 0.3) inset;
}

.totp-hint {
  display: flex;
  align-items: center;
  gap: 6px;
  margin-top: 8px;
  font-size: 12px;
  color: #67C23A;
}

.login-btn {
  width: 100%;
  border-radius: 12px;
  height: 48px;
  font-size: 16px;
  font-weight: 500;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border: none;
  box-shadow: 0 8px 20px rgba(102, 126, 234, 0.35);
  transition: all 0.3s;
}

.login-btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 12px 30px rgba(102, 126, 234, 0.45);
}

.login-btn:active {
  transform: translateY(0);
}

.login-btn-icon {
  margin-right: 6px;
}

.back-btn {
  width: 100%;
  border-radius: 12px;
  height: 40px;
}

/* 登录页脚 */
.login-footer {
  margin-top: 24px;
}

.login-divider {
  display: flex;
  align-items: center;
  margin-bottom: 16px;
  color: #c0c4cc;
  font-size: 12px;
}

.login-divider::before,
.login-divider::after {
  content: '';
  flex: 1;
  height: 1px;
  background: #e4e7ed;
}

.login-divider span {
  padding: 0 16px;
}

.login-hint {
  text-align: center;
}

/* 版权信息 */
.copyright {
  position: absolute;
  bottom: 24px;
  left: 0;
  right: 0;
  text-align: center;
  color: rgba(255, 255, 255, 0.6);
  font-size: 12px;
}

.copyright p {
  margin: 0;
}

/* 响应式 */
@media (max-width: 480px) {
  .login-card {
    width: 90%;
    margin: 20px;
  }
}
</style>
