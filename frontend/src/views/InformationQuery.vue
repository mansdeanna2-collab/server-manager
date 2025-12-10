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
          <el-card class="info-card">
            <template #header>
              <div class="card-header">
                <div class="card-header-title">
                  <el-icon
                    class="card-header-icon"
                    :size="20"
                  >
                    <Search />
                  </el-icon>
                  <span>信息显示</span>
                </div>
                <div class="header-actions">
                  <el-button
                    type="primary"
                    :loading="loading"
                    @click="loadServers"
                  >
                    <el-icon><Refresh /></el-icon>
                    刷新数据
                  </el-button>
                </div>
              </div>
            </template>
            
            <!-- Loading State -->
            <div
              v-if="loading"
              class="loading-container"
            >
              <el-icon
                class="loading-icon"
                :size="40"
              >
                <Loading />
              </el-icon>
              <p class="loading-text">
                正在加载服务器信息...
              </p>
            </div>
            
            <!-- Error State -->
            <el-result
              v-else-if="loadError"
              icon="error"
              title="加载失败"
              :sub-title="loadError"
            >
              <template #extra>
                <el-button
                  type="primary"
                  @click="loadServers"
                >
                  <el-icon><Refresh /></el-icon>
                  重新加载
                </el-button>
              </template>
            </el-result>
            
            <!-- Empty State -->
            <el-empty
              v-else-if="groupedServers.length === 0"
              description="暂无服务器数据"
              :image-size="150"
            />
            
            <!-- IP段卡片布局 - 左右各8个 -->
            <div
              v-else
              class="ip-segments-layout"
            >
              <!-- 左侧8个IP段卡片 -->
              <div class="segments-column left-column">
                <div class="column-title">
                  <el-icon><Monitor /></el-icon>
                  <span>IP段组 A</span>
                </div>
                <div class="segments-grid">
                  <div
                    v-for="segment in leftColumnSegments"
                    :key="segment.segmentKey"
                    class="segment-card"
                    @click="viewSegmentDetail(segment)"
                  >
                    <div class="segment-card-header">
                      <span class="ip-segment-title">{{ segment.segment }}.x</span>
                      <el-tag
                        size="small"
                        type="info"
                        effect="plain"
                        class="count-tag"
                      >
                        {{ segment.count }} 台
                      </el-tag>
                    </div>
                    <div class="segment-card-status">
                      <el-tag
                        v-if="segment.onlineCount > 0"
                        type="success"
                        size="small"
                        effect="dark"
                      >
                        ✓ {{ segment.onlineCount }}
                      </el-tag>
                      <el-tag
                        v-if="segment.offlineCount > 0"
                        type="danger"
                        size="small"
                        effect="dark"
                      >
                        ✗ {{ segment.offlineCount }}
                      </el-tag>
                    </div>
                    <div class="segment-card-footer">
                      <el-button
                        size="small"
                        type="primary"
                        plain
                        @click.stop="viewSegmentDetail(segment)"
                      >
                        <el-icon><View /></el-icon>
                        查看详情
                      </el-button>
                    </div>
                  </div>
                </div>
              </div>
              
              <!-- 右侧8个IP段卡片 -->
              <div class="segments-column right-column">
                <div class="column-title">
                  <el-icon><Monitor /></el-icon>
                  <span>IP段组 B</span>
                </div>
                <div class="segments-grid">
                  <div
                    v-for="segment in rightColumnSegments"
                    :key="segment.segmentKey"
                    class="segment-card"
                    @click="viewSegmentDetail(segment)"
                  >
                    <div class="segment-card-header">
                      <span class="ip-segment-title">{{ segment.segment }}.x</span>
                      <el-tag
                        size="small"
                        type="info"
                        effect="plain"
                        class="count-tag"
                      >
                        {{ segment.count }} 台
                      </el-tag>
                    </div>
                    <div class="segment-card-status">
                      <el-tag
                        v-if="segment.onlineCount > 0"
                        type="success"
                        size="small"
                        effect="dark"
                      >
                        ✓ {{ segment.onlineCount }}
                      </el-tag>
                      <el-tag
                        v-if="segment.offlineCount > 0"
                        type="danger"
                        size="small"
                        effect="dark"
                      >
                        ✗ {{ segment.offlineCount }}
                      </el-tag>
                    </div>
                    <div class="segment-card-footer">
                      <el-button
                        size="small"
                        type="primary"
                        plain
                        @click.stop="viewSegmentDetail(segment)"
                      >
                        <el-icon><View /></el-icon>
                        查看详情
                      </el-button>
                    </div>
                  </div>
                </div>
              </div>
            </div>
            
            <!-- 分页 -->
            <div
              v-if="groupedServers.length > PAGE_SIZE"
              class="pagination-container"
            >
              <el-pagination
                v-model:current-page="currentPage"
                :page-size="PAGE_SIZE"
                :total="groupedServers.length"
                layout="prev, pager, next"
                background
              />
            </div>
          </el-card>
        </div>
      </el-main>
    </el-container>
    
    <!-- IP段详情对话框 -->
    <el-dialog
      v-model="segmentDialogVisible"
      :title="selectedSegment ? `IP段 ${selectedSegment.segment}.x 的服务器` : 'IP段服务器'"
      width="900px"
      class="segment-dialog"
    >
      <div v-if="selectedSegment">
        <div class="segment-header">
          <span class="segment-count">共 {{ selectedSegment.count }} 台服务器</span>
        </div>
        <el-table
          :data="selectedSegment.servers"
          style="width: 100%"
          stripe
          max-height="400"
        >
          <el-table-column
            label="IP地址"
            width="160"
          >
            <template #default="scope">
              <span class="ip-text">{{ scope.row.ip_address }}</span>
            </template>
          </el-table-column>
          <el-table-column
            prop="port"
            label="端口"
            width="80"
          />
          <el-table-column
            prop="username"
            label="用户名"
            width="100"
          />
          <el-table-column
            label="状态"
            width="100"
          >
            <template #default="scope">
              <el-tag
                :type="getStatusType(scope.row.status)"
                size="small"
                effect="dark"
              >
                {{ getStatusLabel(scope.row.status) }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column
            prop="os_info"
            label="系统信息"
            min-width="150"
          >
            <template #default="scope">
              <span v-if="scope.row.os_info">{{ scope.row.os_info }}</span>
              <span
                v-else
                class="no-info"
              >-</span>
            </template>
          </el-table-column>
        </el-table>
      </div>
    </el-dialog>
    
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
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, computed } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'
import {
  ArrowDown, Monitor, Odometer, OfficeBuilding, Search, User, Setting, FolderOpened,
  Refresh, Loading, View
} from '@element-plus/icons-vue'
import { authAPI, serversAPI } from '@/api'

