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
          background-color="#409EFF"
          text-color="#fff"
          active-text-color="#ffd04b"
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
          <el-card class="server-card">
            <template #header>
              <div class="card-header">
                <span class="card-title">🖥️ 服务器列表</span>
                <div class="header-actions">
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
              placeholder="按IP、用户名或备注搜索"
              class="search-input"
              :prefix-icon="Search"
              clearable
            />
            
            <el-empty
              v-if="groupedServers.length === 0"
              description="未找到服务器"
            />
            
            <!-- IP段卡片网格布局 - 每行2个 -->
            <div
              v-else
              class="segments-grid"
            >
              <div
                v-for="segment in groupedServers"
                :key="segment.segmentKey"
                class="segment-card"
                @click="viewSegment(segment)"
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
                    ✓ 在线 {{ segment.onlineCount }}
                  </el-tag>
                  <el-tag
                    v-if="segment.offlineCount > 0"
                    type="danger"
                    size="small"
                    effect="dark"
                  >
                    ✗ 离线 {{ segment.offlineCount }}
                  </el-tag>
                </div>
                <div class="segment-card-action">
                  <el-button
                    size="small"
                    type="primary"
                    plain
                    @click.stop="viewSegment(segment)"
                  >
                    <el-icon><View /></el-icon>
                    查看详情
                  </el-button>
                </div>
              </div>
            </div>
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
      <div
        v-if="selectedServer"
        class="server-detail"
      >
        <div class="detail-header">
          <div class="detail-title">
            <h3>{{ selectedServer.ip_address }}</h3>
          </div>
          <StatusBadge
            :status="selectedServer.status"
            :detail="selectedServer.checkDetail"
            :error-type="selectedServer.error_type"
          />
        </div>
        
        <el-descriptions
          :column="2"
          border
        >
          <el-descriptions-item label="IP地址">
            {{ selectedServer.ip_address }}
          </el-descriptions-item>
          <el-descriptions-item label="端口">
            <el-tag
              :type="getPortTagType(selectedServer.port)"
              size="small"
              effect="dark"
            >
              {{ getPortTypeIcon(selectedServer.port) }} {{ selectedServer.port }} ({{ getPortTypeName(selectedServer.port) }})
            </el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="用户名">
            {{ selectedServer.username }}
          </el-descriptions-item>
          <el-descriptions-item label="状态">
            <StatusBadge
              :status="selectedServer.status"
              :detail="selectedServer.checkDetail"
              :error-type="selectedServer.error_type"
            />
          </el-descriptions-item>
          <el-descriptions-item
            label="系统信息"
            :span="2"
          >
            <span v-if="selectedServer.os_info">
              {{ getOsIcon(selectedServer.os_info) }} {{ selectedServer.os_info }}
            </span>
            <span
              v-else
              class="no-info"
            >暂无</span>
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
        
        <div class="detail-actions">
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
      width="1100px"
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
        >
          <el-table-column
            label="IP地址"
            width="160"
          >
            <template #default="scope">
              <div class="ip-cell">
                <span class="ip-text">{{ scope.row.ip_address }}</span>
              </div>
            </template>
          </el-table-column>
          <el-table-column
            label="端口 / 配置"
            width="160"
          >
            <template #default="scope">
              <div class="port-cell">
                <div class="port-row">
                  <el-tag
                    :type="getPortTagType(scope.row.port)"
                    size="small"
                    effect="dark"
                    round
                  >
                    {{ getPortTypeIcon(scope.row.port) }} {{ scope.row.port }}
                  </el-tag>
                </div>
                <div
                  v-if="getServerSpecs(scope.row)"
                  class="specs-row"
                >
                  <el-tag
                    size="small"
                    effect="plain"
                    type="info"
                    class="specs-tag"
                  >
                    💻 {{ getServerSpecs(scope.row) }}
                  </el-tag>
                </div>
              </div>
            </template>
          </el-table-column>
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
              <StatusBadge
                :status="scope.row.status"
                :detail="scope.row.checkDetail"
                :error-type="scope.row.error_type"
                size="small"
              />
            </template>
          </el-table-column>
          <el-table-column
            prop="os_info"
            label="系统信息"
            min-width="140"
          >
            <template #default="scope">
              <span v-if="scope.row.os_info">
                {{ getOsIcon(scope.row.os_info) }} {{ scope.row.os_info }}
              </span>
              <span
                v-else
                class="no-info"
              >-</span>
            </template>
          </el-table-column>
          <el-table-column
            prop="notes"
            label="备注"
            min-width="120"
          >
            <template #default="scope">
              <span
                v-if="scope.row.notes"
                class="notes-text"
              >{{ scope.row.notes }}</span>
              <span
                v-else
                class="no-info"
              >-</span>
            </template>
          </el-table-column>
          <el-table-column
            label="操作"
            width="280"
            fixed="right"
          >
            <template #default="scope">
              <div class="action-buttons">
                <el-button
                  size="small"
                  type="success"
                  @click="openTerminal(scope.row)"
                >
                  <el-icon><Connection /></el-icon>
                  连接
                </el-button>
                <el-button
                  size="small"
                  @click="viewServer(scope.row)"
                >
                  <el-icon><View /></el-icon>
                  详情
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
                  type="danger"
                  @click="deleteServer(scope.row)"
                >
                  <el-icon><Delete /></el-icon>
                  删除
                </el-button>
              </div>
            </template>
          </el-table-column>
        </el-table>
      </div>
    </el-dialog>
    
    <!-- Terminal Connection Dialog -->
    <el-dialog
      v-model="terminalDialogVisible"
      :title="`终端 - ${terminalServer?.ip_address || ''}`"
      width="900px"
      class="terminal-dialog"
      append-to-body
      :close-on-click-modal="false"
      @closed="handleTerminalDialogClosed"
    >
      <div
        v-if="terminalServer"
        class="terminal-dialog-content"
      >
        <div class="terminal-header-info">
          <el-descriptions
            :column="4"
            border
            size="small"
          >
            <el-descriptions-item label="IP地址">
              <span class="mono-text">{{ terminalServer.ip_address }}</span>
            </el-descriptions-item>
            <el-descriptions-item label="端口">
              <el-tag
                :type="getPortTagType(terminalServer.port)"
                size="small"
                effect="dark"
              >
                {{ terminalServer.port }}
              </el-tag>
            </el-descriptions-item>
            <el-descriptions-item label="用户名">
              <span class="mono-text">{{ terminalServer.username }}</span>
            </el-descriptions-item>
            <el-descriptions-item label="状态">
              <StatusBadge
                :status="terminalServer.status"
                size="small"
              />
            </el-descriptions-item>
          </el-descriptions>
        </div>
        
        <Terminal
          v-if="terminalServer.port !== 3389"
          ref="terminalRef"
          :server="terminalServer"
          :visible="terminalDialogVisible"
          @connected="handleTerminalConnected"
          @disconnected="handleTerminalDisconnected"
          @error="handleTerminalError"
        />
        
        <div
          v-else
          class="rdp-info"
        >
          <el-alert
            title="Windows 远程桌面"
            type="warning"
            :closable="false"
            show-icon
          >
            <template #default>
              <p>端口 3389 为 Windows RDP 服务，请使用系统远程桌面连接。</p>
              <div class="rdp-command-box">
                <code class="rdp-command">{{ getSshCommand(terminalServer) }}</code>
                <el-button
                  type="primary"
                  size="small"
                  @click="copySshCommand(terminalServer)"
                >
                  <el-icon><CopyDocument /></el-icon>
                  复制命令
                </el-button>
              </div>
            </template>
          </el-alert>
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
  Monitor, Odometer, User, ArrowDown, Plus, Refresh,
  Search, View, Edit, Delete, OfficeBuilding, Connection, CopyDocument
} from '@element-plus/icons-vue'
import { serversAPI, authAPI } from '@/api'
import StatusBadge from '@/components/StatusBadge.vue'
import ServerForm from '@/components/ServerForm.vue'
import Terminal from '@/components/Terminal.vue'

