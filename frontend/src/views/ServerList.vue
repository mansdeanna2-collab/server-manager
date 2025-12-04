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
          <el-card>
            <template #header>
              <div class="card-header">
                <span>Server List</span>
                <div>
                  <el-button type="primary" @click="showAddDialog">
                    <el-icon><Plus /></el-icon>
                    Add Server
                  </el-button>
                  <el-button @click="loadServers">
                    <el-icon><Refresh /></el-icon>
                    Refresh
                  </el-button>
                </div>
              </div>
            </template>
            
            <el-input
              v-model="searchText"
              placeholder="Search by IP or username"
              style="margin-bottom: 20px; max-width: 300px;"
              :prefix-icon="Search"
              clearable
            />
            
            <el-empty v-if="filteredServers.length === 0" description="No servers found" />
            
            <el-table v-else :data="filteredServers" style="width: 100%">
              <el-table-column prop="ip_address" label="IP Address" width="150" />
              <el-table-column prop="port" label="Port" width="100" />
              <el-table-column prop="username" label="Username" width="120" />
              <el-table-column label="Status" width="120">
                <template #default="scope">
                  <StatusBadge :status="scope.row.status" />
                </template>
              </el-table-column>
              <el-table-column prop="os_info" label="OS Info" />
              <el-table-column prop="notes" label="Notes" />
              <el-table-column label="Actions" width="300">
                <template #default="scope">
                  <el-button
                    size="small"
                    @click="viewServer(scope.row)"
                  >
                    <el-icon><View /></el-icon>
                    View
                  </el-button>
                  <el-button
                    size="small"
                    type="primary"
                    @click="editServer(scope.row)"
                  >
                    <el-icon><Edit /></el-icon>
                    Edit
                  </el-button>
                  <el-button
                    size="small"
                    type="success"
                    @click="checkServer(scope.row)"
                    :loading="scope.row.checking"
                  >
                    <el-icon><Refresh /></el-icon>
                    Check
                  </el-button>
                  <el-button
                    size="small"
                    type="danger"
                    @click="deleteServer(scope.row)"
                  >
                    <el-icon><Delete /></el-icon>
                    Delete
                  </el-button>
                </template>
              </el-table-column>
            </el-table>
          </el-card>
        </div>
      </el-main>
    </el-container>
    
    <!-- Add/Edit Server Dialog -->
    <el-dialog
      v-model="dialogVisible"
      :title="isEdit ? 'Edit Server' : 'Add Server'"
      width="600px"
    >
      <ServerForm
        :server="currentServer"
        :is-edit="isEdit"
        @submit="handleSubmit"
        @cancel="dialogVisible = false"
      />
    </el-dialog>
    
    <!-- View Server Detail Dialog -->
    <el-dialog
      v-model="detailDialogVisible"
      title="Server Details"
      width="700px"
    >
      <div v-if="selectedServer">
        <el-descriptions :column="2" border>
          <el-descriptions-item label="IP Address">
            {{ selectedServer.ip_address }}
          </el-descriptions-item>
          <el-descriptions-item label="Port">
            {{ selectedServer.port }}
          </el-descriptions-item>
          <el-descriptions-item label="Username">
            {{ selectedServer.username }}
          </el-descriptions-item>
          <el-descriptions-item label="Status">
            <StatusBadge :status="selectedServer.status" />
          </el-descriptions-item>
          <el-descriptions-item label="OS Info" :span="2">
            {{ selectedServer.os_info || 'N/A' }}
          </el-descriptions-item>
          <el-descriptions-item label="CPU Info" :span="2">
            {{ selectedServer.cpu_info || 'N/A' }}
          </el-descriptions-item>
          <el-descriptions-item label="Memory Info" :span="2">
            {{ selectedServer.memory_info || 'N/A' }}
          </el-descriptions-item>
          <el-descriptions-item label="Disk Info" :span="2">
            {{ selectedServer.disk_info || 'N/A' }}
          </el-descriptions-item>
          <el-descriptions-item label="Uptime" :span="2">
            {{ selectedServer.uptime || 'N/A' }}
          </el-descriptions-item>
          <el-descriptions-item label="Notes" :span="2">
            {{ selectedServer.notes || 'N/A' }}
          </el-descriptions-item>
          <el-descriptions-item label="Last Checked" :span="2">
            {{ formatDate(selectedServer.last_checked) }}
          </el-descriptions-item>
        </el-descriptions>
        
        <div style="margin-top: 20px; text-align: right;">
          <el-button
            type="primary"
            @click="refreshSystemInfo"
            :loading="refreshing"
          >
            <el-icon><Refresh /></el-icon>
            Refresh System Info
          </el-button>
        </div>
      </div>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  Monitor, Odometer, Server, User, ArrowDown, Plus, Refresh,
  Search, View, Edit, Delete
} from '@element-plus/icons-vue'
import { serversAPI, authAPI } from '@/api'
import StatusBadge from '@/components/StatusBadge.vue'
import ServerForm from '@/components/ServerForm.vue'

