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
          :default-active="currentTopMenu"
          background-color="transparent"
          text-color="#fff"
          active-text-color="#fff"
          class="header-menu"
          @select="handleMenuSelect"
        >
          <el-menu-item index="dashboard">
            <el-icon><Odometer /></el-icon>
            仪表盘
          </el-menu-item>
          <el-menu-item index="/servers">
            <el-icon><OfficeBuilding /></el-icon>
            服务器
          </el-menu-item>
          <el-menu-item index="main-program">
            <el-icon><Setting /></el-icon>
            主程序功能
          </el-menu-item>
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
        <div class="dashboard-layout">
          <!-- 左侧主程序功能菜单（仅在主程序功能模式显示） -->
          <div
            v-if="showMainProgramSidebar"
            class="main-program-sidebar"
          >
            <div class="sidebar-header">
              <el-icon :size="18">
                <Setting />
              </el-icon>
              <span>主程序功能</span>
            </div>
            <div class="sidebar-menu">
              <div
                class="sidebar-menu-item"
                :class="{ active: activeSubMenu === 'information-query' }"
                @click="selectSubMenu('information-query')"
              >
                <el-icon><Search /></el-icon>
                <span>信息查询</span>
              </div>
              <div
                class="sidebar-menu-item"
                :class="{ active: activeSubMenu === 'system-backup' }"
                @click="selectSubMenu('system-backup')"
              >
                <el-icon><FolderOpened /></el-icon>
                <span>系统备份</span>
              </div>
            </div>
          </div>
          
          <!-- 右侧主内容区 -->
          <div class="content-wrapper">
            <!-- 仪表盘内容（仅在仪表盘模式显示） -->
            <template v-if="!showMainProgramSidebar">
              <!-- 欢迎横幅 -->
              <div class="welcome-banner">
                <div class="welcome-content">
                  <h1 class="welcome-title">
                    👋 欢迎回来，{{ currentUser?.username || '管理员' }}
                  </h1>
                  <p class="welcome-subtitle">
                    这是您的服务器管理仪表盘，随时监控服务器状态
                  </p>
                </div>
                <div class="welcome-decoration">
                  <div class="decoration-circle circle-1" />
                  <div class="decoration-circle circle-2" />
                  <div class="decoration-circle circle-3" />
                </div>
              </div>
            
              <!-- 统计卡片 -->
              <div class="stats-grid">
                <div class="stat-card stat-card-total">
                  <div class="stat-card-bg" />
                  <div class="stat-card-content">
                    <div class="stat-card-icon-wrapper stat-icon-total">
                      <el-icon :size="28">
                        <OfficeBuilding />
                      </el-icon>
                    </div>
                    <div class="stat-card-info">
                      <div class="stat-card-value">
                        {{ stats.total }}
                      </div>
                      <div class="stat-card-title">
                        服务器总数
                      </div>
                    </div>
                  </div>
                  <div class="stat-card-trend">
                    <el-icon><DataAnalysis /></el-icon>
                    全部服务器
                  </div>
                </div>
              
                <div class="stat-card stat-card-online">
                  <div class="stat-card-bg" />
                  <div class="stat-card-content">
                    <div class="stat-card-icon-wrapper stat-icon-online">
                      <el-icon :size="28">
                        <CircleCheck />
                      </el-icon>
                    </div>
                    <div class="stat-card-info">
                      <div class="stat-card-value">
                        {{ stats.online }}
                      </div>
                      <div class="stat-card-title">
                        正常运行
                      </div>
                    </div>
                  </div>
                  <div class="stat-card-trend trend-success">
                    <el-icon><TrendCharts /></el-icon>
                    {{ onlinePercentage }}% 运行率
                  </div>
                </div>
              
                <div class="stat-card stat-card-offline">
                  <div class="stat-card-bg" />
                  <div class="stat-card-content">
                    <div class="stat-card-icon-wrapper stat-icon-offline">
                      <el-icon :size="28">
                        <CircleClose />
                      </el-icon>
                    </div>
                    <div class="stat-card-info">
                      <div class="stat-card-value">
                        {{ stats.offline }}
                      </div>
                      <div class="stat-card-title">
                        离线
                      </div>
                    </div>
                  </div>
                  <div class="stat-card-trend trend-danger">
                    <el-icon><Warning /></el-icon>
                    需要关注
                  </div>
                </div>
              
                <div class="stat-card stat-card-unknown">
                  <div class="stat-card-bg" />
                  <div class="stat-card-content">
                    <div class="stat-card-icon-wrapper stat-icon-unknown">
                      <el-icon :size="28">
                        <QuestionFilled />
                      </el-icon>
                    </div>
                    <div class="stat-card-info">
                      <div class="stat-card-value">
                        {{ stats.unknown }}
                      </div>
                      <div class="stat-card-title">
                        未知状态
                      </div>
                    </div>
                  </div>
                  <div class="stat-card-trend trend-info">
                    <el-icon><InfoFilled /></el-icon>
                    待检测
                  </div>
                </div>
              </div>
            
              <!-- 服务器列表卡片 -->
              <el-card class="server-list-card">
                <template #header>
                  <div class="card-header">
                    <div class="card-header-title">
                      <el-icon
                        class="card-header-icon"
                        :size="20"
                      >
                        <List />
                      </el-icon>
                      <span>近期服务器</span>
                    </div>
                    <el-button
                      type="primary"
                      :loading="checkingAll"
                      class="check-all-btn"
                      @click="checkAllServers"
                    >
                      <el-icon><Refresh /></el-icon>
                      一键检测
                    </el-button>
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
              
                <el-empty
                  v-else-if="servers.length === 0"
                  description="未找到服务器"
                />
              
                <template v-else>
                  <el-table
                    :data="paginatedServers"
                    style="width: 100%"
                    stripe
                    class="server-table"
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
                      label="端口"
                      width="100"
                    >
                      <template #default="scope">
                        <el-tag
                          :type="getPortTagType(scope.row.port)"
                          size="small"
                          effect="dark"
                          round
                        >
                          {{ scope.row.port }}
                        </el-tag>
                      </template>
                    </el-table-column>
                    <el-table-column
                      prop="username"
                      label="用户名"
                      width="120"
                    />
                    <el-table-column
                      label="状态"
                      width="120"
                    >
                      <template #default="scope">
                        <StatusBadge
                          :status="scope.row.status"
                          :detail="scope.row.checkDetail"
                          :error-type="scope.row.error_type"
                        />
                      </template>
                    </el-table-column>
                    <el-table-column
                      label="操作系统"
                    >
                      <template #default="scope">
                        <span v-if="scope.row.os_info">
                          {{ getOsIcon(scope.row.os_info) }} {{ scope.row.os_info }}
                        </span>
                        <span
                          v-else
                          class="no-info"
                        >暂无</span>
                      </template>
                    </el-table-column>
                    <el-table-column
                      label="最近检查"
                      width="180"
                    >
                      <template #default="scope">
                        <span class="check-time">
                          <el-icon><Timer /></el-icon>
                          {{ formatDate(scope.row.last_checked) }}
                        </span>
                      </template>
                    </el-table-column>
                    <el-table-column
                      label="操作"
                      width="100"
                    >
                      <template #default="scope">
                        <el-button
                          size="small"
                          type="primary"
                          :loading="scope.row.checking"
                          @click="checkServer(scope.row)"
                        >
                          <el-icon><Search /></el-icon>
                          检测
                        </el-button>
                      </template>
                    </el-table-column>
                  </el-table>
                  <div
                    v-if="servers.length > PAGE_SIZE"
                    class="pagination-container"
                  >
                    <el-pagination
                      v-model:current-page="currentPage"
                      :page-size="PAGE_SIZE"
                      :total="servers.length"
                      layout="prev, pager, next"
                      background
                    />
                  </div>
                </template>
              </el-card>
            </template>

            <!-- 主程序功能内容（仅在主程序功能模式显示） -->
            <template v-else>
              <!-- 信息查询内容 -->
              <el-card
                v-if="activeSubMenu === 'information-query'"
                class="sub-page-card"
              >
                <template #header>
                  <div class="card-header">
                    <div class="card-header-title">
                      <el-icon
                        class="card-header-icon"
                        :size="20"
                      >
                        <Search />
                      </el-icon>
                      <span>信息查询</span>
                    </div>
                  </div>
                </template>
                <div class="sub-page-content">
                  <el-empty description="信息查询功能页面" />
                </div>
              </el-card>

              <!-- 系统备份内容 -->
              <el-card
                v-else-if="activeSubMenu === 'system-backup'"
                class="sub-page-card"
              >
                <template #header>
                  <div class="card-header">
                    <div class="card-header-title">
                      <el-icon
                        class="card-header-icon card-header-icon-success"
                        :size="20"
                      >
                        <FolderOpened />
                      </el-icon>
                      <span>系统备份</span>
                    </div>
                  </div>
                </template>
                <div class="sub-page-content">
                  <el-empty description="系统备份功能页面" />
                </div>
              </el-card>

              <!-- 默认提示：请选择功能 -->
              <div
                v-else
                class="select-hint"
              >
                <el-empty description="请从左侧菜单选择功能" />
              </div>
            </template>
          </div>
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
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import {
  ArrowDown, CircleCheck, CircleClose, DataAnalysis, FolderOpened, InfoFilled, List,
  Loading, Monitor, Odometer, OfficeBuilding, QuestionFilled, Refresh,
  Search, Setting, Timer, TrendCharts, User, Warning
} from '@element-plus/icons-vue'
import { serversAPI, authAPI } from '@/api'
import StatusBadge from '@/components/StatusBadge.vue'

