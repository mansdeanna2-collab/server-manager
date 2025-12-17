<template>
  <div class="page-container">
    <el-container>
      <el-header class="header-container">
        <div class="header-logo">
          <el-icon :size="30">
            <Monitor />
          </el-icon>
          <h2>服务器管理</h2>
        </div>
        <el-menu
          mode="horizontal"
          :default-active="activeMenu"
          background-color="transparent"
          text-color="#fff"
          active-text-color="#fff"
          class="header-menu"
          @select="handleMenuSelect"
        >
          <el-menu-item index="/dashboard">
            <el-icon><Odometer /></el-icon>
            仪表盘
          </el-menu-item>
          <el-menu-item index="/servers">
            <el-icon><OfficeBuilding /></el-icon>
            服务器
          </el-menu-item>
          <el-sub-menu index="main-program">
            <template #title>
              <el-icon><Setting /></el-icon>
              主程序功能
            </template>
            <el-menu-item index="/information-query">
              <el-icon><Search /></el-icon>
              信息查询
            </el-menu-item>
            <el-menu-item index="/system-backup">
              <el-icon><FolderOpened /></el-icon>
              系统备份
            </el-menu-item>
            <el-menu-item index="/system-settings">
              <el-icon><Tools /></el-icon>
              系统设置
            </el-menu-item>
          </el-sub-menu>
        </el-menu>
        <el-dropdown @command="handleCommand">
          <span class="user-dropdown">
            <el-icon><User /></el-icon>
            {{ currentUser?.username || '管理员' }}
            <el-icon><ArrowDown /></el-icon>
          </span>
          <template #dropdown>
            <el-dropdown-menu>
              <el-dropdown-item command="changePassword">
                修改密码
              </el-dropdown-item>
              <el-dropdown-item command="logout">
                退出登录
              </el-dropdown-item>
            </el-dropdown-menu>
          </template>
        </el-dropdown>
      </el-header>
      
      <el-main class="main-content">
        <div class="content-wrapper">
          <el-card class="settings-card">
            <template #header>
              <div class="card-header">
                <div class="card-header-title">
                  <el-icon
                    class="card-header-icon"
                    :size="20"
                  >
                    <Tools />
                  </el-icon>
                  <span>系统设置</span>
                </div>
                <div class="card-header-buttons">
                  <el-button
                    type="default"
                    @click="goBack"
                  >
                    <el-icon><Back /></el-icon>
                    返回仪表盘
                  </el-button>
                </div>
              </div>
            </template>
            
            <div class="settings-content">
              <el-row :gutter="24">
                <!-- 左侧垂直菜单 -->
                <el-col :span="6">
                  <el-menu
                    :default-active="activeSettingMenu"
                    class="settings-menu"
                    @select="handleSettingMenuSelect"
                  >
                    <el-menu-item index="whitelist">
                      <el-icon><Lock /></el-icon>
                      <span>登录白名单</span>
                    </el-menu-item>
                    <el-menu-item index="ssl">
                      <el-icon><Key /></el-icon>
                      <span>SSL设置</span>
                    </el-menu-item>
                    <el-menu-item index="logs">
                      <el-icon><Document /></el-icon>
                      <span>查看系统日志</span>
                    </el-menu-item>
                  </el-menu>
                </el-col>
                
                <!-- 右侧内容区 -->
                <el-col :span="18">
                  <!-- 登录白名单设置 -->
                  <div
                    v-if="activeSettingMenu === 'whitelist'"
                    class="setting-panel"
                  >
                    <h3 class="setting-title">
                      <el-icon><Lock /></el-icon>
                      登录白名单设置
                    </h3>
                    <el-form
                      :model="whitelistForm"
                      label-width="120px"
                    >
                      <el-form-item label="启用白名单">
                        <el-switch v-model="whitelistForm.enabled" />
                        <span class="form-tip">启用后，只有白名单中的IP地址可以登录系统</span>
                      </el-form-item>
                      <el-form-item label="IP白名单">
                        <div class="ip-list-container">
                          <div
                            v-for="(ip, index) in whitelistForm.ip_list"
                            :key="index"
                            class="ip-item"
                          >
                            <el-input
                              v-model="whitelistForm.ip_list[index]"
                              placeholder="请输入IP地址，如: 192.168.1.1"
                            />
                            <el-button
                              type="danger"
                              :icon="Delete"
                              circle
                              @click="removeWhitelistIp(index)"
                            />
                          </div>
                          <el-button
                            type="primary"
                            @click="addWhitelistIp"
                          >
                            <el-icon><Plus /></el-icon>
                            添加IP
                          </el-button>
                        </div>
                      </el-form-item>
                      <el-form-item>
                        <el-button
                          type="primary"
                          :loading="savingSettings"
                          @click="saveWhitelistSettings"
                        >
                          保存设置
                        </el-button>
                      </el-form-item>
                    </el-form>
                  </div>
                  
                  <!-- SSL设置 -->
                  <div
                    v-if="activeSettingMenu === 'ssl'"
                    class="setting-panel"
                  >
                    <h3 class="setting-title">
                      <el-icon><Key /></el-icon>
                      SSL设置
                    </h3>
                    <el-form
                      :model="sslForm"
                      label-width="120px"
                    >
                      <el-form-item label="启用SSL">
                        <el-switch v-model="sslForm.enabled" />
                        <span class="form-tip">启用HTTPS安全连接</span>
                      </el-form-item>
                      <el-form-item label="证书路径">
                        <el-input
                          v-model="sslForm.cert_path"
                          placeholder="SSL证书文件路径，如: /etc/ssl/certs/server.crt"
                        />
                      </el-form-item>
                      <el-form-item label="私钥路径">
                        <el-input
                          v-model="sslForm.key_path"
                          placeholder="SSL私钥文件路径，如: /etc/ssl/private/server.key"
                        />
                      </el-form-item>
                      <el-form-item>
                        <el-button
                          type="primary"
                          :loading="savingSettings"
                          @click="saveSSLSettings"
                        >
                          保存设置
                        </el-button>
                      </el-form-item>
                    </el-form>
                  </div>
                  
                  <!-- 系统日志 -->
                  <div
                    v-if="activeSettingMenu === 'logs'"
                    class="setting-panel"
                  >
                    <h3 class="setting-title">
                      <el-icon><Document /></el-icon>
                      系统日志
                    </h3>
                    <div class="log-actions">
                      <el-button
                        type="primary"
                        :loading="loadingLogs"
                        @click="viewSystemLogs"
                      >
                        <el-icon><View /></el-icon>
                        查看日志
                      </el-button>
                      <el-select
                        v-model="logLines"
                        placeholder="选择行数"
                        style="width: 150px; margin-left: 10px;"
                      >
                        <el-option
                          label="最近100行"
                          :value="100"
                        />
                        <el-option
                          label="最近500行"
                          :value="500"
                        />
                        <el-option
                          label="最近1000行"
                          :value="1000"
                        />
                        <el-option
                          label="最近2000行"
                          :value="2000"
                        />
                      </el-select>
                    </div>
                  </div>
                </el-col>
              </el-row>
            </div>
          </el-card>
        </div>
      </el-main>
    </el-container>
    
    <!-- Change Password Dialog -->
    <el-dialog
      v-model="passwordDialogVisible"
      title="修改密码"
      width="400px"
    >
      <el-form
        ref="passwordFormRef"
        :model="passwordForm"
        :rules="passwordRules"
        label-width="80px"
      >
        <el-form-item
          label="旧密码"
          prop="old_password"
        >
          <el-input
            v-model="passwordForm.old_password"
            type="password"
            placeholder="请输入旧密码"
            show-password
          />
        </el-form-item>
        <el-form-item
          label="新密码"
          prop="new_password"
        >
          <el-input
            v-model="passwordForm.new_password"
            type="password"
            placeholder="请输入新密码（至少6位）"
            show-password
          />
        </el-form-item>
        <el-form-item
          label="确认密码"
          prop="confirm_password"
        >
          <el-input
            v-model="passwordForm.confirm_password"
            type="password"
            placeholder="请再次输入新密码"
            show-password
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="passwordDialogVisible = false">
          取消
        </el-button>
        <el-button
          type="primary"
          :loading="changingPassword"
          @click="handleChangePassword"
        >
          确认修改
        </el-button>
      </template>
    </el-dialog>
    
    <!-- System Logs Dialog -->
    <el-dialog
      v-model="logsDialogVisible"
      title="系统日志"
      width="900px"
      top="5vh"
    >
      <div
        v-if="loadingLogs"
        class="loading-container"
      >
        <el-icon
          class="loading-icon"
          :size="40"
        >
          <Loading />
        </el-icon>
        <p class="loading-text">
          正在加载系统日志...
        </p>
      </div>
      <div
        v-else
        class="logs-content"
      >
        <div class="logs-header">
          <el-tag type="info">
            共 {{ systemLogs.length }} 条日志
          </el-tag>
          <el-button
            size="small"
            @click="refreshLogs"
          >
            <el-icon><Refresh /></el-icon>
            刷新
          </el-button>
        </div>
        <div class="logs-container">
          <pre class="logs-text">{{ systemLogs.join('\n') }}</pre>
        </div>
      </div>
      <template #footer>
        <el-button @click="logsDialogVisible = false">
          关闭
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, computed } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'
import {
  ArrowDown, Back, Delete, Document, FolderOpened, Key, Loading, Lock, Monitor, Odometer, OfficeBuilding, Plus, Refresh, Search, Setting, Tools, User, View
} from '@element-plus/icons-vue'
import { authAPI, preferencesAPI } from '@/api'