const router = useRouter()
const route = useRoute()
const servers = ref([])
const searchText = ref('')
const dialogVisible = ref(false)
const detailDialogVisible = ref(false)
const segmentDialogVisible = ref(false)
const terminalDialogVisible = ref(false)
const isEdit = ref(false)
const currentServer = ref(null)
const selectedServer = ref(null)
const selectedSegment = ref(null)
const terminalServer = ref(null)
const terminalRef = ref(null)
const refreshing = ref(false)
const currentUser = ref(null)

const activeMenu = computed(() => route.path)

// 端口类型信息
const PORT_TYPE_MAP = {
  22: { type: 'SSH', osHint: 'Linux/Unix', icon: '🐧', color: 'success' },
  3389: { type: 'RDP', osHint: 'Windows', icon: '🪟', color: 'primary' },
  23: { type: 'Telnet', osHint: 'Network', icon: '📡', color: 'warning' },
  21: { type: 'FTP', osHint: 'File', icon: '📁', color: 'info' },
  80: { type: 'HTTP', osHint: 'Web', icon: '🌐', color: '' },
  443: { type: 'HTTPS', osHint: 'Web', icon: '🔒', color: 'success' },
  3306: { type: 'MySQL', osHint: 'DB', icon: '🗄️', color: 'warning' },
  5432: { type: 'PostgreSQL', osHint: 'DB', icon: '🐘', color: 'primary' },
}