const router = useRouter()
const servers = ref([])
const checkingAll = ref(false)
const currentUser = ref(null)
const loading = ref(false)
const loadError = ref('')
const passwordDialogVisible = ref(false)
const changingPassword = ref(false)
const passwordFormRef = ref(null)
const currentPage = ref(1)
const PAGE_SIZE = 10
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

// 主程序功能相关状态
const showMainProgramSidebar = ref(false)
const activeSubMenu = ref('')

// 当前顶部菜单（用于高亮显示）
const currentTopMenu = computed(() => {
  if (showMainProgramSidebar.value) {
    return 'main-program'
  }
  return 'dashboard'
})

// 端口类型颜色映射
const PORT_TYPE_MAP = {
  22: 'success',
  3389: 'primary',
  23: 'warning',
  21: 'info',
  80: 'info',
  443: 'success',
  3306: 'warning',
  5432: 'primary'
}

const getPortTagType = (port) => {
  return PORT_TYPE_MAP[port] || 'info'
}

// OS图标映射常量
const OS_ICONS = {
  default: '💻',
  linux: '🐧',
  redhat: '🎩',
  windows: '🪟',
  mac: '🍎'
}

// 根据OS信息获取图标
const getOsIcon = (osInfo) => {
  if (!osInfo) return OS_ICONS.default
  const osLower = osInfo.toLowerCase()
  if (osLower.includes('ubuntu') || osLower.includes('debian')) return OS_ICONS.linux
  if (osLower.includes('centos') || osLower.includes('red hat') || osLower.includes('rhel')) return OS_ICONS.redhat
  if (osLower.includes('windows')) return OS_ICONS.windows
  if (osLower.includes('mac') || osLower.includes('darwin')) return OS_ICONS.mac
  if (osLower.includes('linux')) return OS_ICONS.linux
  return OS_ICONS.default
}