const router = useRouter()
const route = useRoute()
const currentUser = ref(null)
const passwordDialogVisible = ref(false)
const changingPassword = ref(false)
const passwordFormRef = ref(null)

// 设置菜单相关状态
const activeSettingMenu = ref('whitelist')
const savingSettings = ref(false)

// 白名单设置
const whitelistForm = reactive({
  enabled: false,
  ip_list: []
})

// SSL设置
const sslForm = reactive({
  enabled: false,
  cert_path: '',
  key_path: ''
})

// 日志相关状态
const logsDialogVisible = ref(false)
const loadingLogs = ref(false)
const systemLogs = ref([])
const logLines = ref(500)

const passwordForm = reactive({
  old_password: '',
  new_password: '',
  confirm_password: ''
})
const passwordRules = {
  old_password: [
    { required: true, message: '请输入旧密码', trigger: 'blur' }
  ],
  new_password: [
    { required: true, message: '请输入新密码', trigger: 'blur' },
    { min: 6, message: '密码长度不能少于6个字符', trigger: 'blur' }
  ],
  confirm_password: [
    { required: true, message: '请再次输入新密码', trigger: 'blur' },
    {
      validator: (_rule, value, callback) => {
        if (value !== passwordForm.new_password) {
          callback(new Error('两次输入的密码不一致'))
        } else {
          callback()
        }
      },
      trigger: 'blur'
    }
  ]
}

