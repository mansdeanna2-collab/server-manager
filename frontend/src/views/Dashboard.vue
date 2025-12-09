<template>
  <div class="page-container">
    <el-container>
      <el-header style="background: #409EFF; color: white; display: flex; align-items: center; justify-content: space-between;">
        <div style="display: flex; align-items: center; gap: 10px;">
          <el-icon :size="30">
            <Monitor />
          </el-icon>
          <h2 style="margin: 0;">
            服务器管理
          </h2>
        </div>
        <el-menu
          mode="horizontal"
          :default-active="activeMenu"
          background-color="#409EFF"
          text-color="#fff"
          active-text-color="#ffd04b"
          style="border: none; flex: 1; margin-left: 50px;"
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
        </el-menu>
        <el-dropdown @command="handleCommand">
          <span class="user-dropdown">
            <el-icon><User /></el-icon>
            {{ currentUser?.username || '管理员' }}
            <el-icon><ArrowDown /></el-icon>
          </span>
          <template #dropdown>
            <el-dropdown-menu>
              <el-dropdown-item command="logout">
                退出登录
              </el-dropdown-item>
            </el-dropdown-menu>
          </template>
        </el-dropdown>
      </el-header>
      
      <el-main>
        <div class="content-wrapper">
          <div class="stats-grid">
            <div class="stat-card">
              <div
                class="stat-card-icon"
                style="color: #409EFF;"
              >
                <el-icon><OfficeBuilding /></el-icon>
              </div>
              <div class="stat-card-title">
                服务器总数
              </div>
              <div class="stat-card-value">
                {{ stats.total }}
              </div>
            </div>
            
            <div class="stat-card">
              <div
                class="stat-card-icon"
                style="color: #67C23A;"
              >
                <el-icon><CircleCheck /></el-icon>
              </div>
              <div class="stat-card-title">
                在线
              </div>
              <div class="stat-card-value">
                {{ stats.online }}
              </div>
            </div>
            
            <div class="stat-card">
              <div
                class="stat-card-icon"
                style="color: #F56C6C;"
              >
                <el-icon><CircleClose /></el-icon>
              </div>
              <div class="stat-card-title">
                离线
              </div>
              <div class="stat-card-value">
                {{ stats.offline }}
              </div>
            </div>
            
            <div class="stat-card">
              <div
                class="stat-card-icon"
                style="color: #909399;"
              >
                <el-icon><QuestionFilled /></el-icon>
              </div>
              <div class="stat-card-title">
                未知
              </div>
              <div class="stat-card-value">
                {{ stats.unknown }}
              </div>
            </div>
          </div>
          
          <el-card>
            <template #header>
              <div class="card-header">
                <span>近期服务器</span>
                <el-button
                  type="primary"
                  :loading="checkingAll"
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
            
            <el-table
              v-else
              :data="servers"
              style="width: 100%"
            >
              <el-table-column
                prop="ip_address"
                label="IP地址"
                width="150"
              />
              <el-table-column
                prop="port"
                label="端口"
                width="100"
              />
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
                prop="os_info"
                label="操作系统"
              />
              <el-table-column
                label="最近检查"
                width="180"
              >
                <template #default="scope">
                  {{ formatDate(scope.row.last_checked) }}
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
                    检测
                  </el-button>
                </template>
              </el-table-column>
            </el-table>
          </el-card>
        </div>
      </el-main>
    </el-container>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, computed } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'
import {
  Monitor, Odometer, User, ArrowDown, Refresh,
  CircleCheck, CircleClose, QuestionFilled, OfficeBuilding, Loading
} from '@element-plus/icons-vue'
import { serversAPI, authAPI } from '@/api'
import StatusBadge from '@/components/StatusBadge.vue'

const router = useRouter()
const route = useRoute()
const servers = ref([])
const checkingAll = ref(false)
const currentUser = ref(null)
const loading = ref(false)
const loadError = ref('')

const activeMenu = computed(() => route.path)

const stats = reactive({
  total: 0,
  online: 0,
  offline: 0,
  unknown: 0
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
  stats.online = servers.value.filter(s => s.status === 'online').length
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
  router.push(index)
}

const handleCommand = async (command) => {
  if (command === 'logout') {
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
</script>

<style scoped>
.user-dropdown {
  display: flex;
  align-items: center;
  gap: 5px;
  cursor: pointer;
  padding: 10px;
  color: white;
}

.user-dropdown:hover {
  background-color: rgba(255, 255, 255, 0.1);
  border-radius: 4px;
}
</style>
