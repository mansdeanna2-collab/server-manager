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
                  <span>信息查询 - IP段配置</span>
                </div>
                <el-button
                  type="primary"
                  :loading="loading"
                  @click="loadServers"
                >
                  <el-icon><Refresh /></el-icon>
                  刷新数据
                </el-button>
              </div>
            </template>
            
            <div class="info-content">
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
                  正在加载数据...
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
                v-else-if="ipSegments.length === 0"
                description="暂无服务器数据"
              />

              <!-- IP Segment List -->
              <div
                v-else
                class="segment-list"
              >
                <div class="segment-stats">
                  <el-tag
                    type="info"
                    size="large"
                    effect="dark"
                  >
                    共 {{ ipSegments.length }} 个IP段
                  </el-tag>
                  <el-tag
                    type="success"
                    size="large"
                    effect="dark"
                  >
                    共 {{ totalServers }} 台服务器
                  </el-tag>
                </div>

                <el-table
                  :data="paginatedSegments"
                  style="width: 100%"
                  stripe
                  border
                >
                  <el-table-column
                    label="IP段"
                    width="180"
                  >
                    <template #default="scope">
                      <span class="ip-segment-text">{{ scope.row.segment }}.x</span>
                    </template>
                  </el-table-column>
                  <el-table-column
                    prop="count"
                    label="服务器数量"
                    width="120"
                    align="center"
                  >
                    <template #default="scope">
                      <el-tag
                        type="primary"
                        effect="plain"
                      >
                        {{ scope.row.count }} 台
                      </el-tag>
                    </template>
                  </el-table-column>
                  <el-table-column
                    label="在线状态"
                    width="200"
                    align="center"
                  >
                    <template #default="scope">
                      <div class="status-tags">
                        <el-tag
                          v-if="scope.row.onlineCount > 0"
                          type="success"
                          size="small"
                        >
                          在线 {{ scope.row.onlineCount }}
                        </el-tag>
                        <el-tag
                          v-if="scope.row.offlineCount > 0"
                          type="danger"
                          size="small"
                        >
                          离线 {{ scope.row.offlineCount }}
                        </el-tag>
                        <el-tag
                          v-if="scope.row.unknownCount > 0"
                          type="info"
                          size="small"
                        >
                          未知 {{ scope.row.unknownCount }}
                        </el-tag>
                      </div>
                    </template>
                  </el-table-column>
                  <el-table-column
                    label="备注"
                    min-width="200"
                  >
                    <template #default="scope">
                      <span
                        v-if="scope.row.note"
                        class="segment-note"
                      >{{ scope.row.note }}</span>
                      <span
                        v-else
                        class="no-note"
                      >暂无备注</span>
                    </template>
                  </el-table-column>
                  <el-table-column
                    label="IP范围"
                    min-width="180"
                  >
                    <template #default="scope">
                      <span class="ip-range">{{ scope.row.segment }}.1 - {{ scope.row.segment }}.255</span>
                    </template>
                  </el-table-column>
                </el-table>

                <div
                  v-if="ipSegments.length > PAGE_SIZE"
                  class="pagination-container"
                >
                  <el-pagination
                    v-model:current-page="currentPage"
                    :page-size="PAGE_SIZE"
                    :total="ipSegments.length"
                    layout="prev, pager, next"
                    background
                  />
                </div>
              </div>
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
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, computed } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'
import {
  ArrowDown, Monitor, Odometer, OfficeBuilding, Search, User, Setting, FolderOpened, Refresh, Loading
} from '@element-plus/icons-vue'
import { authAPI, serversAPI } from '@/api'

const router = useRouter()
const route = useRoute()
const currentUser = ref(null)
const passwordDialogVisible = ref(false)
const changingPassword = ref(false)
const passwordFormRef = ref(null)
const loading = ref(false)
const loadError = ref('')
const servers = ref([])
const currentPage = ref(1)
const PAGE_SIZE = 15

// IP段备注存储键
const SEGMENT_NOTES_KEY = 'server_manager_segment_notes'
const segmentNotes = ref({})

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

// 获取IP段（前3个字节）
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

// 比较IP段（数值排序）
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

// 按IP段分组的服务器数据
const ipSegments = computed(() => {
  const segmentMap = new Map()

  servers.value.forEach(server => {
    const segment = getIpSegment(server.ip_address)
    if (!segment) return
    
    if (!segmentMap.has(segment)) {
      segmentMap.set(segment, {
        segment: segment,
        count: 0,
        onlineCount: 0,
        offlineCount: 0,
        unknownCount: 0,
        note: segmentNotes.value[segment] || ''
      })
    }
    
    const segmentData = segmentMap.get(segment)
    segmentData.count++
    
    if (server.status === 'online') {
      segmentData.onlineCount++
    } else if (server.status === 'offline') {
      segmentData.offlineCount++
    } else {
      segmentData.unknownCount++
    }
  })

  // 转换为数组并按IP段排序
  const result = Array.from(segmentMap.values())
  result.sort(compareIpSegments)
  return result
})

// 服务器总数
const totalServers = computed(() => servers.value.length)

// 分页后的IP段数据
const paginatedSegments = computed(() => {
  const start = (currentPage.value - 1) * PAGE_SIZE
  const end = start + PAGE_SIZE
  return ipSegments.value.slice(start, end)
})

// 加载服务器数据
const loadServers = async () => {
  loading.value = true
  loadError.value = ''
  try {
    const response = await serversAPI.getAll()
    servers.value = response.data || []
  } catch (error) {
    const message = error.response?.data?.message || error.message || '网络连接失败'
    loadError.value = message
    ElMessage.error(`加载数据失败: ${message}`)
  } finally {
    loading.value = false
  }
}

// 初始化备注数据
const initSegmentNotes = () => {
  try {
    const savedNotes = localStorage.getItem(SEGMENT_NOTES_KEY)
    if (savedNotes) {
      segmentNotes.value = JSON.parse(savedNotes)
    }
  } catch (_e) {
    segmentNotes.value = {}
  }
}

onMounted(async () => {
  const userStr = localStorage.getItem('user')
  if (userStr) {
    currentUser.value = JSON.parse(userStr)
  }
  initSegmentNotes()
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

.info-content {
  min-height: 400px;
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

/* IP段列表 */
.segment-list {
  padding: 16px 0;
}

.segment-stats {
  display: flex;
  gap: 16px;
  margin-bottom: 20px;
}

.ip-segment-text {
  font-family: 'Monaco', 'Menlo', 'Consolas', monospace;
  font-size: 15px;
  font-weight: 600;
  color: #409EFF;
}

.status-tags {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
  justify-content: center;
}

.segment-note {
  color: #606266;
}

.no-note {
  color: #c0c4cc;
  font-style: italic;
}

.ip-range {
  font-family: 'Monaco', 'Menlo', 'Consolas', monospace;
  font-size: 13px;
  color: #909399;
}

/* 分页容器 */
.pagination-container {
  display: flex;
  justify-content: center;
  margin-top: 20px;
  padding-top: 20px;
  border-top: 1px solid #f0f0f0;
}
</style>