const activeMenu = computed(() => route.path)

// 加载系统设置
const loadSystemSettings = async () => {
  try {
    const response = await preferencesAPI.getSystemSettings()
    if (response.data.success) {
      const settings = response.data.settings
      // 白名单设置
      whitelistForm.enabled = settings.login_whitelist?.enabled || false
      whitelistForm.ip_list = settings.login_whitelist?.ip_list || []
      if (whitelistForm.ip_list.length === 0) {
        whitelistForm.ip_list = ['']
      }
      // SSL设置
      sslForm.enabled = settings.ssl?.enabled || false
      sslForm.cert_path = settings.ssl?.cert_path || ''
      sslForm.key_path = settings.ssl?.key_path || ''
    }
  } catch (error) {
    const message = error.response?.data?.message || error.message || '网络连接失败'
    ElMessage.error(`加载系统设置失败: ${message}`)
  }
}

// 保存白名单设置
const saveWhitelistSettings = async () => {
  savingSettings.value = true
  try {
    const response = await preferencesAPI.updateSystemSettings({
      login_whitelist: {
        enabled: whitelistForm.enabled,
        ip_list: whitelistForm.ip_list.filter(ip => ip.trim())
      }
    })
    if (response.data.success) {
      ElMessage.success('白名单设置已保存')
    } else {
      ElMessage.error(response.data.message || '保存失败')
    }
  } catch (error) {
    const message = error.response?.data?.message || error.message || '网络连接失败'
    ElMessage.error(`保存设置失败: ${message}`)
  } finally {
    savingSettings.value = false
  }
}

