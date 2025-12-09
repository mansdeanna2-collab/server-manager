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
      
      <el-main>
        <div class="content-wrapper">
          <el-card class="server-card">
            <template #header>
              <div class="card-header">
                <span class="card-title">🖥️ 服务器列表</span>
                <div class="header-actions">
                  <el-button
                    type="success"
                    :loading="importing"
                    @click="importServersFromFiles"
                  >
                    <el-icon><Download /></el-icon>
                    获取服务器
                  </el-button>
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
            
            <div class="search-filter-row">
              <el-input
                v-model="searchText"
                placeholder="按IP、用户名或备注搜索"
                class="search-input"
                :prefix-icon="Search"
                clearable
              />
              
              <div class="filter-buttons">
                <el-button
                  type="success"
                  @click="showFilteredServersDialog('normal')"
                >
                  <el-icon><CircleCheck /></el-icon>
                  正常 {{ normalCount }}
                </el-button>
                <el-button
                  type="danger"
                  @click="showFilteredServersDialog('offline')"
                >
                  <el-icon><CircleClose /></el-icon>
                  离线 {{ offlineCount }}
                </el-button>
                <el-button
                  type="info"
                  @click="showFilteredServersDialog('unknown')"
                >
                  <el-icon><QuestionFilled /></el-icon>
                  未知 {{ unknownCount }}
                </el-button>
                <el-button
                  type="warning"
                  @click="showFilteredServersDialog('error')"
                >
                  <el-icon><WarningFilled /></el-icon>
                  错误 {{ errorCount }}
                </el-button>
                <el-button
                  type="primary"
                  @click="showFilteredServersDialog('computer')"
                >
                  <el-icon><Monitor /></el-icon>
                  电脑 {{ computerCount }}
                </el-button>
              </div>
            </div>
            
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
            >
              <template #description>
                <p class="empty-description">
                  还没有添加任何服务器
                </p>
                <p class="empty-hint">
                  点击「新增服务器」按钮开始管理您的服务器
                </p>
              </template>
              <el-button
                type="primary"
                @click="showAddDialog"
              >
                <el-icon><Plus /></el-icon>
                新增服务器
              </el-button>
            </el-empty>
            
            <!-- IP段卡片网格布局 - 每行3个 -->
            <div
              v-if="!loading && !loadError && groupedServers.length > 0"
              class="segments-container"
            >
              <div class="segments-grid">
                <div
                  v-for="segment in paginatedSegments"
                  :key="segment.segmentKey"
                  class="segment-card"
                  :class="{ 'is-favorited': isSegmentFavorited(segment.segment) }"
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
                      ✓ {{ segment.onlineCount }}<template v-if="segment.errorCount > 0">
                        / <span class="error-count">✗ {{ segment.errorCount }}</span>
                      </template>
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
                    <div class="segment-card-actions-left">
                      <el-tooltip
                        :content="isSegmentFavorited(segment.segment) ? '取消收藏' : '收藏'"
                        placement="top"
                      >
                        <el-icon
                          class="action-icon favorite-icon"
                          :class="{ 'is-favorited': isSegmentFavorited(segment.segment) }"
                          @click.stop="toggleSegmentFavorite(segment.segment)"
                        >
                          <Star />
                        </el-icon>
                      </el-tooltip>
                      <el-tooltip
                        :content="getSegmentNote(segment.segment) || '点击添加备注'"
                        placement="top"
                      >
                        <el-icon
                          class="action-icon note-icon"
                          :class="{ 'has-note': getSegmentNote(segment.segment) }"
                          @click.stop="editSegmentNote(segment.segment)"
                        >
                          <EditPen />
                        </el-icon>
                      </el-tooltip>
                    </div>
                    <el-button
                      size="small"
                      type="primary"
                      plain
                      @click.stop="viewSegment(segment)"
                    >
                      <el-icon><View /></el-icon>
                      查看
                    </el-button>
                  </div>
                </div>
              </div>
              <div
                v-if="groupedServers.length > PAGE_SIZE"
                class="pagination-container"
              >
                <el-pagination
                  v-model:current-page="segmentsCurrentPage"
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
            <p class="detail-updated">
              更新时间：{{ formatDate(getLastUpdateTime(selectedServer)) }}
            </p>
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
            <span
              class="clickable-note"
              @click="editServerNote(selectedServer)"
            >
              {{ selectedServer.notes || '点击添加备注' }}
              <el-icon class="edit-icon"><EditPen /></el-icon>
            </span>
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
          :data="paginatedSegmentServers"
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
                <span class="updated-time">
                  更新时间：{{ formatDate(getLastUpdateTime(scope.row)) }}
                </span>
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
            width="340"
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
                  type="warning"
                  :loading="scope.row.checking"
                  @click="checkServer(scope.row)"
                >
                  <el-icon><Search /></el-icon>
                  检测
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
        <div
          v-if="selectedSegment.count > PAGE_SIZE"
          class="pagination-container"
        >
          <el-pagination
            v-model:current-page="segmentDialogCurrentPage"
            :page-size="PAGE_SIZE"
            :total="selectedSegment.count"
            layout="prev, pager, next"
            background
          />
        </div>
      </div>
    </el-dialog>
    <el-dialog
      v-model="filteredDialogVisible"
      :title="filteredDialogTitle"
      width="1100px"
      class="filtered-dialog"
    >
      <div v-if="filteredDialogServers.length > 0">
        <div class="segment-header">
          <span class="segment-count">共 {{ filteredDialogServers.length }} 台服务器</span>
          <el-button
            v-if="filteredDialogType === 'normal'"
            type="success"
            size="small"
            :loading="batchGettingSystemInfo"
            @click="batchGetSystemInfo"
          >
            <el-icon><Cpu /></el-icon>
            一键获取系统信息
          </el-button>
        </div>
        <el-table
          :data="paginatedFilteredServers"
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
                <span class="updated-time">
                  更新时间：{{ formatDate(getLastUpdateTime(scope.row)) }}
                </span>
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
            width="340"
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
                  type="warning"
                  :loading="scope.row.checking"
                  @click="checkServer(scope.row)"
                >
                  <el-icon><Search /></el-icon>
                  检测
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
        <div
          v-if="filteredDialogServers.length > PAGE_SIZE"
          class="pagination-container"
        >
          <el-pagination
            v-model:current-page="filteredDialogCurrentPage"
            :page-size="PAGE_SIZE"
            :total="filteredDialogServers.length"
            layout="prev, pager, next"
            background
          />
        </div>
      </div>
      <el-empty
        v-else
        description="没有符合条件的服务器"
      />
    </el-dialog>
    
    <!-- Terminal Connection Dialog -->
    <el-dialog
      v-model="terminalDialogVisible"
      :title="`终端 - ${terminalServer?.ip_address || ''}`"
      width="1100px"
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
import { ref, reactive, computed, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  Monitor, Odometer, User, ArrowDown, Plus, Refresh,
  Search, View, Edit, Delete, OfficeBuilding, Connection, CopyDocument, Loading,
  CircleCheck, CircleClose, Download, QuestionFilled, WarningFilled, Cpu, Star, EditPen
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
const filteredDialogVisible = ref(false)
const filteredDialogTitle = ref('')
const filteredDialogServers = ref([])
const filteredDialogType = ref('')
const batchGettingSystemInfo = ref(false)
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
const isEdit = ref(false)
const currentServer = ref(null)
const selectedServer = ref(null)
const selectedSegment = ref(null)
const terminalServer = ref(null)
const terminalRef = ref(null)
const refreshing = ref(false)
const currentUser = ref(null)
const loading = ref(false)
const loadError = ref('')
const importing = ref(false)

// Pagination variables
const PAGE_SIZE = 10
const segmentsCurrentPage = ref(1)
const segmentDialogCurrentPage = ref(1)
const filteredDialogCurrentPage = ref(1)

// IP段收藏和备注功能
const FAVORITES_KEY = 'server_segment_favorites'
const SEGMENT_NOTES_KEY = 'server_segment_notes'
const segmentFavorites = ref(new Set())
const segmentNotes = ref({})

// 初始化收藏和备注数据
const initSegmentData = () => {
  try {
    const savedFavorites = localStorage.getItem(FAVORITES_KEY)
    if (savedFavorites) {
      segmentFavorites.value = new Set(JSON.parse(savedFavorites))
    }
    const savedNotes = localStorage.getItem(SEGMENT_NOTES_KEY)
    if (savedNotes) {
      segmentNotes.value = JSON.parse(savedNotes)
    }
  } catch (_e) {
    segmentFavorites.value = new Set()
    segmentNotes.value = {}
  }
}

// 检查IP段是否被收藏
const isSegmentFavorited = (segment) => {
  return segmentFavorites.value.has(segment)
}

// 切换IP段收藏状态
const toggleSegmentFavorite = (segment) => {
  if (segmentFavorites.value.has(segment)) {
    segmentFavorites.value.delete(segment)
    ElMessage.success(`已取消收藏 ${segment}.x`)
  } else {
    segmentFavorites.value.add(segment)
    ElMessage.success(`已收藏 ${segment}.x`)
  }
  localStorage.setItem(FAVORITES_KEY, JSON.stringify([...segmentFavorites.value]))
}

// 获取IP段备注
const getSegmentNote = (segment) => {
  return segmentNotes.value[segment] || ''
}

// 编辑IP段备注
const editSegmentNote = async (segment) => {
  const currentNote = getSegmentNote(segment)
  try {
    const { value } = await ElMessageBox.prompt(`请输入 ${segment}.x 的备注`, '编辑备注', {
      inputValue: currentNote,
      inputPlaceholder: '请输入备注内容',
      confirmButtonText: '保存',
      cancelButtonText: '取消',
      inputPattern: /^.{0,100}$/,
      inputErrorMessage: '备注长度不能超过100个字符'
    })
    if (value !== undefined) {
      if (value.trim()) {
        segmentNotes.value[segment] = value.trim()
      } else {
        delete segmentNotes.value[segment]
      }
      localStorage.setItem(SEGMENT_NOTES_KEY, JSON.stringify(segmentNotes.value))
      ElMessage.success('备注已保存')
    }
  } catch (_e) {
    // 用户取消操作
  }
}

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

const getLastUpdateTime = (server) => {
  if (!server) return null
  return server.last_checked || server.updated_at || server.created_at
}

const getUpdatedTimestamp = (server) => {
  const timeStr = getLastUpdateTime(server)
  if (!timeStr) return Number.NEGATIVE_INFINITY
  const time = new Date(timeStr).getTime()
  return isNaN(time) ? Number.NEGATIVE_INFINITY : time
}

// Computed counts for filter buttons
// Helper function to check if a server is "normal" (root user + online + no error)
const isNormalServer = (server) => {
  return server.username === 'root' && server.status === 'online' && !server.error_type
}
// 正常: root用户 + 在线 + 无错误
const normalCount = computed(() => servers.value.filter(isNormalServer).length)
// 离线 (排除Administrator用户)
const offlineCount = computed(() => servers.value.filter(s => s.status === 'offline' && s.username !== 'Administrator').length)
// 未知
const unknownCount = computed(() => servers.value.filter(s => s.status === 'unknown').length)
// 错误: 有error_type的 (排除Administrator用户)
const errorCount = computed(() => servers.value.filter(s => s.error_type && s.username !== 'Administrator').length)
// 电脑 (Windows RDP) - 包含Administrator用户的错误和离线状态
const computerCount = computed(() => servers.value.filter(s => s.port === 3389).length)

// Show filtered servers in dialog
const showFilteredServersDialog = (filterType) => {
  let result = servers.value
  let title = ''
  
  if (filterType === 'normal') {
    // 正常: root用户 + 在线 + 无错误
    result = result.filter(isNormalServer)
    title = '正常服务器'
  } else if (filterType === 'offline') {
    // 离线服务器：排除Administrator用户
    result = result.filter(server => server.status === 'offline' && server.username !== 'Administrator')
    title = '离线服务器'
  } else if (filterType === 'unknown') {
    result = result.filter(server => server.status === 'unknown')
    title = '未知状态服务器'
  } else if (filterType === 'error') {
    // 错误服务器：排除Administrator用户
    result = result.filter(server => server.error_type && server.username !== 'Administrator')
    title = '错误服务器'
  } else if (filterType === 'computer') {
    // 电脑对话框：显示所有Windows RDP服务器（包含Administrator的错误和离线状态）
    result = result.filter(server => server.port === 3389)
    title = '电脑 (Windows RDP)'
  }
  
  // 根据filterType设置排序逻辑
  filteredDialogType.value = filterType
  
  if (filterType === 'computer') {
    // 电脑对话框排序：正常 > 错误 > 离线
    filteredDialogServers.value = [...result].sort((a, b) => {
      // 定义状态优先级：正常(0) > 错误(1) > 离线(2)
      const getStatusPriority = (server) => {
        if (server.status === 'online' && !server.error_type) return 0  // 正常
        if (server.error_type) return 1                                  // 错误（包括在线但有错误的）
        if (server.status === 'offline') return 2                        // 离线
        return 3  // 其他状态
      }
      const priorityDiff = getStatusPriority(a) - getStatusPriority(b)
      if (priorityDiff !== 0) return priorityDiff
      // 同优先级按更新时间排序
      return getUpdatedTimestamp(b) - getUpdatedTimestamp(a)
    })
  } else {
    // 其他对话框按更新时间排序
    filteredDialogServers.value = [...result].sort((a, b) => getUpdatedTimestamp(b) - getUpdatedTimestamp(a))
  }
  
  filteredDialogTitle.value = title
  filteredDialogCurrentPage.value = 1
  filteredDialogVisible.value = true
}

// Filter servers by search text
const filteredServers = computed(() => {
  let result = servers.value
  
  // Apply search filter
  if (searchText.value) {
    const search = searchText.value.toLowerCase()
    result = result.filter(server =>
      server.ip_address.toLowerCase().includes(search) ||
      server.username.toLowerCase().includes(search) ||
      (server.notes && server.notes.toLowerCase().includes(search))
    )
  }
  
  // Note: Sorting by update time is handled in groupedServers computed property
  return result
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
    // Count online, offline, and error servers in single pass
    let onlineCount = 0
    let offlineCount = 0
    let errorCount = 0
    const sortedServers = [...serverList].sort(
      (a, b) => getUpdatedTimestamp(b) - getUpdatedTimestamp(a)
    )
    for (const s of sortedServers) {
      if (s.status === 'online') {
        onlineCount++
        // Count servers that have error_type as having errors
        if (s.error_type) {
          errorCount++
        }
      } else if (s.status === 'offline') {
        offlineCount++
      }
    }

    result.push({
      segmentKey: `segment-${segment}`,
      segment: segment,
      isSegment: true,
      count: serverList.length,
      onlineCount: onlineCount,
      offlineCount: offlineCount,
      errorCount: errorCount,
      hasChildren: true,
      latestUpdated: getUpdatedTimestamp(sortedServers[0]),
      servers: sortedServers.map(s => ({
        ...s,
        segmentKey: `server-${s.id}`
      }))
    })
  })

  // Sort: favorites first, then by latest update time, fallback to numeric segment order
  result.sort((a, b) => {
    const aFavorited = segmentFavorites.value.has(a.segment) ? 0 : 1
    const bFavorited = segmentFavorites.value.has(b.segment) ? 0 : 1
    if (aFavorited !== bFavorited) return aFavorited - bFavorited
    const diff = (b.latestUpdated || 0) - (a.latestUpdated || 0)
    if (diff !== 0) return diff
    return compareIpSegments(a, b)
  })

  return result
})

