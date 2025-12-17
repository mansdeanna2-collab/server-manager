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
          <el-card class="backup-card">
            <template #header>
              <div class="card-header">
                <div class="card-header-title">
                  <el-icon
                    class="card-header-icon"
                    :size="20"
                  >
                    <FolderOpened />
                  </el-icon>
                  <span>系统备份</span>
                </div>
                <div class="card-header-buttons">
                  <el-button
                    type="info"
                    :loading="loadingSchema"
                    @click="handleViewDatabase"
                  >
                    <el-icon><Grid /></el-icon>
                    查看数据库
                  </el-button>
                  <el-button
                    type="success"
                    :loading="creatingBackup"
                    @click="handleCreateBackup"
                  >
                    <el-icon><Upload /></el-icon>
                    备份系统
                  </el-button>
                  <el-button
                    type="primary"
                    :loading="loadingBackups"
                    @click="loadBackupList"
                  >
                    <el-icon><Refresh /></el-icon>
                    刷新列表
                  </el-button>
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
            
            <div class="backup-content">
              <!-- Loading State -->
              <div
                v-if="loadingBackups"
                class="loading-container"
              >
                <el-icon
                  class="loading-icon"
                  :size="40"
                >
                  <Loading />
                </el-icon>
                <p class="loading-text">
                  正在加载备份列表...
                </p>
              </div>

              <!-- Empty State -->
              <el-empty
                v-else-if="backupList.length === 0"
                description="暂无备份文件，点击【备份系统】按钮创建新的备份"
              />

              <!-- Backup List -->
              <div
                v-else
                class="backup-list"
              >
                <div class="backup-stats">
                  <el-tag
                    type="info"
                    size="large"
                    effect="dark"
                  >
                    共 {{ backupList.length }} 个备份文件
                  </el-tag>
                </div>

                <el-table
                  :data="backupList"
                  style="width: 100%"
                  stripe
                  border
                >
                  <el-table-column
                    label="文件名"
                    min-width="280"
                  >
                    <template #default="scope">
                      <span class="backup-filename">{{ scope.row.filename }}</span>
                    </template>
                  </el-table-column>
                  <el-table-column
                    label="文件大小"
                    width="150"
                    align="center"
                  >
                    <template #default="scope">
                      <el-tag
                        type="primary"
                        effect="plain"
                      >
                        {{ scope.row.size_formatted }}
                      </el-tag>
                    </template>
                  </el-table-column>
                  <el-table-column
                    label="创建时间"
                    width="200"
                    align="center"
                  >
                    <template #default="scope">
                      <span class="backup-time">{{ scope.row.created_at || '-' }}</span>
                    </template>
                  </el-table-column>
                  <el-table-column
                    label="操作"
                    width="200"
                    align="center"
                    fixed="right"
                  >
                    <template #default="scope">
                      <div class="operation-buttons">
                        <el-button
                          type="primary"
                          size="small"
                          @click="handleDownloadBackup(scope.row)"
                        >
                          <el-icon><Download /></el-icon>
                          下载
                        </el-button>
                        <el-button
                          type="danger"
                          size="small"
                          @click="handleDeleteBackup(scope.row)"
                        >
                          <el-icon><Delete /></el-icon>
                          删除
                        </el-button>
                      </div>
                    </template>
                  </el-table-column>
                </el-table>
              </div>
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
    
    <!-- Database Schema Dialog -->
    <el-dialog
      v-model="databaseDialogVisible"
      title="数据库结构查看"
      width="800px"
      top="5vh"
    >
      <div
        v-if="loadingSchema"
        class="loading-container"
      >
        <el-icon
          class="loading-icon"
          :size="40"
        >
          <Loading />
        </el-icon>
        <p class="loading-text">
          正在加载数据库结构...
        </p>
      </div>
      <div
        v-else
        class="database-schema-content"
      >
        <el-alert
          type="info"
          :closable="false"
          style="margin-bottom: 16px;"
        >
          <template #title>
            <el-icon><InfoFilled /></el-icon>
            仅供查看，不可修改数据库内容
          </template>
        </el-alert>
        <el-collapse v-model="activeTableNames">
          <el-collapse-item
            v-for="table in databaseSchema"
            :key="table.name"
            :name="table.name"
          >
            <template #title>
              <div class="table-header">
                <el-icon><Grid /></el-icon>
                <span class="table-name">{{ table.name }}</span>
                <el-tag
                  size="small"
                  type="info"
                >
                  {{ table.columns.length }} 列
                </el-tag>
              </div>
            </template>
            <el-table
              :data="table.columns"
              stripe
              border
              size="small"
            >
              <el-table-column
                prop="name"
                label="列名"
                width="180"
              >
                <template #default="scope">
                  <span :class="{ 'primary-key': scope.row.primary_key }">
                    {{ scope.row.name }}
                    <el-tag
                      v-if="scope.row.primary_key"
                      size="small"
                      type="warning"
                    >
                      主键
                    </el-tag>
                  </span>
                </template>
              </el-table-column>
              <el-table-column
                prop="type"
                label="数据类型"
                width="150"
              />
              <el-table-column
                prop="nullable"
                label="可为空"
                width="100"
                align="center"
              >
                <template #default="scope">
                  <el-tag
                    :type="scope.row.nullable ? 'success' : 'danger'"
                    size="small"
                  >
                    {{ scope.row.nullable ? '是' : '否' }}
                  </el-tag>
                </template>
              </el-table-column>
              <el-table-column
                prop="default"
                label="默认值"
              >
                <template #default="scope">
                  <span class="default-value">{{ scope.row.default || '-' }}</span>
                </template>
              </el-table-column>
            </el-table>
          </el-collapse-item>
        </el-collapse>
      </div>
      <template #footer>
        <el-button @click="databaseDialogVisible = false">
          关闭
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, computed } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  ArrowDown, Back, Delete, Download, FolderOpened, Grid, InfoFilled, Loading, Monitor, Odometer, OfficeBuilding, Refresh, Search, Setting, Tools, Upload, User
} from '@element-plus/icons-vue'
import { authAPI, preferencesAPI } from '@/api'