// 保存SSL设置
const saveSSLSettings = async () => {
  savingSettings.value = true
  try {
    const response = await preferencesAPI.updateSystemSettings({
      ssl: {
        enabled: sslForm.enabled,
        cert_path: sslForm.cert_path,
        key_path: sslForm.key_path
      }
    })
    if (response.data.success) {
      ElMessage.success('SSL设置已保存')
    } else {
      ElMessage.error(response.data.message || '保存失败')
    }
  } catch (error) {
    const message = error.response?.data?.message || error.message || '网络连接失败'
    ElMessage.error(`保存设置失败: ${message}`)
  } finally {
    savingSettings.value = false
  }
}

// 添加白名单IP
const addWhitelistIp = () => {
  whitelistForm.ip_list.push('')
}

// 移除白名单IP
const removeWhitelistIp = (index) => {
  whitelistForm.ip_list.splice(index, 1)
  if (whitelistForm.ip_list.length === 0) {
    whitelistForm.ip_list.push('')
  }
}

// 查看系统日志
const viewSystemLogs = async () => {
  logsDialogVisible.value = true
  await refreshLogs()
}

// 刷新日志
const refreshLogs = async () => {
  loadingLogs.value = true
  try {
    const response = await preferencesAPI.getSystemLogs(logLines.value)
    if (response.data.success) {
      systemLogs.value = response.data.logs || []
    } else {
      ElMessage.error(response.data.message || '获取日志失败')
    }
  } catch (error) {
    const message = error.response?.data?.message || error.message || '网络连接失败'
    ElMessage.error(`获取系统日志失败: ${message}`)
  } finally {
    loadingLogs.value = false
  }
}

// 处理设置菜单选择
const handleSettingMenuSelect = (index) => {
  activeSettingMenu.value = index
  if (index === 'logs') {
    viewSystemLogs()
  }
}

onMounted(async () => {
  const userStr = localStorage.getItem('user')
  if (userStr) {
    currentUser.value = JSON.parse(userStr)
  }
  await loadSystemSettings()
})

const goBack = () => {
  router.push('/dashboard')
}

const handleMenuSelect = (index) => {
  router.push(index)
}

const handleCommand = async (command) => {
  if (command === 'changePassword') {
    passwordForm.old_password = ''
    passwordForm.new_password = ''
    passwordForm.confirm_password = ''
    passwordDialogVisible.value = true
  } else if (command === 'logout') {
    try {
      await authAPI.logout()
    } catch (_error) {
      // 忽略登出错误，因为仍然需要清除本地存储
    }
    localStorage.removeItem('token')
    localStorage.removeItem('user')
    router.push('/login')
  }
}

const handleChangePassword = async () => {
  if (!passwordFormRef.value) return
  
  await passwordFormRef.value.validate(async (valid) => {
    if (valid) {
      changingPassword.value = true
      try {
        await authAPI.changePassword({
          old_password: passwordForm.old_password,
          new_password: passwordForm.new_password
        })
        ElMessage.success('密码修改成功')
        passwordDialogVisible.value = false
      } catch (error) {
        const message = error.response?.data?.message || '密码修改失败'
        ElMessage.error(message)
      } finally {
        changingPassword.value = false
      }
    }
  })
}
</script>