const getPortTypeName = (port) => {
  return PORT_TYPE_MAP[port]?.type || 'Custom'
}

const getPortTypeIcon = (port) => {
  return PORT_TYPE_MAP[port]?.icon || '🔌'
}

const getPortTagType = (port) => {
  return PORT_TYPE_MAP[port]?.color || 'info'
}

// 获取服务器配置信息（CPU核数和内存大小）
const getServerSpecs = (server) => {
  if (!server.cpu_info && !server.memory_info) return null
  
  // 解析CPU核数
  let cpuCores = ''
  if (server.cpu_info) {
    // 尝试匹配常见的CPU信息格式
    const cpuMatch = server.cpu_info.match(/(\d+)\s*(核|cores?|cpus?|processors?)/i)
    if (cpuMatch) {
      cpuCores = cpuMatch[1]
    } else {
      // 如果是纯数字
      const numMatch = server.cpu_info.match(/^(\d+)$/)
      if (numMatch) {
        cpuCores = numMatch[1]
      }
    }
  }
  
  // 解析内存大小
  let memorySize = ''
  if (server.memory_info) {
    // 尝试匹配内存信息格式，如 "4GB", "4 GB", "4G", "4096MB"
    const memMatch = server.memory_info.match(/(\d+(?:\.\d+)?)\s*(GB|G|MB|M|TB|T)/i)
    if (memMatch) {
      let size = parseFloat(memMatch[1])
      const unit = memMatch[2].toUpperCase()
      // 转换为GB显示 (使用二进制转换 1024，符合计算机内存标准)
      if (unit === 'MB' || unit === 'M') {
        size = Math.round(size / 1024)
        memorySize = size > 0 ? `${size}G` : '<1G'
      } else if (unit === 'TB' || unit === 'T') {
        size = size * 1024
        memorySize = `${Math.round(size)}G`
      } else {
        memorySize = `${Math.round(size)}G`
      }
    } else {
      // 处理纯数字（假设为MB）
      const numMatch = server.memory_info.match(/^(\d+)$/)
      if (numMatch) {
        const sizeMB = parseInt(numMatch[1])
        const sizeGB = Math.round(sizeMB / 1024)
        memorySize = sizeGB > 0 ? `${sizeGB}G` : '<1G'
      }
    }
  }
  
  // 组合显示
  if (cpuCores && memorySize) {
    return `${cpuCores}核${memorySize}`
  } else if (cpuCores) {
    return `${cpuCores}核`
  } else if (memorySize) {
    return memorySize
  }
  return null
}