const router = useRouter()
const route = useRoute()
const currentUser = ref(null)
const passwordDialogVisible = ref(false)
const changingPassword = ref(false)
const passwordFormRef = ref(null)

// 备份相关状态
const creatingBackup = ref(false)
const loadingBackups = ref(false)
const backupList = ref([])

// 数据库结构相关状态
const databaseDialogVisible = ref(false)
const loadingSchema = ref(false)
const databaseSchema = ref([])
const activeTableNames = ref([])

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

// 加载备份列表
const loadBackupList = async () => {
  loadingBackups.value = true
  try {
    const response = await preferencesAPI.listBackups()
    if (response.data.success) {
      backupList.value = response.data.backups || []
    } else {
      ElMessage.error(response.data.message || '获取备份列表失败')
    }
  } catch (error) {
    const message = error.response?.data?.message || error.message || '网络连接失败'
    ElMessage.error(`获取备份列表失败: ${message}`)
  } finally {
    loadingBackups.value = false
  }
}

// 创建备份
const handleCreateBackup = async () => {
  creatingBackup.value = true
  try {
    const response = await preferencesAPI.createBackup()
    if (response.data.success) {
      ElMessage.success(`系统备份创建成功，文件大小: ${response.data.size_formatted}`)
      // 刷新备份列表
      await loadBackupList()
    } else {
      ElMessage.error(response.data.message || '创建备份失败')
    }
  } catch (error) {
    const message = error.response?.data?.message || error.message || '网络连接失败'
    ElMessage.error(`创建备份失败: ${message}`)
  } finally {
    creatingBackup.value = false
  }
}