<style scoped>
/* 页面容器 */
.page-container {
  min-height: 100vh;
  background: linear-gradient(135deg, #f5f7fa 0%, #e4e7ed 100%);
}

/* 头部样式 - 统一淡蓝色导航 */
.header-container {
  background: linear-gradient(135deg, #5b9bd5 0%, #7db8e8 50%, #9ecae1 100%);
  color: white;
  display: flex;
  align-items: center;
  justify-content: space-between;
  box-shadow: 0 4px 24px 0 rgba(91, 155, 213, 0.35);
}

.header-logo {
  display: flex;
  align-items: center;
  gap: 10px;
}

.header-logo h2 {
  margin: 0;
  font-weight: 600;
}

.header-menu {
  border: none;
  flex: 1;
  margin-left: 50px;
  background: transparent !important;
}

.header-menu :deep(.el-menu-item) {
  color: rgba(255, 255, 255, 0.9) !important;
  font-weight: 500;
  font-size: 15px;
  border-radius: 8px;
  margin: 0 4px;
  transition: all 0.3s ease;
}

.header-menu :deep(.el-menu-item:hover) {
  background: rgba(255, 255, 255, 0.2) !important;
  color: #fff !important;
}

.header-menu :deep(.el-menu-item.is-active) {
  background: rgba(255, 255, 255, 0.25) !important;
  color: #fff !important;
  box-shadow: 0 2px 8px rgba(255, 255, 255, 0.2);
}

/* 子菜单样式 */
.header-menu :deep(.el-sub-menu__title) {
  color: rgba(255, 255, 255, 0.9) !important;
  font-weight: 500;
  font-size: 15px;
  border-radius: 8px;
  margin: 0 4px;
  transition: all 0.3s ease;
}

.header-menu :deep(.el-sub-menu__title:hover) {
  background: rgba(255, 255, 255, 0.2) !important;
  color: #fff !important;
}

.header-menu :deep(.el-sub-menu.is-active .el-sub-menu__title) {
  background: rgba(255, 255, 255, 0.25) !important;
  color: #fff !important;
  box-shadow: 0 2px 8px rgba(255, 255, 255, 0.2);
}

.user-dropdown {
  display: flex;
  align-items: center;
  gap: 5px;
  cursor: pointer;
  padding: 10px 15px;
  color: white;
  transition: all 0.3s;
  border-radius: 8px;
  background: rgba(255, 255, 255, 0.15);
}

.user-dropdown:hover {
  background-color: rgba(255, 255, 255, 0.25);
}

/* 主内容区 */
.main-content {
  background: transparent;
}

.content-wrapper {
  padding: 24px;
  max-width: 1400px;
  margin: 0 auto;
}

/* 设置卡片 */
.settings-card {
  border-radius: 16px;
  box-shadow: 0 4px 20px 0 rgba(0, 0, 0, 0.05);
  border: none;
}

.settings-card :deep(.el-card__header) {
  border-bottom: 1px solid #f0f0f0;
  padding: 20px 24px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.card-header-title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 18px;
  font-weight: 600;
  color: #303133;
}

.card-header-icon {
  color: #409EFF;
}

.card-header-buttons {
  display: flex;
  gap: 10px;
}

.settings-content {
  min-height: 500px;
  padding: 16px;
}

/* 设置菜单样式 */
.settings-menu {
  border-right: 1px solid #e6e6e6;
  border-radius: 8px;
  background: #fafafa;
}

.settings-menu :deep(.el-menu-item) {
  height: 50px;
  line-height: 50px;
  font-size: 14px;
  margin: 4px 0;
  border-radius: 8px;
}

.settings-menu :deep(.el-menu-item.is-active) {
  background: linear-gradient(135deg, #409EFF 0%, #66b1ff 100%);
  color: white;
}

/* 设置面板样式 */
.setting-panel {
  padding: 20px;
  background: #fafafa;
  border-radius: 12px;
}

.setting-title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 18px;
  font-weight: 600;
  color: #303133;
  margin-bottom: 24px;
  padding-bottom: 12px;
  border-bottom: 2px solid #409EFF;
}

.form-tip {
  margin-left: 12px;
  font-size: 12px;
  color: #909399;
}

/* IP列表样式 */
.ip-list-container {
  width: 100%;
}

.ip-item {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 10px;
}

.ip-item .el-input {
  flex: 1;
}

/* 日志操作区 */
.log-actions {
  display: flex;
  align-items: center;
  margin-bottom: 20px;
}

/* 加载状态 */
.loading-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 60px 20px;
  color: #909399;
  width: 100%;
}

.loading-icon {
  color: #409EFF;
  animation: rotate 1s linear infinite;
}

@keyframes rotate {
  from {
    transform: rotate(0deg);
  }
  to {
    transform: rotate(360deg);
  }
}

.loading-text {
  margin-top: 16px;
  font-size: 14px;
  color: #606266;
}

/* 日志对话框样式 */
.logs-content {
  max-height: 60vh;
  overflow: hidden;
}

.logs-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.logs-container {
  max-height: 50vh;
  overflow-y: auto;
  background: #1e1e1e;
  border-radius: 8px;
  padding: 16px;
}

.logs-text {
  font-family: 'Monaco', 'Menlo', 'Consolas', monospace;
  font-size: 12px;
  color: #d4d4d4;
  margin: 0;
  white-space: pre-wrap;
  word-break: break-all;
}
</style>
