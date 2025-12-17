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
            <el-menu-item index="/system-settings">
              <el-icon><Tools /></el-icon>
              系统设置
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
          <el-card class="settings-card">
            <template #header>
              <div class="card-header">
                <div class="card-header-title">
                  <el-icon
                    class="card-header-icon"
                    :size="20"
                  >
                    <Tools />
                  </el-icon>
                  <span>系统设置</span>
                </div>
                <div class="card-header-buttons">
                  <el-button
                    type="default"
                    @click="goBack"
                  >
                    <el-icon><Back /></el-icon>
                    返回仪表盘
                  </el-button>
                </div>
              </div>
            </template>
            
            <div class="settings-content">
              <el-row :gutter="24">
                <!-- 左侧垂直菜单 -->
                <el-col :span="6">
                  <el-menu
                    :default-active="activeSettingMenu"
                    class="settings-menu"
                    @select="handleSettingMenuSelect"
                  >
                    <el-menu-item index="whitelist">
                      <el-icon><Lock /></el-icon>
                      <span>登录白名单</span>
                    </el-menu-item>
                    <el-menu-item index="ssl">
                      <el-icon><Key /></el-icon>
                      <span>SSL设置</span>
                    </el-menu-item>
                    <el-menu-item index="logs">
                      <el-icon><Document /></el-icon>
                      <span>查看系统日志</span>
                    </el-menu-item>
                  </el-menu>
                </el-col>
                
                <!-- 右侧内容区 -->
                <el-col :span="18">
                  <!-- 登录白名单设置 -->
                  <div
                    v-if="activeSettingMenu === 'whitelist'"
                    class="setting-panel"
                  >
                    <h3 class="setting-title">
                      <el-icon><Lock /></el-icon>
                      登录白名单设置
                    </h3>
                    <el-alert
                      type="warning"
                      :closable="false"
                      show-icon
                      class="setting-alert"
                    >
                      <template #title>
                        注意：启用白名单后，不在列表中的IP将无法登录系统。请确保当前IP已添加到白名单中。
                      </template>
                    </el-alert>
                    <el-form
                      :model="whitelistForm"
                      label-width="120px"
                    >
                      <el-form-item label="启用白名单">
                        <el-switch
                          v-model="whitelistForm.enabled"
                          :active-text="whitelistForm.enabled ? '已启用' : ''"
                          :inactive-text="!whitelistForm.enabled ? '未启用' : ''"
                        />
                        <span class="form-tip">启用后，只有白名单中的IP地址可以登录系统</span>
                      </el-form-item>
                      <el-form-item label="IP白名单">
                        <div class="ip-list-container">
                          <div
                            v-for="(ip, index) in whitelistForm.ip_list"
                            :key="index"
                            class="ip-item"
                          >
                            <el-input
                              v-model="whitelistForm.ip_list[index]"
                              placeholder="请输入IP地址，如: 192.168.1.1"
                              :class="{ 'is-valid': isValidIp(ip), 'is-invalid': ip && !isValidIp(ip) }"
                              @blur="validateIpInput(index)"
                            >
                              <template #suffix>
                                <el-icon
                                  v-if="ip && isValidIp(ip)"
                                  class="valid-icon"
                                >
                                  <CircleCheck />
                                </el-icon>
                                <el-icon
                                  v-else-if="ip && !isValidIp(ip)"
                                  class="invalid-icon"
                                >
                                  <CircleClose />
                                </el-icon>
                              </template>
                            </el-input>
                            <el-tooltip
                              v-if="ip && !isValidIp(ip)"
                              content="无效的IP地址格式"
                              placement="top"
                            >
                              <el-button
                                type="warning"
                                :icon="Warning"
                                circle
                                size="small"
                              />
                            </el-tooltip>
                            <el-button
                              type="danger"
                              :icon="Delete"
                              circle
                              @click="removeWhitelistIp(index)"
                            />
                          </div>
                          <div class="ip-actions">
                            <el-button
                              type="primary"
                              @click="addWhitelistIp"
                            >
                              <el-icon><Plus /></el-icon>
                              添加IP
                            </el-button>
                            <span class="ip-count">
                              共 {{ validIpCount }} 个有效IP
                            </span>
                          </div>
                        </div>
                      </el-form-item>
                      <el-form-item>
                        <el-button
                          type="primary"
                          :loading="savingSettings"
                          :disabled="whitelistForm.enabled && validIpCount === 0"
                          @click="saveWhitelistSettings"
                        >
                          <el-icon><Check /></el-icon>
                          保存设置
                        </el-button>
                        <el-tooltip
                          v-if="whitelistForm.enabled && validIpCount === 0"
                          content="启用白名单时至少需要一个有效的IP地址"
                          placement="top"
                        >
                          <el-icon class="tip-icon">
                            <InfoFilled />
                          </el-icon>
                        </el-tooltip>
                      </el-form-item>
                    </el-form>
                  </div>
                  
                  <!-- SSL设置 -->
                  <div
                    v-if="activeSettingMenu === 'ssl'"
                    class="setting-panel"
                  >
                    <h3 class="setting-title">
                      <el-icon><Key /></el-icon>
                      SSL设置
                    </h3>
                    <el-alert
                      type="info"
                      :closable="false"
                      show-icon
                      class="setting-alert"
                    >
                      <template #title>
                        SSL证书用于加密HTTPS连接。请确保证书文件路径正确且文件存在。
                      </template>
                    </el-alert>
                    <el-form
                      :model="sslForm"
                      label-width="120px"
                    >
                      <el-form-item label="启用SSL">
                        <el-switch
                          v-model="sslForm.enabled"
                          :active-text="sslForm.enabled ? '已启用' : ''"
                          :inactive-text="!sslForm.enabled ? '未启用' : ''"
                        />
                        <span class="form-tip">启用HTTPS安全连接</span>
                      </el-form-item>
                      <el-form-item label="证书路径">
                        <el-input
                          v-model="sslForm.cert_path"
                          placeholder="SSL证书文件路径，如: /etc/ssl/certs/server.crt"
                          :disabled="!sslForm.enabled"
                          :class="{ 'path-configured': sslForm.cert_path }"
                        >
                          <template #prefix>
                            <el-icon><Document /></el-icon>
                          </template>
                          <template #suffix>
                            <el-tag
                              v-if="sslForm.cert_path"
                              size="small"
                              type="success"
                            >
                              已配置
                            </el-tag>
                          </template>
                        </el-input>
                        <div class="path-hint">
                          支持 .crt, .pem, .cer 格式的证书文件
                        </div>
                      </el-form-item>
                      <el-form-item label="私钥路径">
                        <el-input
                          v-model="sslForm.key_path"
                          placeholder="SSL私钥文件路径，如: /etc/ssl/private/server.key"
                          :disabled="!sslForm.enabled"
                          :class="{ 'path-configured': sslForm.key_path }"
                        >
                          <template #prefix>
                            <el-icon><Key /></el-icon>
                          </template>
                          <template #suffix>
                            <el-tag
                              v-if="sslForm.key_path"
                              size="small"
                              type="success"
                            >
                              已配置
                            </el-tag>
                          </template>
                        </el-input>
                        <div class="path-hint">
                          支持 .key, .pem 格式的私钥文件
                        </div>
                      </el-form-item>
                      <el-form-item>
                        <el-button
                          type="primary"
                          :loading="savingSettings"
                          :disabled="sslForm.enabled && (!sslForm.cert_path || !sslForm.key_path)"
                          @click="saveSSLSettings"
                        >
                          <el-icon><Check /></el-icon>
                          保存设置
                        </el-button>
                        <el-tooltip
                          v-if="sslForm.enabled && (!sslForm.cert_path || !sslForm.key_path)"
                          content="启用SSL时需要配置证书和私钥路径"
                          placement="top"
                        >
                          <el-icon class="tip-icon">
                            <InfoFilled />
                          </el-icon>
                        </el-tooltip>
                      </el-form-item>
                    </el-form>
                  </div>
                  
                  <!-- 系统日志 -->
                  <div
                    v-if="activeSettingMenu === 'logs'"
                    class="setting-panel"
                  >
                    <h3 class="setting-title">
                      <el-icon><Document /></el-icon>
                      系统日志
                    </h3>
                    <div class="log-description">
                      <p>系统日志记录了用户登录、服务器操作、系统设置等重要操作。</p>
                    </div>
                    <div class="log-actions">
                      <el-button
                        type="primary"
                        :loading="loadingLogs"
                        @click="viewSystemLogs"
                      >
                        <el-icon><View /></el-icon>
                        查看完整日志
                      </el-button>
                    </div>
                    
                    <!-- 日志统计 -->
                    <div
                      v-if="logStats.total > 0"
                      class="log-stats"
                    >
                      <h4>日志统计</h4>
                      <div class="stats-grid">
                        <div class="stat-item">
                          <span class="stat-label">总日志数</span>
                          <span class="stat-value">{{ logStats.total }}</span>
                        </div>
                        <div
                          v-for="(count, type) in logStats.by_type"
                          :key="type"
                          class="stat-item"
                        >
                          <span class="stat-label">{{ getLogTypeLabel(type) }}</span>
                          <span class="stat-value">{{ count }}</span>
                        </div>
                      </div>
                    </div>
                    
                    <!-- 最近日志预览 -->
                    <div
                      v-if="recentLogs.length > 0"
                      class="recent-logs"
                    >
                      <h4>最近操作</h4>
                      <div class="log-list">
                        <div
                          v-for="log in recentLogs"
                          :key="log.id"
                          class="log-item"
                          :class="['log-' + log.status]"
                        >
                          <div class="log-item-header">
                            <el-tag
                              :type="getLogStatusType(log.status)"
                              size="small"
                            >
                              {{ getLogTypeLabel(log.log_type) }}
                            </el-tag>
                            <span class="log-time">{{ formatDateTime(log.created_at) }}</span>
                          </div>
                          <div class="log-item-body">
                            <span class="log-action">{{ log.action }}</span>
                            <span
                              v-if="log.target"
                              class="log-target"
                            >
                              → {{ log.target }}
                            </span>
                          </div>
                          <div class="log-item-footer">
                            <span
                              v-if="log.username"
                              class="log-user"
                            >
                              <el-icon><User /></el-icon>
                              {{ log.username }}
                            </span>
                            <span
                              v-if="log.ip_address"
                              class="log-ip"
                            >
                              <el-icon><Monitor /></el-icon>
                              {{ log.ip_address }}
                            </span>
                          </div>
                        </div>
                      </div>
                    </div>
                    
                    <el-empty
                      v-else-if="!loadingLogs"
                      description="暂无日志记录"
                    />
                  </div>
                </el-col>
              </el-row>
            </div>
          </el-card>
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
    
    <!-- System Logs Dialog -->
    <el-dialog
      v-model="logsDialogVisible"
      title="系统操作日志"
      width="1100px"
      top="3vh"
      :close-on-click-modal="false"
    >
      <div class="logs-dialog-content">
        <!-- 筛选工具栏 -->
        <div class="logs-toolbar">
          <el-select
            v-model="logTypeFilter"
            placeholder="日志类型"
            clearable
            style="width: 150px;"
            @change="filterLogs"
          >
            <el-option
              v-for="type in logTypes"
              :key="type.value"
              :label="type.label"
              :value="type.value"
            />
          </el-select>
          <el-select
            v-model="logStatusFilter"
            placeholder="状态"
            clearable
            style="width: 120px; margin-left: 10px;"
            @change="filterLogs"
          >
            <el-option
              label="成功"
              value="success"
            />
            <el-option
              label="失败"
              value="failed"
            />
            <el-option
              label="警告"
              value="warning"
            />
          </el-select>
          <el-button
            type="primary"
            :loading="loadingLogs"
            style="margin-left: auto;"
            @click="refreshLogs"
          >
            <el-icon><Refresh /></el-icon>
            刷新
          </el-button>
        </div>
        
        <!-- 日志列表 -->
        <div
          v-if="loadingLogs"
          class="loading-container"
        >
          <el-icon
            class="loading-icon"
            :size="40"
          >
            <Loading />
          </el-icon>
          <p class="loading-text">
            正在加载日志...
          </p>
        </div>
        
        <el-table
          v-else
          :data="systemLogs"
          stripe
          border
          size="small"
          max-height="500"
          style="width: 100%;"
        >
          <el-table-column
            prop="created_at"
            label="时间"
            width="180"
          >
            <template #default="scope">
              <span class="log-time-cell">{{ formatDateTime(scope.row.created_at) }}</span>
            </template>
          </el-table-column>
          <el-table-column
            prop="log_type"
            label="类型"
            width="120"
            align="center"
          >
            <template #default="scope">
              <el-tag
                :type="getLogTypeColor(scope.row.log_type)"
                size="small"
              >
                {{ getLogTypeLabel(scope.row.log_type) }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column
            prop="action"
            label="操作"
            min-width="200"
            show-overflow-tooltip
          />
          <el-table-column
            prop="target"
            label="目标"
            width="150"
            show-overflow-tooltip
          >
            <template #default="scope">
              <span class="log-target-cell">{{ scope.row.target || '-' }}</span>
            </template>
          </el-table-column>
          <el-table-column
            prop="username"
            label="用户"
            width="100"
            align="center"
          >
            <template #default="scope">
              <span>{{ scope.row.username || '-' }}</span>
            </template>
          </el-table-column>
          <el-table-column
            prop="ip_address"
            label="IP地址"
            width="140"
          >
            <template #default="scope">
              <span class="log-ip-cell">{{ scope.row.ip_address || '-' }}</span>
            </template>
          </el-table-column>
          <el-table-column
            prop="status"
            label="状态"
            width="80"
            align="center"
          >
            <template #default="scope">
              <el-tag
                :type="getLogStatusType(scope.row.status)"
                size="small"
              >
                {{ getStatusLabel(scope.row.status) }}
              </el-tag>
            </template>
          </el-table-column>
        </el-table>
        
        <!-- 分页 -->
        <div
          v-if="logTotal > 0"
          class="pagination-container"
        >
          <el-pagination
            v-model:current-page="logPage"
            v-model:page-size="logPageSize"
            :page-sizes="[50, 100, 200, 500]"
            :total="logTotal"
            layout="total, sizes, prev, pager, next, jumper"
            @size-change="refreshLogs"
            @current-change="refreshLogs"
          />
        </div>
      </div>
      <template #footer>
        <el-button @click="logsDialogVisible = false">
          关闭
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
  ArrowDown, Back, Check, CircleCheck, CircleClose, Delete, Document, FolderOpened, InfoFilled, Key, Loading, Lock, Monitor, Odometer, OfficeBuilding, Plus, Refresh, Search, Setting, Tools, User, View, Warning
} from '@element-plus/icons-vue'
import { authAPI, preferencesAPI } from '@/api'