// 根据OS信息获取图标
const getOsIcon = (osInfo) => {
  if (!osInfo) return '💻'
  const osLower = osInfo.toLowerCase()
  if (osLower.includes('ubuntu') || osLower.includes('debian')) return '🐧'
  if (osLower.includes('centos') || osLower.includes('red hat') || osLower.includes('rhel')) return '🎩'
  if (osLower.includes('windows')) return '🪟'
  if (osLower.includes('mac') || osLower.includes('darwin')) return '🍎'
  if (osLower.includes('linux')) return '🐧'
  return '💻'
}

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
    server.username.toLowerCase().includes(search) ||
    (server.notes && server.notes.toLowerCase().includes(search))
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
    servers.value = response.data.map(s => ({
      ...s,
      checking: false,
      checkDetail: s.checkDetail || '',
      error_type: s.error_type || ''
    }))
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

// 终端连接功能
const openTerminal = (server) => {
  terminalServer.value = server
  terminalDialogVisible.value = true
}

const handleTerminalDialogClosed = () => {
  // 关闭对话框时断开终端连接
  if (terminalRef.value) {
    terminalRef.value.disconnect()
  }
}

const handleTerminalConnected = () => {
  ElMessage.success('终端连接成功')
}

const handleTerminalDisconnected = () => {
  ElMessage.info('终端已断开')
}

const handleTerminalError = (errorMsg) => {
  ElMessage.error(errorMsg || '终端连接失败')
}

const getSshCommand = (server) => {
  if (!server) return ''
  if (server.port === 22) {
    return `ssh ${server.username}@${server.ip_address}`
  } else if (server.port === 3389) {
    return `mstsc /v:${server.ip_address}`
  } else {
    return `ssh -p ${server.port} ${server.username}@${server.ip_address}`
  }
}