const router = useRouter()
const route = useRoute()
const currentUser = ref(null)
const passwordDialogVisible = ref(false)
const changingPassword = ref(false)
const passwordFormRef = ref(null)
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

// 服务器数据
const servers = ref([])
const loading = ref(false)
const loadError = ref('')
const currentPage = ref(1)
const PAGE_SIZE = 16 // 左右各8个，每页16个IP段
const segmentDialogVisible = ref(false)
const selectedSegment = ref(null)

const activeMenu = computed(() => route.path)

// 按IP段分组服务器
const groupedServers = computed(() => {
  const groups = {}
  servers.value.forEach(server => {
    const parts = server.ip_address.split('.')
    if (parts.length >= 3) {
      const segment = `${parts[0]}.${parts[1]}.${parts[2]}`
      if (!groups[segment]) {
        groups[segment] = {
          segment,
          segmentKey: segment,
          servers: [],
          count: 0,
          onlineCount: 0,
          offlineCount: 0
        }
      }
      groups[segment].servers.push(server)
      groups[segment].count++
      if (server.status === 'online') {
        groups[segment].onlineCount++
      } else if (server.status === 'offline') {
        groups[segment].offlineCount++
      }
    }
  })
  return Object.values(groups).sort((a, b) => a.segment.localeCompare(b.segment))
})

// 当前页的IP段
const paginatedSegments = computed(() => {
  const start = (currentPage.value - 1) * PAGE_SIZE
  const end = start + PAGE_SIZE
  return groupedServers.value.slice(start, end)
})

// 左侧列显示的IP段（前8个）
const leftColumnSegments = computed(() => {
  return paginatedSegments.value.slice(0, 8)
})

// 右侧列显示的IP段（后8个）
const rightColumnSegments = computed(() => {
  return paginatedSegments.value.slice(8, 16)
})

onMounted(async () => {
  const userStr = localStorage.getItem('user')
  if (userStr) {
    currentUser.value = JSON.parse(userStr)
  }
  await loadServers()
})