const router = useRouter()
const route = useRoute()
const currentUser = ref(null)
const passwordDialogVisible = ref(false)
const changingPassword = ref(false)
const passwordFormRef = ref(null)

// 设置菜单相关状态
const activeSettingMenu = ref('whitelist')
const savingSettings = ref(false)

// 白名单设置
const whitelistForm = reactive({
  enabled: false,
  ip_list: []
})

// SSL设置
const sslForm = reactive({
  enabled: false,
  cert_path: '',
  key_path: ''
})

// IP验证正则表达式（IPv4和IPv6）
const ipv4Pattern = /^(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$/
const ipv6Pattern = /^(?:[0-9a-fA-F]{1,4}:){7}[0-9a-fA-F]{1,4}$|^::(?:[0-9a-fA-F]{1,4}:){0,6}[0-9a-fA-F]{1,4}$|^[0-9a-fA-F]{1,4}::(?:[0-9a-fA-F]{1,4}:){0,5}[0-9a-fA-F]{1,4}$/

// 验证IP地址
const isValidIp = (ip) => {
  if (!ip || !ip.trim()) return false
  const trimmedIp = ip.trim()
  return ipv4Pattern.test(trimmedIp) || ipv6Pattern.test(trimmedIp)
}

// IP输入验证反馈
const validateIpInput = (_index) => {
  // 触发重新计算有效IP数量（通过computed自动更新）
}

// 计算有效IP数量
const validIpCount = computed(() => {
  return whitelistForm.ip_list.filter(ip => isValidIp(ip)).length
})

// 日志相关状态
const logsDialogVisible = ref(false)
const loadingLogs = ref(false)
const systemLogs = ref([])
const recentLogs = ref([])
const logTypes = ref([])
const logStats = ref({ total: 0, by_type: {}, by_status: {} })
const logPage = ref(1)
const logPageSize = ref(100)
const logTotal = ref(0)
const logTypeFilter = ref('')
const logStatusFilter = ref('')

// 日志类型标签映射
const logTypeLabels = {
  'login': '登录成功',
  'login_failed': '登录失败',
  'logout': '用户登出',
  'password_change': '密码修改',
  'server_connect': '服务器连接',
  'server_create': '创建服务器',
  'server_update': '更新服务器',
  'server_delete': '删除服务器',
  'server_check': '检测服务器',
  'backup': '系统备份',
  'settings': '设置修改',
  'import': '服务器导入'
}

// 日志类型颜色映射
const logTypeColors = {
  'login': 'success',
  'login_failed': 'danger',
  'logout': 'info',
  'password_change': 'warning',
  'server_connect': 'primary',
  'server_create': 'success',
  'server_update': 'warning',
  'server_delete': 'danger',
  'server_check': 'info',
  'backup': 'primary',
  'settings': 'warning',
  'import': 'success'
}

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

// 加载系统设置
const loadSystemSettings = async () => {
  try {
    const response = await preferencesAPI.getSystemSettings()
    if (response.data.success) {
      const settings = response.data.settings
      // 白名单设置
      whitelistForm.enabled = settings.login_whitelist?.enabled || false
      whitelistForm.ip_list = settings.login_whitelist?.ip_list || []
      if (whitelistForm.ip_list.length === 0) {
        whitelistForm.ip_list = ['']
      }
      // SSL设置
      sslForm.enabled = settings.ssl?.enabled || false
      sslForm.cert_path = settings.ssl?.cert_path || ''
      sslForm.key_path = settings.ssl?.key_path || ''
    }
  } catch (error) {
    const message = error.response?.data?.message || error.message || '网络连接失败'
    ElMessage.error(`加载系统设置失败: ${message}`)
  }
}

// 保存白名单设置
const saveWhitelistSettings = async () => {
  savingSettings.value = true
  try {
    const response = await preferencesAPI.updateSystemSettings({
      login_whitelist: {
        enabled: whitelistForm.enabled,
        ip_list: whitelistForm.ip_list.filter(ip => ip.trim())
      }
    })
    if (response.data.success) {
      ElMessage.success('白名单设置已保存')
    } else {
      ElMessage.error(response.data.message || '保存失败')
    }
  } catch (error) {
    const message = error.response?.data?.message || error.message || '网络连接失败'
    ElMessage.error(`保存设置失败: ${message}`)
  } finally {
    savingSettings.value = false
  }
}

// 保存SSL设置
const saveSSLSettings = async () => {
  savingSettings.value = true
  try {
    const response = await preferencesAPI.updateSystemSettings({
      ssl: {
        enabled: sslForm.enabled,
        cert_path: sslForm.cert_path,
        key_path: sslForm.key_path
      }
    })
    if (response.data.success) {
      ElMessage.success('SSL设置已保存')
    } else {
      ElMessage.error(response.data.message || '保存失败')
    }
  } catch (error) {
    const message = error.response?.data?.message || error.message || '网络连接失败'
    ElMessage.error(`保存设置失败: ${message}`)
  } finally {
    savingSettings.value = false
  }
}

// 添加白名单IP
const addWhitelistIp = () => {
  whitelistForm.ip_list.push('')
}

// 移除白名单IP
const removeWhitelistIp = (index) => {
  whitelistForm.ip_list.splice(index, 1)
  if (whitelistForm.ip_list.length === 0) {
    whitelistForm.ip_list.push('')
  }
}

// 获取日志类型标签
const getLogTypeLabel = (type) => {
  return logTypeLabels[type] || type
}

// 获取日志类型颜色
const getLogTypeColor = (type) => {
  return logTypeColors[type] || 'info'
}

// 获取日志状态类型
const getLogStatusType = (status) => {
  const statusMap = {
    'success': 'success',
    'failed': 'danger',
    'warning': 'warning'
  }
  return statusMap[status] || 'info'
}

// 获取状态标签
const getStatusLabel = (status) => {
  const labels = {
    'success': '成功',
    'failed': '失败',
    'warning': '警告'
  }
  return labels[status] || status
}

// 格式化日期时间
const formatDateTime = (isoString) => {
  if (!isoString) return '-'
  const date = new Date(isoString)
  return date.toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit'
  })
}

