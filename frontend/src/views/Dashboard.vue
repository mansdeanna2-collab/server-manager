<template>
  <div class="page-container">
    <el-container>
      <el-header style="background: #409EFF; color: white; display: flex; align-items: center; justify-content: space-between;">
        <div style="display: flex; align-items: center; gap: 10px;">
          <el-icon :size="30"><Monitor /></el-icon>
          <h2 style="margin: 0;">Server Manager</h2>
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
            Dashboard
          </el-menu-item>
          <el-menu-item index="/servers">
            <el-icon><Server /></el-icon>
            Servers
          </el-menu-item>
        </el-menu>
        <el-dropdown @command="handleCommand">
          <span class="user-dropdown">
            <el-icon><User /></el-icon>
            {{ currentUser?.username || 'Admin' }}
            <el-icon><ArrowDown /></el-icon>
          </span>
          <template #dropdown>
            <el-dropdown-menu>
              <el-dropdown-item command="logout">Logout</el-dropdown-item>
            </el-dropdown-menu>
          </template>
        </el-dropdown>
      </el-header>
      
      <el-main>
        <div class="content-wrapper">
          <div class="stats-grid">
            <div class="stat-card">
              <div class="stat-card-icon" style="color: #409EFF;">
                <el-icon><Server /></el-icon>
              </div>
              <div class="stat-card-title">Total Servers</div>
              <div class="stat-card-value">{{ stats.total }}</div>
            </div>
            
            <div class="stat-card">
              <div class="stat-card-icon" style="color: #67C23A;">
                <el-icon><CircleCheck /></el-icon>
              </div>
              <div class="stat-card-title">Online</div>
              <div class="stat-card-value">{{ stats.online }}</div>
            </div>
            
            <div class="stat-card">
              <div class="stat-card-icon" style="color: #F56C6C;">
                <el-icon><CircleClose /></el-icon>
              </div>
              <div class="stat-card-title">Offline</div>
              <div class="stat-card-value">{{ stats.offline }}</div>
            </div>
            
            <div class="stat-card">
              <div class="stat-card-icon" style="color: #909399;">
                <el-icon><QuestionFilled /></el-icon>
              </div>
              <div class="stat-card-title">Unknown</div>
              <div class="stat-card-value">{{ stats.unknown }}</div>
            </div>
          </div>
          
          <el-card>
            <template #header>
              <div class="card-header">
                <span>Recent Servers</span>
                <el-button type="primary" @click="checkAllServers" :loading="checkingAll">
                  <el-icon><Refresh /></el-icon>
                  Check All
                </el-button>
              </div>
            </template>
            
            <el-empty v-if="servers.length === 0" description="No servers found" />
            
            <el-table v-else :data="servers" style="width: 100%">
              <el-table-column prop="ip_address" label="IP Address" width="150" />
              <el-table-column prop="port" label="Port" width="100" />
              <el-table-column prop="username" label="Username" width="120" />
              <el-table-column label="Status" width="120">
                <template #default="scope">
                  <StatusBadge :status="scope.row.status" />
                </template>
              </el-table-column>
              <el-table-column prop="os_info" label="OS" />
              <el-table-column label="Last Checked" width="180">
                <template #default="scope">
                  {{ formatDate(scope.row.last_checked) }}
                </template>
              </el-table-column>
              <el-table-column label="Actions" width="100">
                <template #default="scope">
                  <el-button
                    size="small"
                    type="primary"
                    @click="checkServer(scope.row)"
                    :loading="scope.row.checking"
                  >
                    Check
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
  Monitor, Odometer, Server, User, ArrowDown, Refresh,
  CircleCheck, CircleClose, QuestionFilled
} from '@element-plus/icons-vue'
import { serversAPI, authAPI } from '@/api'
import StatusBadge from '@/components/StatusBadge.vue'

const router = useRouter()
const route = useRoute()
const servers = ref([])
const checkingAll = ref(false)
const currentUser = ref(null)

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
  try {
    const response = await serversAPI.getAll()
    servers.value = response.data.map(s => ({ ...s, checking: false }))
    calculateStats()
  } catch (error) {
    ElMessage.error('Failed to load servers')
  }
}

const calculateStats = () => {
  stats.total = servers.value.length
  stats.online = servers.value.filter(s => s.status === 'online').length
  stats.offline = servers.value.filter(s => s.status === 'offline').length
  stats.unknown = servers.value.filter(s => s.status === 'unknown').length
}

const checkServer = async (server) => {
  server.checking = true
  try {
    const response = await serversAPI.check(server.id)
    server.status = response.data.status.overall
    server.last_checked = new Date().toISOString()
    ElMessage.success(`Server ${server.ip_address} checked`)
    calculateStats()
  } catch (error) {
    ElMessage.error('Failed to check server')
  } finally {
    server.checking = false
  }
}

const checkAllServers = async () => {
  checkingAll.value = true
  try {
    await serversAPI.checkAll()
    await loadServers()
    ElMessage.success('All servers checked')
  } catch (error) {
    ElMessage.error('Failed to check all servers')
  } finally {
    checkingAll.value = false
  }
}

const formatDate = (dateStr) => {
  if (!dateStr) return 'Never'
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
    } catch (error) {
      // Ignore error
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