// 下载备份
const handleDownloadBackup = async (backup) => {
  const downloadUrl = preferencesAPI.getBackupDownloadUrl(backup.backup_id)
  const token = localStorage.getItem('token')
  
  try {
    // 使用fetch获取文件并触发下载
    const response = await fetch(downloadUrl, {
      headers: {
        'Authorization': `Bearer ${token}`
      }
    })
    
    if (!response.ok) {
      // 尝试解析错误消息
      let errorMessage = '下载失败'
      try {
        const errorData = await response.json()
        errorMessage = errorData.message || errorMessage
      } catch (_e) {
        // 如果无法解析JSON，使用状态文本
        errorMessage = response.statusText || errorMessage
      }
      throw new Error(errorMessage)
    }
    
    const blob = await response.blob()
    // 创建下载链接
    const url = window.URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = backup.filename
    document.body.appendChild(a)
    a.click()
    window.URL.revokeObjectURL(url)
    document.body.removeChild(a)
    ElMessage.success('备份文件下载成功')
  } catch (error) {
    ElMessage.error(`下载备份失败: ${error.message}`)
  }
}

// 删除备份
const handleDeleteBackup = async (backup) => {
  try {
    await ElMessageBox.confirm(
      `确定要删除备份文件 "${backup.filename}" 吗？此操作不可恢复。`,
      '删除确认',
      {
        confirmButtonText: '确定删除',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )
    
    const response = await preferencesAPI.deleteBackup(backup.backup_id)
    if (response.data.success) {
      ElMessage.success('备份文件已删除')
      // 刷新备份列表
      await loadBackupList()
    } else {
      ElMessage.error(response.data.message || '删除备份失败')
    }
  } catch (error) {
    if (error !== 'cancel') {
      const message = error.response?.data?.message || error.message || '删除失败'
      ElMessage.error(`删除备份失败: ${message}`)
    }
  }
}

onMounted(async () => {
  const userStr = localStorage.getItem('user')
  if (userStr) {
    currentUser.value = JSON.parse(userStr)
  }
  // 加载备份列表
  await loadBackupList()
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

// 查看数据库结构
const handleViewDatabase = async () => {
  databaseDialogVisible.value = true
  loadingSchema.value = true
  
  try {
    const response = await preferencesAPI.getDatabaseSchema()
    if (response.data.success) {
      databaseSchema.value = response.data.tables || []
      // 默认展开第一个表
      if (databaseSchema.value.length > 0) {
        activeTableNames.value = [databaseSchema.value[0].name]
      }
    } else {
      ElMessage.error(response.data.message || '获取数据库结构失败')
    }
  } catch (error) {
    const message = error.response?.data?.message || error.message || '网络连接失败'
    ElMessage.error(`获取数据库结构失败: ${message}`)
  } finally {
    loadingSchema.value = false
  }
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

/* 备份卡片 */
.backup-card {
  border-radius: 16px;
  box-shadow: 0 4px 20px 0 rgba(0, 0, 0, 0.05);
  border: none;
}

.backup-card :deep(.el-card__header) {
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
  color: #67C23A;
}

.card-header-buttons {
  display: flex;
  gap: 10px;
}

.backup-content {
  min-height: 400px;
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

/* 备份列表 */
.backup-list {
  padding: 16px 0;
}

.backup-stats {
  display: flex;
  gap: 16px;
  margin-bottom: 20px;
}

.backup-filename {
  font-family: 'Monaco', 'Menlo', 'Consolas', monospace;
  font-size: 14px;
  font-weight: 500;
  color: #409EFF;
}

.backup-time {
  color: #606266;
  font-size: 14px;
}

/* 操作按钮容器 */
.operation-buttons {
  display: flex;
  gap: 8px;
  justify-content: center;
}

/* 数据库结构对话框样式 */
.database-schema-content {
  max-height: 60vh;
  overflow-y: auto;
}

.table-header {
  display: flex;
  align-items: center;
  gap: 8px;
}

.table-name {
  font-weight: 600;
  color: #303133;
}

.primary-key {
  display: flex;
  align-items: center;
  gap: 8px;
  font-weight: 500;
  color: #E6A23C;
}

.default-value {
  font-family: 'Monaco', 'Menlo', 'Consolas', monospace;
  font-size: 12px;
  color: #909399;
}
</style>
