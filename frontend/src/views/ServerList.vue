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
          <el-card>
            <template #header>
              <div class="card-header">
                <span>服务器列表</span>
                <div>
                  <el-button
                    type="primary"
                    @click="showAddDialog"
                  >
                    <el-icon><Plus /></el-icon>
                    新增服务器
                  </el-button>
                  <el-button @click="loadServers">
                    <el-icon><Refresh /></el-icon>
                    刷新
                  </el-button>
                </div>
              </div>
            </template>
            
            <el-input
              v-model="searchText"
              placeholder="按IP或用户名搜索"
              style="margin-bottom: 20px; max-width: 300px;"
              :prefix-icon="Search"
              clearable
            />
            
            <el-empty
              v-if="groupedServers.length === 0"
              description="未找到服务器"
            />
            
            <el-table
              v-else
              :data="groupedServers"
              style="width: 100%"
              row-key="segmentKey"
              :tree-props="{ children: 'servers', hasChildren: 'hasChildren' }"
              default-expand-all
            >
              <el-table-column
                label="IP地址"
                width="200"
              >
                <template #default="scope">
                  <span
                    v-if="scope.row.isSegment"
                    class="ip-segment"
                  >
                    {{ scope.row.segment }}.x
                    <el-tag
                      size="small"
                      type="info"
                      style="margin-left: 8px;"
                    >
                      {{ scope.row.count }} 台
                    </el-tag>
                  </span>
                  <span v-else>{{ scope.row.ip_address }}</span>
                </template>
              </el-table-column>
              <el-table-column
                prop="port"
                label="端口"
                width="100"
              >
                <template #default="scope">
                  <span v-if="!scope.row.isSegment">{{ scope.row.port }}</span>
                </template>
              </el-table-column>
              <el-table-column
                prop="username"
                label="用户名"
                width="120"
              >
                <template #default="scope">
                  <span v-if="!scope.row.isSegment">{{ scope.row.username }}</span>
                </template>
              </el-table-column>
              <el-table-column
                label="状态"
                width="120"
              >
                <template #default="scope">
                  <template v-if="scope.row.isSegment">
                    <el-tag
                      v-if="scope.row.onlineCount > 0"
                      type="success"
                      size="small"
                    >
                      {{ scope.row.onlineCount }} 在线
                    </el-tag>
                    <el-tag
                      v-if="scope.row.offlineCount > 0"
                      type="danger"
                      size="small"
                      style="margin-left: 4px;"
                    >
                      {{ scope.row.offlineCount }} 离线
                    </el-tag>
                  </template>
                  <StatusBadge
                    v-else
                    :status="scope.row.status"
                  />
                </template>
              </el-table-column>
              <el-table-column
                prop="os_info"
                label="系统信息"
              >
                <template #default="scope">
                  <span v-if="!scope.row.isSegment">{{ scope.row.os_info }}</span>
                </template>
              </el-table-column>
              <el-table-column
                prop="notes"
                label="备注"
              >
                <template #default="scope">
                  <span v-if="!scope.row.isSegment">{{ scope.row.notes }}</span>
                </template>
              </el-table-column>
              <el-table-column
                label="操作"
                width="300"
              >
                <template #default="scope">
                  <template v-if="scope.row.isSegment">
                    <el-button
                      size="small"
                      @click="viewSegment(scope.row)"
                    >
                      <el-icon><View /></el-icon>
                      查看
                    </el-button>
                  </template>
                  <template v-else>
                    <el-button
                      size="small"
                      @click="viewServer(scope.row)"
                    >
                      <el-icon><View /></el-icon>
                      查看
                    </el-button>
                    <el-button
                      size="small"
                      type="primary"
                      @click="editServer(scope.row)"
                    >
                      <el-icon><Edit /></el-icon>
                      编辑
                    </el-button>
                    <el-button
                      size="small"
                      type="success"
                      :loading="scope.row.checking"
                      @click="checkServer(scope.row)"
                    >
                      <el-icon><Refresh /></el-icon>
                      检测
                    </el-button>
                    <el-button
                      size="small"
                      type="danger"
                      @click="deleteServer(scope.row)"
                    >
                      <el-icon><Delete /></el-icon>
                      删除
                    </el-button>
                  </template>
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
      :title="isEdit ? '编辑服务器' : '新增服务器'"
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
      title="服务器详情"
      width="700px"
    >
      <div v-if="selectedServer">
        <el-descriptions
          :column="2"
          border
        >
          <el-descriptions-item label="IP地址">
            {{ selectedServer.ip_address }}
          </el-descriptions-item>
          <el-descriptions-item label="端口">
            {{ selectedServer.port }}
          </el-descriptions-item>
          <el-descriptions-item label="用户名">
            {{ selectedServer.username }}
          </el-descriptions-item>
          <el-descriptions-item label="状态">
            <StatusBadge :status="selectedServer.status" />
          </el-descriptions-item>
          <el-descriptions-item
            label="系统信息"
            :span="2"
          >
            {{ selectedServer.os_info || '暂无' }}
          </el-descriptions-item>
          <el-descriptions-item
            label="CPU 信息"
            :span="2"
          >
            {{ selectedServer.cpu_info || '暂无' }}
          </el-descriptions-item>
          <el-descriptions-item
            label="内存信息"
            :span="2"
          >
            {{ selectedServer.memory_info || '暂无' }}
          </el-descriptions-item>
          <el-descriptions-item
            label="磁盘信息"
            :span="2"
          >
            {{ selectedServer.disk_info || '暂无' }}
          </el-descriptions-item>
          <el-descriptions-item
            label="运行时间"
            :span="2"
          >
            {{ selectedServer.uptime || '暂无' }}
          </el-descriptions-item>
          <el-descriptions-item
            label="备注"
            :span="2"
          >
            {{ selectedServer.notes || '暂无' }}
          </el-descriptions-item>
          <el-descriptions-item
            label="最近检查"
            :span="2"
          >
            {{ formatDate(selectedServer.last_checked) }}
          </el-descriptions-item>
        </el-descriptions>
        
        <div style="margin-top: 20px; text-align: right;">
          <el-button
            type="primary"
            :loading="refreshing"
            @click="refreshSystemInfo"
          >
            <el-icon><Refresh /></el-icon>
            刷新系统信息
          </el-button>
        </div>
      </div>
    </el-dialog>
    
    <!-- View Segment Servers Dialog -->
    <el-dialog
      v-model="segmentDialogVisible"
      :title="selectedSegment ? `IP段 ${selectedSegment.segment}.x 的服务器` : 'IP段服务器'"
      width="900px"
    >
      <div v-if="selectedSegment">
        <el-table
          :data="selectedSegment.servers"
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
              <StatusBadge :status="scope.row.status" />
            </template>
          </el-table-column>
          <el-table-column
            prop="os_info"
            label="系统信息"
          />
          <el-table-column
            prop="notes"
            label="备注"
          />
          <el-table-column
            label="操作"
            width="180"
          >
            <template #default="scope">
              <el-button
                size="small"
                @click="viewServerFromSegment(scope.row)"
              >
                <el-icon><View /></el-icon>
                详情
              </el-button>
              <el-button
                size="small"
                type="primary"
                @click="editServerFromSegment(scope.row)"
              >
                <el-icon><Edit /></el-icon>
                编辑
              </el-button>
            </template>
          </el-table-column>
        </el-table>
      </div>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  Monitor, Odometer, User, ArrowDown, Plus, Refresh,
  Search, View, Edit, Delete, OfficeBuilding
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
const segmentDialogVisible = ref(false)
const isEdit = ref(false)
const currentServer = ref(null)
const selectedServer = ref(null)
const selectedSegment = ref(null)
const refreshing = ref(false)
const currentUser = ref(null)