const stats = reactive({
  total: 0,
  online: 0,
  offline: 0,
  unknown: 0
})

// 运行率百分比计算
const onlinePercentage = computed(() => {
  return stats.total > 0 ? Math.round(stats.online / stats.total * 100) : 0
})

// Computed property for paginated servers
const paginatedServers = computed(() => {
  const start = (currentPage.value - 1) * PAGE_SIZE
  const end = start + PAGE_SIZE
  return servers.value.slice(start, end)
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
    calculateStats()
  } catch (error) {
    const message = error.response?.data?.message || error.message || '网络连接失败'
    loadError.value = message
    ElMessage.error(`加载服务器失败: ${message}`)
  } finally {
    loading.value = false
  }
}

const calculateStats = () => {
  stats.total = servers.value.length
  // 正常: root用户 + 在线 + 无错误 (与服务器列表的"正常"按钮一致)
  stats.online = servers.value.filter(s => s.username === 'root' && s.status === 'online' && !s.error_type).length
  stats.offline = servers.value.filter(s => s.status === 'offline').length
  stats.unknown = servers.value.filter(s => s.status === 'unknown').length
}

const applyStatusFields = (server, statusData) => {
  if (!server || !statusData) return
  server.status = statusData.overall
  server.checkDetail = statusData.detail || ''
  server.error_type = statusData.error_type || ''
}

const checkServer = async (server) => {
  server.checking = true
  try {
    const response = await serversAPI.check(server.id)
    const statusData = response.data.status
    applyStatusFields(server, statusData)
    server.last_checked = new Date().toISOString()
    ElMessage.success(`已检测服务器 ${server.ip_address}`)
    calculateStats()
  } catch (_error) {
    ElMessage.error('检测服务器失败')
  } finally {
    server.checking = false
  }
}

