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
                    刷新
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
                正在加载服务器...
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
              description="未找到服务器"
              :image-size="150"
            />
            
            <!-- IP段卡片左右两边布局 -->
            <div
              v-else
              class="segments-container"
            >
              <div class="segments-two-columns">
                <!-- 左边区域：8个卡片，上下各4个 -->
                <div class="segments-column left-column">
                  <div class="column-title">
                    <el-icon><Monitor /></el-icon>
                    <span>IP段分组 (左)</span>
                  </div>
                  <div class="column-grid">
                    <div
                      v-for="segment in leftColumnSegments"
                      :key="segment.segmentKey"
                      class="segment-card"
                      @click="viewSegmentDetails(segment)"
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
                          @click.stop="viewSegmentDetails(segment)"
                        >
                          <el-icon><View /></el-icon>
                          查看
                        </el-button>
                      </div>
                    </div>
                  </div>
                </div>
                
                <!-- 右边区域：8个卡片，上下各4个 -->
                <div class="segments-column right-column">
                  <div class="column-title">
                    <el-icon><Monitor /></el-icon>
                    <span>IP段分组 (右)</span>
                  </div>
                  <div class="column-grid">
                    <div
                      v-for="segment in rightColumnSegments"
                      :key="segment.segmentKey"
                      class="segment-card"
                      @click="viewSegmentDetails(segment)"
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
                          @click.stop="viewSegmentDetails(segment)"
                        >
                          <el-icon><View /></el-icon>
                          查看
                        </el-button>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
              
              <!-- 分页 -->
              <div
                v-if="totalPages > 1"
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
            </div>
          </el-card>
        </div>
      </el-main>
    </el-container>
    
    <!-- Segment Detail Dialog -->
    <el-dialog
      v-model="segmentDialogVisible"
      :title="selectedSegment ? `IP段 ${selectedSegment.segment}.x 的服务器` : 'IP段服务器'"
      width="900px"
      class="segment-dialog"
    >
      <div v-if="selectedSegment">
        <div class="segment-dialog-header">
          <span class="segment-count">共 {{ selectedSegment.count }} 台服务器</span>
        </div>
        <el-table
          :data="selectedSegment.servers"
          style="width: 100%"
          stripe
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
              >
                {{ getStatusText(scope.row.status) }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column
            prop="os_info"
            label="系统信息"
          >
            <template #default="scope">
              <span v-if="scope.row.os_info">{{ scope.row.os_info }}</span>
              <span
                v-else
                class="no-info"
              >暂无</span>
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
  ArrowDown, FolderOpened, Loading, Monitor, Odometer, OfficeBuilding, Refresh, Search, Setting, User, View
} from '@element-plus/icons-vue'
import { authAPI, serversAPI } from '@/api'

const router = useRouter()
const route = useRoute()
const currentUser = ref(null)
const servers = ref([])
const loading = ref(false)
const loadError = ref('')
const passwordDialogVisible = ref(false)
const changingPassword = ref(false)
const passwordFormRef = ref(null)
const segmentDialogVisible = ref(false)
const selectedSegment = ref(null)
const currentPage = ref(1)
const PAGE_SIZE = 16 // 每页16个IP段（左右各8个）

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

// 按IP段分组服务器
const groupedServers = computed(() => {
  const groups = {}
  servers.value.forEach(server => {
    const parts = server.ip_address.split('.')
    const segment = parts.slice(0, 3).join('.')
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
  })
  return Object.values(groups).sort((a, b) => a.segment.localeCompare(b.segment))
})

// 总页数
const totalPages = computed(() => Math.ceil(groupedServers.value.length / PAGE_SIZE))

// 当前页的IP段
const paginatedSegments = computed(() => {
  const start = (currentPage.value - 1) * PAGE_SIZE
  const end = start + PAGE_SIZE
  return groupedServers.value.slice(start, end)
})

// 左边列的IP段（前8个）
const leftColumnSegments = computed(() => {
  return paginatedSegments.value.slice(0, 8)
})

// 右边列的IP段（后8个）
const rightColumnSegments = computed(() => {
  return paginatedSegments.value.slice(8, 16)
})

// 加载服务器数据
const loadServers = async () => {
  loading.value = true
  loadError.value = ''
  try {
    const response = await serversAPI.getAll()
    servers.value = response.data
  } catch (error) {
    const message = error.response?.data?.message || error.message || '网络连接失败'
    loadError.value = message
    ElMessage.error(`加载服务器失败: ${message}`)
  } finally {
    loading.value = false
  }
}

// 查看IP段详情
const viewSegmentDetails = (segment) => {
  selectedSegment.value = segment
  segmentDialogVisible.value = true
}

// 获取状态类型
const getStatusType = (status) => {
  const types = {
    online: 'success',
    offline: 'danger',
    unknown: 'info'
  }
  return types[status] || 'info'
}

// 获取状态文字
const getStatusText = (status) => {
  const texts = {
    online: '在线',
    offline: '离线',
    unknown: '未知'
  }
  return texts[status] || '未知'
}

onMounted(async () => {
  const userStr = localStorage.getItem('user')
  if (userStr) {
    currentUser.value = JSON.parse(userStr)
  }
  await loadServers()
})

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

/* 加载状态 */
.loading-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 60px 20px;
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

/* IP段卡片左右布局 */
.segments-container {
  padding: 16px 0;
}

.segments-two-columns {
  display: flex;
  gap: 24px;
}

.segments-column {
  flex: 1;
  background: #f8fafc;
  border-radius: 12px;
  padding: 16px;
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
  border-bottom: 2px solid #e4e7ed;
}

.column-title .el-icon {
  color: #409EFF;
}

.column-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  grid-template-rows: repeat(4, auto);
  gap: 12px;
}

/* IP段卡片样式 */
.segment-card {
  background: white;
  border-radius: 12px;
  padding: 14px;
  cursor: pointer;
  transition: all 0.3s ease;
  border: 1px solid #e4e7ed;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.04);
}

.segment-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 6px 16px rgba(64, 158, 255, 0.15);
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
  color: #303133;
  font-family: 'Monaco', 'Menlo', 'Consolas', monospace;
}

.count-tag {
  font-size: 12px;
}

.segment-card-status {
  display: flex;
  gap: 6px;
  margin-bottom: 10px;
  flex-wrap: wrap;
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

/* 段详情对话框 */
.segment-dialog :deep(.el-dialog) {
  border-radius: 16px;
}

.segment-dialog :deep(.el-dialog__header) {
  background: linear-gradient(135deg, #409EFF 0%, #337ecc 100%);
  color: white;
  border-radius: 16px 16px 0 0;
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

.segment-dialog-header {
  margin-bottom: 16px;
}

.segment-count {
  font-size: 14px;
  color: #606266;
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
  .segments-two-columns {
    flex-direction: column;
  }
  
  .column-grid {
    grid-template-columns: repeat(4, 1fr);
    grid-template-rows: repeat(2, auto);
  }
}

@media (max-width: 768px) {
  .column-grid {
    grid-template-columns: repeat(2, 1fr);
    grid-template-rows: repeat(4, auto);
  }
}
</style>