// Paginated segments for the grid display
const paginatedSegments = computed(() => {
  const start = (segmentsCurrentPage.value - 1) * PAGE_SIZE
  const end = start + PAGE_SIZE
  return groupedServers.value.slice(start, end)
})

// Paginated servers for segment dialog
const paginatedSegmentServers = computed(() => {
  if (!selectedSegment.value) return []
  const start = (segmentDialogCurrentPage.value - 1) * PAGE_SIZE
  const end = start + PAGE_SIZE
  return selectedSegment.value.servers.slice(start, end)
})

// Paginated servers for filtered dialog
const paginatedFilteredServers = computed(() => {
  const start = (filteredDialogCurrentPage.value - 1) * PAGE_SIZE
  const end = start + PAGE_SIZE
  return filteredDialogServers.value.slice(start, end)
})

onMounted(async () => {
  initSegmentData()
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
    const existingServerMap = new Map()
    servers.value.forEach(item => {
      existingServerMap.set(item.id, item)
    })
    servers.value = response.data.map(s => {
      const existing = existingServerMap.get(s.id)
      const checkDetail = s.check_detail ?? existing?.checkDetail ?? ''
      const errorType = s.error_type ?? existing?.error_type ?? ''
      return {
        ...s,
        checking: false,
        checkDetail,
        error_type: errorType
      }
    })
  } catch (error) {
    const message = error.response?.data?.message || error.message || '网络连接失败'
    loadError.value = message
    ElMessage.error(`加载服务器失败: ${message}`)
  } finally {
    loading.value = false
  }
}