const copySshCommand = async (server) => {
  const command = getSshCommand(server)
  try {
    await navigator.clipboard.writeText(command)
    ElMessage.success('命令已复制到剪贴板')
  } catch (_error) {
    ElMessage.error('复制失败，请手动复制')
  }
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
/* Page container */
.page-container {
  min-height: 100vh;
  background: linear-gradient(135deg, #f5f7fa 0%, #e4e7ed 100%);
}

/* Header styles */
.header-container {
  background: linear-gradient(135deg, #409EFF 0%, #337ecc 100%);
  color: white;
  display: flex;
  align-items: center;
  justify-content: space-between;
  box-shadow: 0 4px 20px 0 rgba(64, 158, 255, 0.3);
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
}

.user-dropdown {
  display: flex;
  align-items: center;
  gap: 5px;
  cursor: pointer;
  padding: 10px;
  color: white;
  transition: all 0.3s;
}

.user-dropdown:hover {
  background-color: rgba(255, 255, 255, 0.1);
  border-radius: 4px;
}

/* Content wrapper */
.content-wrapper {
  padding: 20px;
  max-width: 1400px;
  margin: 0 auto;
}

/* Card styles */
.server-card {
  border-radius: 12px;
  box-shadow: 0 4px 20px 0 rgba(0, 0, 0, 0.08);
  border: none;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.card-title {
  font-size: 20px;
  font-weight: 600;
  color: #303133;
}

.header-actions {
  display: flex;
  gap: 10px;
}

.search-input {
  margin-bottom: 24px;
  max-width: 320px;
}

/* IP段卡片网格布局 */
.segments-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 20px;
}

@media (max-width: 768px) {
  .segments-grid {
    grid-template-columns: 1fr;
  }
}

.segment-card {
  background: linear-gradient(135deg, #ffffff 0%, #f9fafc 100%);
  border-radius: 12px;
  padding: 20px;
  cursor: pointer;
  transition: all 0.3s ease;
  border: 1px solid #e4e7ed;
  box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.05);
}

.segment-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 8px 24px 0 rgba(64, 158, 255, 0.2);
  border-color: #409EFF;
}

.segment-card-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 16px;
}

.ip-segment-title {
  font-size: 18px;
  font-weight: 700;
  color: #409EFF;
  font-family: 'Monaco', 'Menlo', 'Consolas', monospace;
}

.count-tag {
  background: linear-gradient(135deg, #f0f9eb 0%, #e8f5e1 100%);
  border-color: #c2e7b0;
  color: #67c23a;
}

.segment-card-status {
  display: flex;
  gap: 8px;
  margin-bottom: 16px;
}

.segment-card-action {
  display: flex;
  justify-content: flex-end;
}

/* IP cell styles */
.ip-cell {
  display: flex;
  align-items: center;
  gap: 8px;
}

.ip-text {
  font-family: 'Monaco', 'Menlo', 'Consolas', monospace;
  font-size: 13px;
  color: #303133;
  font-weight: 500;
}

/* Port cell styles */
.port-cell {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.port-row {
  display: flex;
  align-items: center;
  gap: 6px;
}

.specs-row {
  display: flex;
  align-items: center;
}

.specs-tag {
  font-size: 11px;
  padding: 2px 8px;
  background: linear-gradient(135deg, #f0f9eb 0%, #e8f5e1 100%);
  border-color: #c2e7b0;
  color: #67c23a;
  font-weight: 500;
}

/* Notes text in table */
.notes-text {
  color: #606266;
  font-size: 13px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  display: block;
  max-width: 150px;
}

/* Action buttons in table */
.action-buttons {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
}

/* No info text */
.no-info {
  color: #c0c4cc;
}

/* Server detail dialog */
.server-detail {
  padding: 10px;
}

.detail-header {
  display: flex;
  align-items: center;
  gap: 15px;
  margin-bottom: 20px;
  padding-bottom: 15px;
  border-bottom: 1px solid #ebeef5;
}

.detail-title {
  flex: 1;
}

.detail-title h3 {
  margin: 0 0 5px 0;
  font-size: 20px;
  color: #303133;
  font-family: 'Monaco', 'Menlo', 'Consolas', monospace;
}

.detail-actions {
  margin-top: 20px;
  text-align: right;
}

/* Segment dialog header */
.segment-header {
  display: flex;
  align-items: center;
  gap: 15px;
  margin-bottom: 20px;
  padding-bottom: 15px;
  border-bottom: 1px solid #ebeef5;
}

.segment-count {
  color: #909399;
  font-size: 14px;
}

/* Terminal dialog styles */
.terminal-dialog :deep(.el-dialog__body) {
  padding: 20px;
}

.terminal-dialog-content {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.terminal-header-info {
  margin-bottom: 8px;
}

.rdp-info {
  margin-top: 16px;
}

.rdp-command-box {
  display: flex;
  align-items: center;
  gap: 12px;
  background: #1e1e1e;
  padding: 12px 16px;
  border-radius: 6px;
  margin-top: 12px;
}

.rdp-command {
  flex: 1;
  font-family: 'Monaco', 'Menlo', 'Consolas', monospace;
  font-size: 14px;
  color: #67c23a;
}

.mono-text {
  font-family: 'Monaco', 'Menlo', 'Consolas', monospace;
}

/* Segment dialog styles */
.segment-dialog :deep(.el-dialog__body) {
  padding: 20px;
}

/* Animations */
@keyframes pulse {
  0% {
    opacity: 1;
  }
  50% {
    opacity: 0.5;
  }
  100% {
    opacity: 1;
  }
}

:deep(.el-table__row.is-checking) {
  animation: pulse 1s infinite;
}

/* Table styling */
:deep(.el-table) {
  border-radius: 8px;
  overflow: hidden;
}

:deep(.el-table th) {
  background-color: #f5f7fa !important;
  font-weight: 600;
}

:deep(.el-table--striped .el-table__body tr.el-table__row--striped td) {
  background: #fafafa;
}
</style>
