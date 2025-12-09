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
              placeholder="按IP或用户名搜索"
              class="search-input"
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
              :row-class-name="getRowClassName"
            >
              <el-table-column
                label="IP地址 / 地区"
                min-width="280"
              >
                <template #default="scope">
                  <div class="segment-cell">
                    <span class="segment-flag">{{ scope.row.regionInfo?.flag || '🌐' }}</span>
                    <span class="ip-segment">{{ scope.row.segment }}.x</span>
                    <el-tag
                      size="small"
                      type="info"
                      class="count-tag"
                    >
                      {{ scope.row.count }} 台
                    </el-tag>
                    <el-tag
                      v-if="scope.row.regionInfo?.name"
                      size="small"
                      class="region-tag"
                      effect="plain"
                    >
                      {{ scope.row.regionInfo.name }}
                    </el-tag>
                  </div>
                </template>
              </el-table-column>
              <el-table-column
                label="状态"
                width="140"
              >
                <template #default="scope">
                  <div class="segment-status">
                    <el-tag
                      v-if="scope.row.onlineCount > 0"
                      type="success"
                      size="small"
                      effect="dark"
                    >
                      ✓ {{ scope.row.onlineCount }}
                    </el-tag>
                    <el-tag
                      v-if="scope.row.offlineCount > 0"
                      type="danger"
                      size="small"
                      effect="dark"
                    >
                      ✗ {{ scope.row.offlineCount }}
                    </el-tag>
                  </div>
                </template>
              </el-table-column>
              <el-table-column
                label="操作"
                width="120"
                fixed="right"
              >
                <template #default="scope">
                  <el-button
                    size="small"
                    type="primary"
                    @click="viewSegment(scope.row)"
                  >
                    <el-icon><View /></el-icon>
                    查看
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
          <span class="region-flag-large">{{ getRegionInfo(selectedServer.ip_address)?.flag || '🌐' }}</span>
          <div class="detail-title">
            <h3>{{ selectedServer.ip_address }}</h3>
            <el-tag
              v-if="getRegionInfo(selectedServer.ip_address)?.name"
              size="small"
              effect="plain"
            >
              {{ getRegionInfo(selectedServer.ip_address)?.name }}
            </el-tag>
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
      :title="selectedSegment ? `${selectedSegment.regionInfo?.flag || '🌐'} IP段 ${selectedSegment.segment}.x 的服务器` : 'IP段服务器'"
      width="1100px"
    >
      <div v-if="selectedSegment">
        <div class="segment-header">
          <el-tag
            size="large"
            effect="plain"
          >
            {{ selectedSegment.regionInfo?.flag || '🌐' }} {{ selectedSegment.regionInfo?.name || '未知地区' }}
          </el-tag>
          <span class="segment-count">共 {{ selectedSegment.count }} 台服务器</span>
        </div>
        <el-table
          :data="selectedSegment.servers"
          style="width: 100%"
        >
          <el-table-column
            label="IP地址"
            width="180"
          >
            <template #default="scope">
              <div class="ip-cell">
                <span class="region-flag">{{ getRegionInfo(scope.row.ip_address)?.flag || '🌐' }}</span>
                <span>{{ scope.row.ip_address }}</span>
              </div>
            </template>
          </el-table-column>
          <el-table-column
            label="端口 / 配置"
            width="180"
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
                size="small"
              />
            </template>
          </el-table-column>
          <el-table-column
            prop="os_info"
            label="系统信息"
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
          />
          <el-table-column
            label="操作"
            width="300"
          >
            <template #default="scope">
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