const loadServers = async () => {
  loading.value = true
  loadError.value = ''
  try {
    const response = await serversAPI.getAll()
    servers.value = response.data.map(s => ({
      ...s,
      checking: false,
      checkDetail: s.checkDetail || '',
      error_type: s.error_type || ''
    }))
  } catch (error) {
    const message = error.response?.data?.message || error.message || '网络连接失败'
    loadError.value = message
    ElMessage.error(`加载服务器失败: ${message}`)
  } finally {
    loading.value = false
  }
}

const viewSegmentDetail = (segment) => {
  selectedSegment.value = segment
  segmentDialogVisible.value = true
}

const getStatusType = (status) => {
  if (status === 'online') return 'success'
  if (status === 'offline') return 'danger'
  return 'info'
}

const getStatusLabel = (status) => {
  if (status === 'online') return '在线'
  if (status === 'offline') return '离线'
  return '未知'
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
  max-width: 1600px;
  margin: 0 auto;
}

/* 信息卡片 */
.info-card {
  border-radius: 16px;
  box-shadow: 0 4px 20px 0 rgba(0, 0, 0, 0.05);
  border: none;
}

.info-card :deep(.el-card__header) {
  border-bottom: 1px solid #f0f0f0;
  padding: 20px 24px;
}

.info-card :deep(.el-card__body) {
  padding: 24px;
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

.header-actions {
  display: flex;
  gap: 12px;
}

/* IP段卡片布局 - 左右各8个 */
.ip-segments-layout {
  display: flex;
  gap: 32px;
  min-height: 500px;
}

.segments-column {
  flex: 1;
  display: flex;
  flex-direction: column;
}

.column-title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 16px;
  font-weight: 600;
  color: #303133;
  margin-bottom: 16px;
  padding-bottom: 12px;
  border-bottom: 2px solid #409EFF;
}

.column-title .el-icon {
  color: #409EFF;
}

.segments-grid {
  display: grid;
  grid-template-columns: 1fr;
  gap: 12px;
}

/* IP段卡片样式 */
.segment-card {
  background: linear-gradient(145deg, #ffffff 0%, #f8fafc 100%);
  border-radius: 12px;
  padding: 14px 16px;
  cursor: pointer;
  transition: all 0.3s ease;
  border: 1px solid #e2e8f0;
  box-shadow: 0 2px 8px 0 rgba(0, 0, 0, 0.04);
}

.segment-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 24px 0 rgba(64, 158, 255, 0.15);
  border-color: #409EFF;
}

.segment-card-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 10px;
}

.ip-segment-title {
  font-size: 15px;
  font-weight: 700;
  color: #1e3a5f;
  font-family: 'Monaco', 'Menlo', 'Consolas', monospace;
}

.count-tag {
  font-size: 12px;
  font-weight: 600;
}

.segment-card-status {
  display: flex;
  gap: 8px;
  margin-bottom: 10px;
}

.segment-card-footer {
  display: flex;
  justify-content: flex-end;
}

/* 分页容器 */
.pagination-container {
  display: flex;
  justify-content: center;
  margin-top: 24px;
  padding-top: 20px;
  border-top: 1px solid #f0f0f0;
}

/* 加载状态 */
.loading-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 80px 20px;
  color: #909399;
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

/* IP段详情对话框 */
.segment-dialog :deep(.el-dialog) {
  border-radius: 16px;
  overflow: hidden;
}

.segment-dialog :deep(.el-dialog__header) {
  background: linear-gradient(135deg, #409EFF 0%, #337ecc 100%);
  color: white;
  padding: 20px 24px;
  margin: 0;
}

.segment-dialog :deep(.el-dialog__title) {
  color: white;
  font-weight: 600;
}

.segment-dialog :deep(.el-dialog__headerbtn .el-dialog__close) {
  color: white;
}

.segment-dialog :deep(.el-dialog__body) {
  padding: 24px;
}

.segment-header {
  margin-bottom: 16px;
}

.segment-count {
  color: #606266;
  font-size: 14px;
}

.ip-text {
  font-family: 'Monaco', 'Menlo', 'Consolas', monospace;
  font-size: 13px;
  color: #409EFF;
  font-weight: 500;
}

.no-info {
  color: #c0c4cc;
}

/* 响应式布局 */
@media (max-width: 1200px) {
  .ip-segments-layout {
    flex-direction: column;
    gap: 24px;
  }
  
  .segments-grid {
    grid-template-columns: repeat(2, 1fr);
  }
}

@media (max-width: 768px) {
  .segments-grid {
    grid-template-columns: 1fr;
  }
}
</style>