const router = useRouter()
const route = useRoute()
const servers = ref([])
const searchText = ref('')
const dialogVisible = ref(false)
const detailDialogVisible = ref(false)
const isEdit = ref(false)
const currentServer = ref(null)
const selectedServer = ref(null)
const refreshing = ref(false)
const currentUser = ref(null)

const activeMenu = computed(() => route.path)

const filteredServers = computed(() => {
  if (!searchText.value) return servers.value
  
  const search = searchText.value.toLowerCase()
  return servers.value.filter(server =>
    server.ip_address.toLowerCase().includes(search) ||
    server.username.toLowerCase().includes(search)
  )
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
  } catch (error) {
    ElMessage.error('Failed to load servers')
  }
}

const showAddDialog = () => {
  isEdit.value = false
  currentServer.value = null
  dialogVisible.value = true
}

const editServer = (server) => {
  isEdit.value = true
  currentServer.value = server
  dialogVisible.value = true
}

const viewServer = (server) => {
  selectedServer.value = server
  detailDialogVisible.value = true
}

const handleSubmit = async (formData) => {
  try {
    if (isEdit.value) {
      await serversAPI.update(currentServer.value.id, formData)
      ElMessage.success('Server updated successfully')
    } else {
      await serversAPI.create(formData)
      ElMessage.success('Server added successfully')
    }
    dialogVisible.value = false
    await loadServers()
  } catch (error) {
    ElMessage.error(error.response?.data?.message || 'Operation failed')
  }
}

const deleteServer = async (server) => {
  try {
    await ElMessageBox.confirm(
      `Are you sure you want to delete server ${server.ip_address}?`,
      'Warning',
      {
        confirmButtonText: 'Delete',
        cancelButtonText: 'Cancel',
        type: 'warning'
      }
    )
    
    await serversAPI.delete(server.id)
    ElMessage.success('Server deleted successfully')
    await loadServers()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('Failed to delete server')
    }
  }
}

const checkServer = async (server) => {
  server.checking = true
  try {
    const response = await serversAPI.check(server.id)
    server.status = response.data.status.overall
    server.last_checked = new Date().toISOString()
    ElMessage.success(`Server ${server.ip_address} checked`)
  } catch (error) {
    ElMessage.error('Failed to check server')
  } finally {
    server.checking = false
  }
}

const refreshSystemInfo = async () => {
  if (!selectedServer.value) return
  
  refreshing.value = true
  try {
    const response = await serversAPI.getSystemInfo(selectedServer.value.id)
    selectedServer.value.os_info = response.data.os
    selectedServer.value.cpu_info = response.data.cpu
    selectedServer.value.memory_info = response.data.memory
    selectedServer.value.disk_info = response.data.disk
    selectedServer.value.uptime = response.data.uptime
    ElMessage.success('System info refreshed')
    await loadServers()
  } catch (error) {
    ElMessage.error('Failed to refresh system info')
  } finally {
    refreshing.value = false
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