// IP段到地区的映射表（前端简化版）
const IP_REGION_MAP = {
  // 香港 (Hong Kong)
  '38.47.': { code: 'HK', name: '香港', flag: '🇭🇰' },
  '103.10.': { code: 'HK', name: '香港', flag: '🇭🇰' },
  '103.11.': { code: 'HK', name: '香港', flag: '🇭🇰' },
  '103.12.': { code: 'HK', name: '香港', flag: '🇭🇰' },
  '119.28.': { code: 'HK', name: '香港', flag: '🇭🇰' },
  '119.29.': { code: 'HK', name: '香港', flag: '🇭🇰' },
  '150.109.': { code: 'HK', name: '香港', flag: '🇭🇰' },
  '162.14.': { code: 'HK', name: '香港', flag: '🇭🇰' },
  '175.24.': { code: 'HK', name: '香港', flag: '🇭🇰' },
  // 新加坡 (Singapore)
  '13.212.': { code: 'SG', name: '新加坡', flag: '🇸🇬' },
  '13.213.': { code: 'SG', name: '新加坡', flag: '🇸🇬' },
  '13.214.': { code: 'SG', name: '新加坡', flag: '🇸🇬' },
  '13.215.': { code: 'SG', name: '新加坡', flag: '🇸🇬' },
  '18.136.': { code: 'SG', name: '新加坡', flag: '🇸🇬' },
  '18.137.': { code: 'SG', name: '新加坡', flag: '🇸🇬' },
  '18.138.': { code: 'SG', name: '新加坡', flag: '🇸🇬' },
  '18.139.': { code: 'SG', name: '新加坡', flag: '🇸🇬' },
  '18.140.': { code: 'SG', name: '新加坡', flag: '🇸🇬' },
  '18.141.': { code: 'SG', name: '新加坡', flag: '🇸🇬' },
  '52.74.': { code: 'SG', name: '新加坡', flag: '🇸🇬' },
  '52.76.': { code: 'SG', name: '新加坡', flag: '🇸🇬' },
  '52.77.': { code: 'SG', name: '新加坡', flag: '🇸🇬' },
  '54.179.': { code: 'SG', name: '新加坡', flag: '🇸🇬' },
  '54.251.': { code: 'SG', name: '新加坡', flag: '🇸🇬' },
  '54.254.': { code: 'SG', name: '新加坡', flag: '🇸🇬' },
  '54.255.': { code: 'SG', name: '新加坡', flag: '🇸🇬' },
  // 美国 (United States) - AWS US regions
  '3.80.': { code: 'US', name: '美国', flag: '🇺🇸' },
  '3.81.': { code: 'US', name: '美国', flag: '🇺🇸' },
  '3.82.': { code: 'US', name: '美国', flag: '🇺🇸' },
  '3.83.': { code: 'US', name: '美国', flag: '🇺🇸' },
  '3.208.': { code: 'US', name: '美国', flag: '🇺🇸' },
  '3.209.': { code: 'US', name: '美国', flag: '🇺🇸' },
  '3.210.': { code: 'US', name: '美国', flag: '🇺🇸' },
  '34.192.': { code: 'US', name: '美国', flag: '🇺🇸' },
  '34.193.': { code: 'US', name: '美国', flag: '🇺🇸' },
  '34.194.': { code: 'US', name: '美国', flag: '🇺🇸' },
  '34.208.': { code: 'US', name: '美国', flag: '🇺🇸' },
  '34.209.': { code: 'US', name: '美国', flag: '🇺🇸' },
  '34.210.': { code: 'US', name: '美国', flag: '🇺🇸' },
  '52.0.': { code: 'US', name: '美国', flag: '🇺🇸' },
  '52.1.': { code: 'US', name: '美国', flag: '🇺🇸' },
  '52.2.': { code: 'US', name: '美国', flag: '🇺🇸' },
  '52.20.': { code: 'US', name: '美国', flag: '🇺🇸' },
  '52.21.': { code: 'US', name: '美国', flag: '🇺🇸' },
  '52.22.': { code: 'US', name: '美国', flag: '🇺🇸' },
  '54.80.': { code: 'US', name: '美国', flag: '🇺🇸' },
  '54.81.': { code: 'US', name: '美国', flag: '🇺🇸' },
  '54.82.': { code: 'US', name: '美国', flag: '🇺🇸' },
  '54.144.': { code: 'US', name: '美国', flag: '🇺🇸' },
  '54.145.': { code: 'US', name: '美国', flag: '🇺🇸' },
  '104.196.': { code: 'US', name: '美国', flag: '🇺🇸' },
  '104.197.': { code: 'US', name: '美国', flag: '🇺🇸' },
  // 日本 (Japan)
  '13.112.': { code: 'JP', name: '日本', flag: '🇯🇵' },
  '13.113.': { code: 'JP', name: '日本', flag: '🇯🇵' },
  '13.114.': { code: 'JP', name: '日本', flag: '🇯🇵' },
  '13.115.': { code: 'JP', name: '日本', flag: '🇯🇵' },
  '18.176.': { code: 'JP', name: '日本', flag: '🇯🇵' },
  '18.177.': { code: 'JP', name: '日本', flag: '🇯🇵' },
  '18.178.': { code: 'JP', name: '日本', flag: '🇯🇵' },
  '52.68.': { code: 'JP', name: '日本', flag: '🇯🇵' },
  '52.69.': { code: 'JP', name: '日本', flag: '🇯🇵' },
  '52.192.': { code: 'JP', name: '日本', flag: '🇯🇵' },
  '52.193.': { code: 'JP', name: '日本', flag: '🇯🇵' },
  '54.64.': { code: 'JP', name: '日本', flag: '🇯🇵' },
  '54.65.': { code: 'JP', name: '日本', flag: '🇯🇵' },
  '54.178.': { code: 'JP', name: '日本', flag: '🇯🇵' },
  '54.199.': { code: 'JP', name: '日本', flag: '🇯🇵' },
  // 韩国 (South Korea)
  '13.124.': { code: 'KR', name: '韩国', flag: '🇰🇷' },
  '13.125.': { code: 'KR', name: '韩国', flag: '🇰🇷' },
  '13.209.': { code: 'KR', name: '韩国', flag: '🇰🇷' },
  '15.164.': { code: 'KR', name: '韩国', flag: '🇰🇷' },
  '15.165.': { code: 'KR', name: '韩国', flag: '🇰🇷' },
  '52.78.': { code: 'KR', name: '韩国', flag: '🇰🇷' },
  '52.79.': { code: 'KR', name: '韩国', flag: '🇰🇷' },
  // 德国 (Germany)
  '3.120.': { code: 'DE', name: '德国', flag: '🇩🇪' },
  '3.121.': { code: 'DE', name: '德国', flag: '🇩🇪' },
  '3.122.': { code: 'DE', name: '德国', flag: '🇩🇪' },
  '18.184.': { code: 'DE', name: '德国', flag: '🇩🇪' },
  '52.28.': { code: 'DE', name: '德国', flag: '🇩🇪' },
  '52.29.': { code: 'DE', name: '德国', flag: '🇩🇪' },
  // 英国 (United Kingdom)
  '3.8.': { code: 'UK', name: '英国', flag: '🇬🇧' },
  '3.9.': { code: 'UK', name: '英国', flag: '🇬🇧' },
  '3.10.': { code: 'UK', name: '英国', flag: '🇬🇧' },
  '18.130.': { code: 'UK', name: '英国', flag: '🇬🇧' },
  '35.176.': { code: 'UK', name: '英国', flag: '🇬🇧' },
  '35.177.': { code: 'UK', name: '英国', flag: '🇬🇧' },
  // 台湾 (Taiwan)
  '61.216.': { code: 'TW', name: '台湾', flag: '🇹🇼' },
  '61.217.': { code: 'TW', name: '台湾', flag: '🇹🇼' },
  '114.32.': { code: 'TW', name: '台湾', flag: '🇹🇼' },
  '114.33.': { code: 'TW', name: '台湾', flag: '🇹🇼' },
  // 中国大陆 (China Mainland) - 阿里云
  '47.92.': { code: 'CN', name: '中国', flag: '🇨🇳' },
  '47.93.': { code: 'CN', name: '中国', flag: '🇨🇳' },
  '47.94.': { code: 'CN', name: '中国', flag: '🇨🇳' },
  '47.95.': { code: 'CN', name: '中国', flag: '🇨🇳' },
  '47.96.': { code: 'CN', name: '中国', flag: '🇨🇳' },
  '47.97.': { code: 'CN', name: '中国', flag: '🇨🇳' },
  '47.98.': { code: 'CN', name: '中国', flag: '🇨🇳' },
  '47.99.': { code: 'CN', name: '中国', flag: '🇨🇳' },
  '47.100.': { code: 'CN', name: '中国', flag: '🇨🇳' },
  '47.101.': { code: 'CN', name: '中国', flag: '🇨🇳' },
  '120.76.': { code: 'CN', name: '中国', flag: '🇨🇳' },
  '120.77.': { code: 'CN', name: '中国', flag: '🇨🇳' },
  '120.78.': { code: 'CN', name: '中国', flag: '🇨🇳' },
  '120.79.': { code: 'CN', name: '中国', flag: '🇨🇳' },
  // 腾讯云
  '129.204.': { code: 'CN', name: '中国', flag: '🇨🇳' },
  '129.205.': { code: 'CN', name: '中国', flag: '🇨🇳' },
}