const importServersFromFiles = async () => {
  importing.value = true
  try {
    const response = await serversAPI.importFromFiles()
    const { summary, imported: _imported, skipped: _skipped, errors } = response.data
    
    let message = `导入完成: 成功 ${summary.imported_count} 台`
    if (summary.skipped_count > 0) {
      message += `，跳过 ${summary.skipped_count} 台`
    }
    if (summary.error_count > 0) {
      message += `，失败 ${summary.error_count} 个`
    }
    
    if (summary.imported_count > 0) {
      ElMessage.success(message)
      await loadServers()
    } else if (summary.skipped_count > 0 && summary.error_count === 0) {
      ElMessage.warning(message + '（所有服务器已存在）')
    } else if (summary.error_count > 0) {
      ElMessage.warning(message)
      // Consolidate error messages - show first 3 errors max
      const maxErrors = 3
      const errorFiles = errors.slice(0, maxErrors).map(e => e.file).join(', ')
      const remaining = errors.length - maxErrors
      let errorDetail = `失败文件: ${errorFiles}`
      if (remaining > 0) {
        errorDetail += ` 等${remaining}个文件`
      }
      ElMessage.error(errorDetail)
    } else {
      ElMessage.info('未找到可导入的服务器文件')
    }
  } catch (error) {
    const message = error.response?.data?.message || error.message || '导入失败'
    ElMessage.error(`导入服务器失败: ${message}`)
  } finally {
    importing.value = false
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
  segmentDialogCurrentPage.value = 1
  segmentDialogVisible.value = true
}

// 检测服务器状态
const checkServer = async (server) => {
  if (server.checking) return
  
  server.checking = true
  try {
    const response = await serversAPI.check(server.id)
    const status = response.data.status

    // Update server status in both servers list and segment
    server.status = status.overall
    server.checkDetail = response.data.check_detail ?? status.detail ?? ''
    server.error_type = response.data.error_type ?? status.error_type ?? ''
    if (response.data.last_checked) {
      server.last_checked = response.data.last_checked
    }
    if (response.data.updated_at) {
      server.updated_at = response.data.updated_at
    }
    
    // Show result message based on status
    if (status.overall === 'online') {
      if (status.auth === true) {
        ElMessage.success(`服务器 ${server.ip_address} 检测成功: ${status.detail}`)
      } else if (status.port === true) {
        ElMessage.success(`服务器 ${server.ip_address} 端口开放，但认证未验证`)
      } else {
        ElMessage.success(`服务器 ${server.ip_address} 可达`)
      }
    } else {
      ElMessage.warning(`服务器 ${server.ip_address}: ${status.detail}`)
    }
  } catch (error) {
    const errorMsg = error.response?.data?.message || error.message || '网络连接失败'
    ElMessage.error(`检测服务器 ${server.ip_address} 失败: ${errorMsg}`)
  } finally {
    server.checking = false
  }
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

// 编辑服务器备注
const editServerNote = async (server) => {
  const currentNote = server.notes || ''
  try {
    const { value } = await ElMessageBox.prompt(`请输入 ${server.ip_address} 的备注`, '编辑备注', {
      inputValue: currentNote,
      inputPlaceholder: '请输入备注内容',
      confirmButtonText: '保存',
      cancelButtonText: '取消',
      inputPattern: /^.{0,255}$/,
      inputErrorMessage: '备注长度不能超过255个字符'
    })
    if (value !== undefined) {
      const newNote = value.trim()
      // 调用API更新备注
      await serversAPI.update(server.id, { notes: newNote })
      server.notes = newNote
      // 更新servers列表中的对应服务器
      const serverInList = servers.value.find(s => s.id === server.id)
      if (serverInList) {
        serverInList.notes = newNote
      }
      ElMessage.success('备注已保存')
    }
  } catch (error) {
    if (error !== 'cancel' && error !== 'close') {
      ElMessage.error('保存备注失败')
    }
  }
}

// 批量获取正常服务器的系统信息
const batchGetSystemInfo = async () => {
  if (filteredDialogServers.value.length === 0) return
  
  batchGettingSystemInfo.value = true
  
  try {
    // 创建所有请求的Promise数组
    const promises = filteredDialogServers.value.map(server => 
      serversAPI.getSystemInfo(server.id)
        .then(response => ({ server, response, success: true }))
        .catch(() => ({ server, success: false }))
    )
    
    // 并发执行所有请求
    const results = await Promise.all(promises)
    
    let successCount = 0
    let failCount = 0
    
    // 处理结果
    results.forEach(result => {
      if (result.success) {
        result.server.os_info = result.response.data.os
        result.server.cpu_info = result.response.data.cpu
        result.server.memory_info = result.response.data.memory
        result.server.disk_info = result.response.data.disk
        result.server.uptime = result.response.data.uptime
        successCount++
      } else {
        failCount++
      }
    })
    
    if (successCount > 0) {
      ElMessage.success(`成功获取 ${successCount} 台服务器的系统信息${failCount > 0 ? `，${failCount} 台失败` : ''}`)
      await loadServers()
    } else if (failCount > 0) {
      ElMessage.error(`获取系统信息失败，共 ${failCount} 台服务器`)
    }
  } catch (_error) {
    ElMessage.error('批量获取系统信息失败')
  } finally {
    batchGettingSystemInfo.value = false
  }
}

const formatDate = (dateStr) => {
  if (!dateStr) return '从未'
  const date = new Date(dateStr)
  return date.toLocaleString('zh-CN', { timeZone: 'Asia/Shanghai' })
}

const handleMenuSelect = (index) => {
  router.push(index)
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

.search-filter-row {
  display: flex;
  align-items: center;
  gap: 20px;
  margin-bottom: 24px;
}

.search-input {
  max-width: 320px;
  flex-shrink: 0;
}

.filter-buttons {
  display: flex;
  gap: 8px;
}

@media (max-width: 768px) {
  .search-filter-row {
    flex-direction: column;
    align-items: stretch;
  }
  
  .search-input {
    max-width: 100%;
  }
  
  .filter-buttons {
    justify-content: flex-start;
  }
}

/* IP段卡片网格布局 - 每行3个 */
.segments-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 12px;
}

@media (max-width: 1200px) {
  .segments-grid {
    grid-template-columns: repeat(2, 1fr);
  }
}

@media (max-width: 768px) {
  .segments-grid {
    grid-template-columns: 1fr;
  }
}

.segment-card {
  background: linear-gradient(135deg, #ffffff 0%, #f9fafc 100%);
  border-radius: 8px;
  padding: 12px;
  cursor: pointer;
  transition: all 0.3s ease;
  border: 1px solid #e4e7ed;
  box-shadow: 0 2px 8px 0 rgba(0, 0, 0, 0.04);
}

.segment-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 16px 0 rgba(64, 158, 255, 0.15);
  border-color: #409EFF;
}

.segment-card.is-favorited {
  border-color: #e6a23c;
  background: linear-gradient(135deg, #fffdf5 0%, #fef8e8 100%);
}

.segment-card-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 8px;
}

.ip-segment-title {
  font-size: 14px;
  font-weight: 700;
  color: #409EFF;
  font-family: 'Monaco', 'Menlo', 'Consolas', monospace;
}

.count-tag {
  background: linear-gradient(135deg, #f0f9eb 0%, #e8f5e1 100%);
  border-color: #c2e7b0;
  color: #67c23a;
  font-size: 11px;
}

.segment-card-status {
  display: flex;
  gap: 6px;
  margin-bottom: 8px;
  flex-wrap: wrap;
}

.error-count {
  color: #f56c6c;
  font-weight: 600;
}

.segment-card-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-top: 8px;
}

.segment-card-actions-left {
  display: flex;
  gap: 8px;
  align-items: center;
}

.action-icon {
  cursor: pointer;
  font-size: 16px;
  color: #909399;
  transition: all 0.2s ease;
}

.action-icon:hover {
  transform: scale(1.1);
}

.favorite-icon:hover {
  color: #e6a23c;
}

.favorite-icon.is-favorited {
  color: #e6a23c;
}

.note-icon:hover {
  color: #409EFF;
}

.note-icon.has-note {
  color: #409EFF;
}

/* IP cell styles */
.ip-cell {
  display: flex;
  gap: 8px;
  flex-direction: column;
  align-items: flex-start;
}

.ip-text {
  font-family: 'Monaco', 'Menlo', 'Consolas', monospace;
  font-size: 13px;
  color: #303133;
  font-weight: 500;
}

.updated-time {
  font-size: 12px;
  color: #909399;
  line-height: 1.2;
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
  word-break: break-word;
  white-space: pre-wrap;
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

.detail-updated {
  margin: 0;
  color: #909399;
  font-size: 13px;
}

.detail-actions {
  margin-top: 20px;
  text-align: right;
}

/* Segment dialog header */
.segment-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 15px;
  margin-bottom: 20px;
  padding-bottom: 15px;
  border-bottom: 1px solid #ebeef5;
}

.segment-count {
  color: #909399;
  font-size: 14px;
}

/* Clickable note styles */
.clickable-note {
  cursor: pointer;
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 4px 8px;
  border-radius: 4px;
  transition: all 0.2s ease;
  color: #606266;
}

.clickable-note:hover {
  background-color: #f5f7fa;
  color: #409EFF;
}

.clickable-note .edit-icon {
  font-size: 14px;
  opacity: 0.5;
  transition: opacity 0.2s ease;
}

.clickable-note:hover .edit-icon {
  opacity: 1;
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

/* Filtered dialog styles */
.filtered-dialog :deep(.el-dialog__body) {
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

/* Pagination container */
.pagination-container {
  display: flex;
  justify-content: center;
  margin-top: 20px;
  padding-top: 16px;
  border-top: 1px solid #ebeef5;
}

/* Segments container */
.segments-container {
  display: flex;
  flex-direction: column;
}
</style>