// 查看系统日志
const viewSystemLogs = async () => {
  logsDialogVisible.value = true
  logPage.value = 1
  await refreshLogs()
}

// 刷新日志
const refreshLogs = async () => {
  loadingLogs.value = true
  try {
    const response = await preferencesAPI.getSystemLogs({
      page: logPage.value,
      perPage: logPageSize.value,
      logType: logTypeFilter.value || undefined,
      status: logStatusFilter.value || undefined
    })
    if (response.data.success) {
      systemLogs.value = response.data.logs || []
      logTotal.value = response.data.total || 0
    } else {
      ElMessage.error(response.data.message || '获取日志失败')
    }
  } catch (error) {
    const message = error.response?.data?.message || error.message || '网络连接失败'
    ElMessage.error(`获取系统日志失败: ${message}`)
  } finally {
    loadingLogs.value = false
  }
}

// 过滤日志
const filterLogs = async () => {
  logPage.value = 1
  await refreshLogs()
}

// 加载日志类型
const loadLogTypes = async () => {
  try {
    const response = await preferencesAPI.getLogTypes()
    if (response.data.success) {
      logTypes.value = response.data.types || []
    }
  } catch (_error) {
    // 忽略错误
  }
}

// 加载日志统计
const loadLogStats = async () => {
  try {
    const response = await preferencesAPI.getLogStats()
    if (response.data.success) {
      logStats.value = response.data.stats || { total: 0, by_type: {}, by_status: {} }
    }
  } catch (_error) {
    // 忽略错误
  }
}