// 获取IP地区信息
const getRegionInfo = (ipAddress) => {
  if (!ipAddress) return { code: 'UNKNOWN', name: '未知', flag: '🌐' }
  
  // 按照前缀长度从长到短排序，优先匹配更精确的
  const sortedPrefixes = Object.keys(IP_REGION_MAP).sort((a, b) => b.length - a.length)
  
  for (const prefix of sortedPrefixes) {
    if (ipAddress.startsWith(prefix)) {
      return IP_REGION_MAP[prefix]
    }
  }
  
  return { code: 'UNKNOWN', name: '未知', flag: '🌐' }
}

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

// 根据OS信息获取标签类型
const _getOsTagType = (osInfo) => {
  if (!osInfo) return 'info'
  const osLower = osInfo.toLowerCase()
  if (osLower.includes('ubuntu')) return 'warning'
  if (osLower.includes('centos')) return 'danger'
  if (osLower.includes('debian')) return 'primary'
  if (osLower.includes('windows')) return 'primary'
  return 'info'
}

// 获取行样式类名
const getRowClassName = ({ row }) => {
  if (row.isSegment) return 'segment-row'
  if (row.status === 'online') return 'online-row'
  if (row.status === 'offline') return 'offline-row'
  return ''
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
    
    // Get region info from first server in segment
    const firstServer = serverList[0]
    const regionInfo = firstServer ? getRegionInfo(firstServer.ip_address) : null
    
    result.push({
      segmentKey: `segment-${segment}`,
      segment: segment,
      isSegment: true,
      count: serverList.length,
      onlineCount: onlineCount,
      offlineCount: offlineCount,
      regionInfo: regionInfo,
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
    const statusData = response.data.status
    server.status = statusData.overall
    server.checkDetail = statusData.detail || ''
    server.error_type = statusData.error_type || ''
    server.last_checked = new Date().toISOString()
    
    // 构建详细的检测结果消息
    let message = `服务器 ${server.ip_address} 检测完成: `
    if (statusData.port_type) {
      message += `${statusData.port_type.icon} ${statusData.port_type.type} `
    }
    if (statusData.region) {
      message += `${statusData.region.flag} ${statusData.region.name} `
    }
    message += `- ${statusData.detail || statusData.overall}`
    
    if (statusData.overall === 'online') {
      ElMessage.success(message)
    } else {
      ElMessage.warning(message)
    }
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
/* Header styles */
.header-container {
  background: linear-gradient(135deg, #409EFF 0%, #337ecc 100%);
  color: white;
  display: flex;
  align-items: center;
  justify-content: space-between;
  box-shadow: 0 2px 12px 0 rgba(64, 158, 255, 0.3);
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

/* Card styles */
.server-card {
  border-radius: 8px;
  box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.1);
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.card-title {
  font-size: 18px;
  font-weight: 600;
  color: #303133;
}

.header-actions {
  display: flex;
  gap: 10px;
}

.search-input {
  margin-bottom: 20px;
  max-width: 300px;
}

/* IP segment styles */
.segment-cell {
  display: flex;
  align-items: center;
  gap: 8px;
}

.segment-flag {
  font-size: 20px;
}

.ip-segment {
  font-weight: bold;
  color: #409EFF;
  font-size: 15px;
}

.count-tag {
  margin-left: 4px;
}

.region-tag {
  margin-left: 4px;
  background-color: #f0f9eb;
  color: #67c23a;
  border-color: #e1f3d8;
}

/* IP cell styles */
.ip-cell {
  display: flex;
  align-items: center;
  gap: 8px;
}

.region-flag {
  font-size: 16px;
}

.ip-address {
  font-family: 'Monaco', 'Menlo', 'Consolas', monospace;
  font-size: 13px;
  color: #606266;
}

.region-tag-small {
  font-size: 10px;
  padding: 0 6px;
  height: 18px;
  line-height: 16px;
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

.port-type-text {
  font-size: 11px;
  color: #909399;
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

/* Username cell */
.username-cell {
  display: flex;
  align-items: center;
  gap: 4px;
  color: #606266;
}

/* Status cell */
.status-cell {
  display: flex;
  align-items: center;
  gap: 4px;
}

.info-icon {
  color: #909399;
  cursor: pointer;
}

.info-icon:hover {
  color: #409EFF;
}

/* Segment status */
.segment-status {
  display: flex;
  gap: 4px;
}

/* OS cell */
.os-cell {
  max-width: 200px;
  overflow: hidden;
  text-overflow: ellipsis;
}

/* Notes cell */
.notes-cell {
  color: #909399;
  font-size: 13px;
}

.no-info {
  color: #c0c4cc;
}

/* Table row styles */
:deep(.segment-row) {
  background-color: #f5f7fa;
}

:deep(.segment-row:hover > td) {
  background-color: #ebeef5 !important;
}

:deep(.online-row) {
  background-color: #f0f9eb;
}

:deep(.offline-row) {
  background-color: #fef0f0;
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

.region-flag-large {
  font-size: 40px;
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

/* Segment dialog */
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
</style>