const activeMenu = computed(() => route.path)

// Get IP segment (first 3 octets) from IP address
const getIpSegment = (ipAddress) => {
  if (!ipAddress || typeof ipAddress !== 'string') {
    return ''
  }
  const parts = ipAddress.split('.')
  if (parts.length >= 3) {
    return `${parts[0]}.${parts[1]}.${parts[2]}`
  }
  return ipAddress
}

// Compare IP segments numerically
const compareIpSegments = (a, b) => {
  const partsA = a.segment.split('.').map(Number)
  const partsB = b.segment.split('.').map(Number)
  for (let i = 0; i < Math.min(partsA.length, partsB.length); i++) {
    if (partsA[i] !== partsB[i]) {
      return partsA[i] - partsB[i]
    }
  }
  return partsA.length - partsB.length
}

// Filter servers by search text
const filteredServers = computed(() => {
  if (!searchText.value) return servers.value
  
  const search = searchText.value.toLowerCase()
  return servers.value.filter(server =>
    server.ip_address.toLowerCase().includes(search) ||
    server.username.toLowerCase().includes(search)
  )
})

// Group servers by IP segment
const groupedServers = computed(() => {
  const filtered = filteredServers.value
  const segmentMap = new Map()
  
  // Group servers by IP segment
  filtered.forEach(server => {
    const segment = getIpSegment(server.ip_address)
    if (!segmentMap.has(segment)) {
      segmentMap.set(segment, [])
    }
    segmentMap.get(segment).push(server)
  })
  
  // Convert to tree structure for el-table
  const result = []
  segmentMap.forEach((serverList, segment) => {
    // Count online and offline in single pass
    let onlineCount = 0
    let offlineCount = 0
    for (const s of serverList) {
      if (s.status === 'online') onlineCount++
      else if (s.status === 'offline') offlineCount++
    }
    
    result.push({
      segmentKey: `segment-${segment}`,
      segment: segment,
      isSegment: true,
      count: serverList.length,
      onlineCount: onlineCount,
      offlineCount: offlineCount,
      hasChildren: true,
      servers: serverList.map(s => ({
        ...s,
        segmentKey: `server-${s.id}`
      }))
    })
  })
  
  // Sort by segment numerically
  result.sort(compareIpSegments)
  
  return result
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
  } catch (_error) {
    ElMessage.error('加载服务器失败')
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

const viewSegment = (segment) => {
  selectedSegment.value = segment
  segmentDialogVisible.value = true
}

const viewServerFromSegment = (server) => {
  selectedServer.value = server
  detailDialogVisible.value = true
}

const editServerFromSegment = (server) => {
  isEdit.value = true
  currentServer.value = server
  dialogVisible.value = true
}

const handleSubmit = async (formData) => {
  try {
    if (isEdit.value) {
      await serversAPI.update(currentServer.value.id, formData)
      ElMessage.success('服务器更新成功')
    } else {
      await serversAPI.create(formData)
      ElMessage.success('服务器新增成功')
    }
    dialogVisible.value = false
    await loadServers()
  } catch (error) {
    ElMessage.error(error.response?.data?.message || '操作失败')
  }
}

const deleteServer = async (server) => {
  try {
    await ElMessageBox.confirm(
      `确认删除服务器 ${server.ip_address} 吗？`,
      '警告',
      {
        confirmButtonText: '删除',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )
    
    await serversAPI.delete(server.id)
    ElMessage.success('删除服务器成功')
    await loadServers()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('删除服务器失败')
    }
  }
}

const checkServer = async (server) => {
  server.checking = true
  try {
    const response = await serversAPI.check(server.id)
    server.status = response.data.status.overall
    server.last_checked = new Date().toISOString()
    ElMessage.success(`已检测服务器 ${server.ip_address}`)
  } catch (_error) {
    ElMessage.error('检测服务器失败')
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
    ElMessage.success('系统信息已刷新')
    await loadServers()
  } catch (_error) {
    ElMessage.error('刷新系统信息失败')
  } finally {
    refreshing.value = false
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

.ip-segment {
  font-weight: bold;
  color: #409EFF;
}
</style>