const checkAllServers = async () => {
  checkingAll.value = true
  try {
    const response = await serversAPI.checkAll()
    const results = Array.isArray(response?.data) ? response.data : []
    const statusMap = new Map(results.map(item => [item.server_id, item.status]))

    servers.value.forEach(server => {
      const status = statusMap.get(server.id)
      if (status) {
        applyStatusFields(server, status)
        server.last_checked = new Date().toISOString()
      }
    })

    calculateStats()
    ElMessage.success('全部服务器已检测')
  } catch (_error) {
    ElMessage.error('检测所有服务器失败')
  } finally {
    checkingAll.value = false
  }
}

const formatDate = (dateStr) => {
  if (!dateStr) return '从未'
  const date = new Date(dateStr)
  return date.toLocaleString()
}

const handleMenuSelect = (index) => {
  if (index === 'dashboard') {
    showMainProgramSidebar.value = false
    activeSubMenu.value = ''
  } else if (index === 'main-program') {
    showMainProgramSidebar.value = true
    // 默认选中信息查询
    if (!activeSubMenu.value) {
      activeSubMenu.value = 'information-query'
    }
  } else {
    // 外部路由（如服务器页面）
    router.push(index)
  }
}

const selectSubMenu = (menuKey) => {
  activeSubMenu.value = menuKey
}