// 加载最近日志
const loadRecentLogs = async () => {
  try {
    const response = await preferencesAPI.getSystemLogs({
      page: 1,
      perPage: 10
    })
    if (response.data.success) {
      recentLogs.value = response.data.logs || []
    }
  } catch (_error) {
    // 忽略错误
  }
}

// 处理设置菜单选择
const handleSettingMenuSelect = async (index) => {
  activeSettingMenu.value = index
  if (index === 'logs') {
    await Promise.all([loadLogTypes(), loadLogStats(), loadRecentLogs()])
  }
}

onMounted(async () => {
  const userStr = localStorage.getItem('user')
  if (userStr) {
    currentUser.value = JSON.parse(userStr)
  }
  await loadSystemSettings()
})

const goBack = () => {
  router.push('/dashboard')
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

.header-menu :deep(.el-sub-menu.is-active .el-sub-menu__title) {
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

.content-wrapper {
  padding: 24px;
  max-width: 1400px;
  margin: 0 auto;
}

/* 设置卡片 */
.settings-card {
  border-radius: 16px;
  box-shadow: 0 4px 20px 0 rgba(0, 0, 0, 0.05);
  border: none;
}

.settings-card :deep(.el-card__header) {
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

.card-header-buttons {
  display: flex;
  gap: 10px;
}

.settings-content {
  min-height: 500px;
  padding: 16px;
}

/* 设置菜单样式 */
.settings-menu {
  border-right: 1px solid #e6e6e6;
  border-radius: 8px;
  background: #fafafa;
}

.settings-menu :deep(.el-menu-item) {
  height: 50px;
  line-height: 50px;
  font-size: 14px;
  margin: 4px 0;
  border-radius: 8px;
}

.settings-menu :deep(.el-menu-item.is-active) {
  background: linear-gradient(135deg, #409EFF 0%, #66b1ff 100%);
  color: white;
}

/* 设置面板样式 */
.setting-panel {
  padding: 20px;
  background: #fafafa;
  border-radius: 12px;
}

.setting-title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 18px;
  font-weight: 600;
  color: #303133;
  margin-bottom: 24px;
  padding-bottom: 12px;
  border-bottom: 2px solid #409EFF;
}

.form-tip {
  margin-left: 12px;
  font-size: 12px;
  color: #909399;
}

/* IP列表样式 */
.ip-list-container {
  width: 100%;
}

.ip-item {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 10px;
}

.ip-item .el-input {
  flex: 1;
}

.ip-item .el-input.is-valid :deep(.el-input__wrapper) {
  border-color: #67C23A;
  box-shadow: 0 0 0 1px #67C23A inset;
}

.ip-item .el-input.is-invalid :deep(.el-input__wrapper) {
  border-color: #F56C6C;
  box-shadow: 0 0 0 1px #F56C6C inset;
}

.valid-icon {
  color: #67C23A;
}

.invalid-icon {
  color: #F56C6C;
}

.ip-actions {
  display: flex;
  align-items: center;
  gap: 16px;
  margin-top: 12px;
}

.ip-count {
  font-size: 13px;
  color: #909399;
}

.tip-icon {
  margin-left: 8px;
  color: #909399;
  cursor: help;
}

.setting-alert {
  margin-bottom: 20px;
}

.path-hint {
  margin-top: 4px;
  font-size: 12px;
  color: #909399;
}

.path-configured :deep(.el-input__wrapper) {
  background-color: rgba(103, 194, 58, 0.05);
}

/* 日志操作区 */
.log-actions {
  display: flex;
  align-items: center;
  margin-bottom: 20px;
}

.log-description {
  margin-bottom: 16px;
  color: #606266;
  font-size: 14px;
}

.log-description p {
  margin: 0;
}

/* 日志统计 */
.log-stats {
  margin-top: 24px;
  padding: 16px;
  background: #fff;
  border-radius: 8px;
  border: 1px solid #ebeef5;
}

.log-stats h4 {
  margin: 0 0 16px 0;
  font-size: 15px;
  color: #303133;
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(120px, 1fr));
  gap: 12px;
}

.stat-item {
  display: flex;
  flex-direction: column;
  padding: 12px;
  background: #f5f7fa;
  border-radius: 8px;
  text-align: center;
}

.stat-label {
  font-size: 12px;
  color: #909399;
  margin-bottom: 4px;
}

.stat-value {
  font-size: 20px;
  font-weight: 600;
  color: #409EFF;
}

/* 最近日志 */
.recent-logs {
  margin-top: 24px;
}

.recent-logs h4 {
  margin: 0 0 16px 0;
  font-size: 15px;
  color: #303133;
}

.log-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.log-item {
  padding: 12px 16px;
  background: #fff;
  border-radius: 8px;
  border-left: 4px solid #409EFF;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
}

.log-item.log-failed {
  border-left-color: #F56C6C;
}

.log-item.log-warning {
  border-left-color: #E6A23C;
}

.log-item-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 8px;
}

.log-time {
  font-size: 12px;
  color: #909399;
}

.log-item-body {
  margin-bottom: 8px;
}

.log-action {
  font-weight: 500;
  color: #303133;
}

.log-target {
  color: #409EFF;
  margin-left: 8px;
}

.log-item-footer {
  display: flex;
  align-items: center;
  gap: 16px;
  font-size: 12px;
  color: #909399;
}

.log-user,
.log-ip {
  display: flex;
  align-items: center;
  gap: 4px;
}

/* 加载状态 */
.loading-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 60px 20px;
  color: #909399;
  width: 100%;
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

/* 日志对话框样式 */
.logs-dialog-content {
  max-height: 70vh;
  overflow-y: auto;
}

.logs-toolbar {
  display: flex;
  align-items: center;
  margin-bottom: 16px;
  padding: 12px 16px;
  background: #f5f7fa;
  border-radius: 8px;
}

.log-time-cell {
  font-family: 'Monaco', 'Menlo', 'Consolas', monospace;
  font-size: 12px;
  color: #606266;
}

.log-target-cell {
  color: #409EFF;
  font-weight: 500;
}

.log-ip-cell {
  font-family: 'Monaco', 'Menlo', 'Consolas', monospace;
  font-size: 12px;
}

.pagination-container {
  display: flex;
  justify-content: center;
  margin-top: 16px;
  padding-top: 16px;
  border-top: 1px solid #ebeef5;
}
</style>