const handleCommand = async (command) => {
  if (command === 'changePassword') {
    // Reset form
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

/* 仪表盘布局 */
.dashboard-layout {
  display: flex;
  gap: 24px;
  padding: 24px;
}

/* 主程序功能侧边栏 */
.main-program-sidebar {
  width: 180px;
  flex-shrink: 0;
  background: white;
  border-radius: 16px;
  box-shadow: 0 4px 20px 0 rgba(0, 0, 0, 0.05);
  padding: 16px;
  height: fit-content;
}

.sidebar-header {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 16px;
  font-weight: 600;
  color: #303133;
  padding-bottom: 12px;
  border-bottom: 1px solid #f0f0f0;
  margin-bottom: 12px;
}

.sidebar-header .el-icon {
  color: #409EFF;
}

.sidebar-menu {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.sidebar-menu-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 12px 16px;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.3s ease;
  color: #606266;
  font-size: 14px;
}

.sidebar-menu-item:hover {
  background: linear-gradient(135deg, #409EFF 0%, #337ecc 100%);
  color: white;
  box-shadow: 0 4px 12px 0 rgba(64, 158, 255, 0.3);
}

.sidebar-menu-item.active {
  background: linear-gradient(135deg, #409EFF 0%, #337ecc 100%);
  color: white;
  box-shadow: 0 4px 12px 0 rgba(64, 158, 255, 0.3);
}

.sidebar-menu-item .el-icon {
  font-size: 16px;
}

.content-wrapper {
  flex: 1;
  max-width: 1400px;
}

/* 欢迎横幅 */
.welcome-banner {
  position: relative;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border-radius: 16px;
  padding: 32px 40px;
  margin-bottom: 24px;
  overflow: hidden;
  box-shadow: 0 10px 40px 0 rgba(102, 126, 234, 0.3);
}

.welcome-content {
  position: relative;
  z-index: 1;
}

.welcome-title {
  color: white;
  font-size: 28px;
  font-weight: 600;
  margin: 0 0 8px 0;
}

.welcome-subtitle {
  color: rgba(255, 255, 255, 0.85);
  font-size: 15px;
  margin: 0;
}

.welcome-decoration {
  position: absolute;
  right: 40px;
  top: 50%;
  transform: translateY(-50%);
}

.decoration-circle {
  position: absolute;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.1);
}

.circle-1 {
  width: 120px;
  height: 120px;
  right: 0;
  top: -30px;
}

.circle-2 {
  width: 80px;
  height: 80px;
  right: 100px;
  top: 20px;
}

.circle-3 {
  width: 60px;
  height: 60px;
  right: 60px;
  top: -60px;
}

/* 统计卡片网格 */
.stats-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 20px;
  margin-bottom: 24px;
}

@media (max-width: 1200px) {
  .stats-grid {
    grid-template-columns: repeat(2, 1fr);
  }
}

@media (max-width: 600px) {
  .stats-grid {
    grid-template-columns: 1fr;
  }
}

/* 统计卡片 */
.stat-card {
  position: relative;
  background: white;
  border-radius: 16px;
  padding: 24px;
  overflow: hidden;
  box-shadow: 0 4px 20px 0 rgba(0, 0, 0, 0.05);
  transition: all 0.3s ease;
}

.stat-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 12px 30px 0 rgba(0, 0, 0, 0.1);
}

.stat-card-bg {
  position: absolute;
  top: 0;
  right: 0;
  width: 100px;
  height: 100px;
  border-radius: 50%;
  transform: translate(30%, -30%);
  opacity: 0.1;
}

.stat-card-total .stat-card-bg {
  background: linear-gradient(135deg, #409EFF 0%, #337ecc 100%);
}

.stat-card-online .stat-card-bg {
  background: linear-gradient(135deg, #67C23A 0%, #529b2e 100%);
}

.stat-card-offline .stat-card-bg {
  background: linear-gradient(135deg, #F56C6C 0%, #dd6161 100%);
}

.stat-card-unknown .stat-card-bg {
  background: linear-gradient(135deg, #909399 0%, #73767a 100%);
}

.stat-card-content {
  display: flex;
  align-items: center;
  gap: 16px;
  position: relative;
  z-index: 1;
}

.stat-card-icon-wrapper {
  width: 56px;
  height: 56px;
  border-radius: 14px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
}

.stat-icon-total {
  background: linear-gradient(135deg, #409EFF 0%, #337ecc 100%);
  box-shadow: 0 4px 15px 0 rgba(64, 158, 255, 0.4);
}

.stat-icon-online {
  background: linear-gradient(135deg, #67C23A 0%, #529b2e 100%);
  box-shadow: 0 4px 15px 0 rgba(103, 194, 58, 0.4);
}

.stat-icon-offline {
  background: linear-gradient(135deg, #F56C6C 0%, #dd6161 100%);
  box-shadow: 0 4px 15px 0 rgba(245, 108, 108, 0.4);
}

.stat-icon-unknown {
  background: linear-gradient(135deg, #909399 0%, #73767a 100%);
  box-shadow: 0 4px 15px 0 rgba(144, 147, 153, 0.4);
}

.stat-card-info {
  flex: 1;
}

.stat-card-value {
  font-size: 32px;
  font-weight: 700;
  color: #303133;
  line-height: 1.2;
}

.stat-card-title {
  font-size: 14px;
  color: #909399;
  margin-top: 4px;
}

.stat-card-trend {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 12px;
  color: #909399;
  margin-top: 16px;
  padding-top: 16px;
  border-top: 1px solid #f0f0f0;
}

.trend-success {
  color: #67C23A;
}

.trend-danger {
  color: #F56C6C;
}

.trend-info {
  color: #909399;
}

/* 服务器列表卡片 */
.server-list-card {
  border-radius: 16px;
  box-shadow: 0 4px 20px 0 rgba(0, 0, 0, 0.05);
  border: none;
}

.server-list-card :deep(.el-card__header) {
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

.check-all-btn {
  border-radius: 8px;
  padding: 10px 20px;
}

/* 服务器表格 */
.server-table {
  border-radius: 12px;
  overflow: hidden;
}

.server-table :deep(.el-table__header th) {
  background-color: #f8f9fa !important;
  font-weight: 600;
  color: #606266;
}

.server-table :deep(.el-table__row:hover td) {
  background-color: #f5f7fa !important;
}

.ip-text {
  font-family: 'Monaco', 'Menlo', 'Consolas', monospace;
  font-size: 13px;
  color: #409EFF;
  font-weight: 500;
}

.check-time {
  display: flex;
  align-items: center;
  gap: 4px;
  color: #909399;
  font-size: 13px;
}

.no-info {
  color: #c0c4cc;
}

/* 分页容器 */
.pagination-container {
  display: flex;
  justify-content: center;
  margin-top: 20px;
  padding-top: 20px;
  border-top: 1px solid #f0f0f0;
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

/* 子页面卡片样式 */
.sub-page-card {
  border-radius: 16px;
  box-shadow: 0 4px 20px 0 rgba(0, 0, 0, 0.05);
  border: none;
}

.sub-page-card :deep(.el-card__header) {
  border-bottom: 1px solid #f0f0f0;
  padding: 20px 24px;
}

.sub-page-content {
  min-height: 400px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.card-header-icon-success {
  color: #67C23A !important;
}

.select-hint {
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 400px;
  background: white;
  border-radius: 16px;
  box-shadow: 0 4px 20px 0 rgba(0, 0, 0, 0.05);
}
</style>
