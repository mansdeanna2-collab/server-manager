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
          <el-card class="backup-card">
            <template #header>
              <div class="card-header">
                <div class="card-header-title">
                  <el-icon
                    class="card-header-icon"
                    :size="20"
                  >
                    <FolderOpened />
                  </el-icon>
                  <span>系统备份</span>
                </div>
                <div class="card-header-buttons">
                  <el-button
                    type="info"
                    :loading="loadingSchema"
                    @click="handleViewDatabase"
                  >
                    <el-icon><Grid /></el-icon>
                    查看数据库
                  </el-button>
                  <el-button
                    type="success"
                    :loading="creatingBackup"
                    @click="handleCreateBackup"
                  >
                    <el-icon><Upload /></el-icon>
                    备份系统
                  </el-button>
                  <el-button
                    type="primary"
                    :loading="loadingBackups"
                    @click="loadBackupList"
                  >
                    <el-icon><Refresh /></el-icon>
                    刷新列表
                  </el-button>
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
            
            <div class="backup-content">
              <!-- Loading State -->
              <div
                v-if="loadingBackups"
                class="loading-container"
              >
                <el-icon
                  class="loading-icon"
                  :size="40"
                >
                  <Loading />
                </el-icon>
                <p class="loading-text">
                  正在加载备份列表...
                </p>
              </div>

              <!-- Empty State -->
              <el-empty
                v-else-if="backupList.length === 0"
                description="暂无备份文件，点击【备份系统】按钮创建新的备份"
              />

              <!-- Backup List -->
              <div
                v-else
                class="backup-list"
              >
                <div class="backup-stats">
                  <el-tag
                    type="info"
                    size="large"
                    effect="dark"
                  >
                    共 {{ backupList.length }} 个备份文件
                  </el-tag>
                </div>

                <el-table
                  :data="backupList"
                  style="width: 100%"
                  stripe
                  border
                >
                  <el-table-column
                    label="文件名"
                    min-width="280"
                  >
                    <template #default="scope">
                      <span class="backup-filename">{{ scope.row.filename }}</span>
                    </template>
                  </el-table-column>
                  <el-table-column
                    label="文件大小"
                    width="150"
                    align="center"
                  >
                    <template #default="scope">
                      <el-tag
                        type="primary"
                        effect="plain"
                      >
                        {{ scope.row.size_formatted }}
                      </el-tag>
                    </template>
                  </el-table-column>
                  <el-table-column
                    label="创建时间"
                    width="200"
                    align="center"
                  >
                    <template #default="scope">
                      <span class="backup-time">{{ scope.row.created_at || '-' }}</span>
                    </template>
                  </el-table-column>
                  <el-table-column
                    label="操作"
                    width="200"
                    align="center"
                    fixed="right"
                  >
                    <template #default="scope">
                      <div class="operation-buttons">
                        <el-button
                          type="primary"
                          size="small"
                          @click="handleDownloadBackup(scope.row)"
                        >
                          <el-icon><Download /></el-icon>
                          下载
                        </el-button>
                        <el-button
                          type="danger"
                          size="small"
                          @click="handleDeleteBackup(scope.row)"
                        >
                          <el-icon><Delete /></el-icon>
                          删除
                        </el-button>
                      </div>
                    </template>
                  </el-table-column>
                </el-table>
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
    
    <!-- Database Dialog -->
    <el-dialog
      v-model="databaseDialogVisible"
      title="数据库查看"
      width="1100px"
      top="3vh"
      :close-on-click-modal="false"
    >
      <div
        v-if="loadingSchema"
        class="loading-container"
      >
        <el-icon
          class="loading-icon"
          :size="40"
        >
          <Loading />
        </el-icon>
        <p class="loading-text">
          正在加载数据库...
        </p>
      </div>
      <div
        v-else
        class="database-content"
      >
        <el-alert
          type="info"
          :closable="false"
          style="margin-bottom: 16px;"
        >
          <template #title>
            <el-icon><InfoFilled /></el-icon>
            仅供查看，不可修改数据库内容
          </template>
        </el-alert>
        
        <!-- 表选择和视图切换 -->
        <div class="database-toolbar">
          <el-select
            v-model="selectedTable"
            placeholder="选择表"
            style="width: 200px;"
            @change="handleTableSelect"
          >
            <el-option
              v-for="table in databaseSchema"
              :key="table.name"
              :label="`${table.name} (${table.columns.length}列)`"
              :value="table.name"
            />
          </el-select>
          <el-radio-group
            v-model="viewMode"
            size="small"
            style="margin-left: 16px;"
          >
            <el-radio-button value="data">
              <el-icon><List /></el-icon>
              数据
            </el-radio-button>
            <el-radio-button value="structure">
              <el-icon><Grid /></el-icon>
              结构
            </el-radio-button>
          </el-radio-group>
          <el-button
            v-if="viewMode === 'data' && selectedTable"
            size="small"
            type="primary"
            :loading="loadingTableData"
            style="margin-left: auto;"
            @click="loadTableData"
          >
            <el-icon><Refresh /></el-icon>
            刷新数据
          </el-button>
        </div>
        
        <!-- 表结构视图 -->
        <div
          v-if="viewMode === 'structure' && selectedTable"
          class="table-structure"
        >
          <h4 class="section-title">
            表结构: {{ selectedTable }}
          </h4>
          <el-table
            :data="selectedTableColumns"
            stripe
            border
            size="small"
          >
            <el-table-column
              prop="name"
              label="列名"
              width="200"
            >
              <template #default="scope">
                <span :class="{ 'primary-key': scope.row.primary_key }">
                  {{ scope.row.name }}
                  <el-tag
                    v-if="scope.row.primary_key"
                    size="small"
                    type="warning"
                  >
                    主键
                  </el-tag>
                </span>
              </template>
            </el-table-column>
            <el-table-column
              prop="type"
              label="数据类型"
              width="150"
            />
            <el-table-column
              prop="nullable"
              label="可为空"
              width="100"
              align="center"
            >
              <template #default="scope">
                <el-tag
                  :type="scope.row.nullable ? 'success' : 'danger'"
                  size="small"
                >
                  {{ scope.row.nullable ? '是' : '否' }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column
              prop="default"
              label="默认值"
            >
              <template #default="scope">
                <span class="default-value">{{ scope.row.default || '-' }}</span>
              </template>
            </el-table-column>
          </el-table>
        </div>
        
        <!-- 表数据视图 -->
        <div
          v-if="viewMode === 'data' && selectedTable"
          class="table-data"
        >
          <div class="data-header">
            <h4 class="section-title">
              表数据: {{ selectedTable }}
            </h4>
            <el-tag type="info">
              共 {{ tableDataTotal }} 条记录
            </el-tag>
          </div>
          
          <div
            v-if="loadingTableData"
            class="loading-container small"
          >
            <el-icon class="loading-icon">
              <Loading />
            </el-icon>
            <span>加载中...</span>
          </div>
          
          <el-table
            v-else
            :data="tableData"
            stripe
            border
            size="small"
            max-height="400"
            style="width: 100%;"
          >
            <el-table-column
              v-for="col in selectedTableColumns"
              :key="col.name"
              :prop="col.name"
              :label="col.name"
              :min-width="getColumnWidth(col)"
              show-overflow-tooltip
            >
              <template #default="scope">
                <span :class="{ 'primary-key-value': col.primary_key }">
                  {{ formatCellValue(scope.row[col.name]) }}
                </span>
              </template>
            </el-table-column>
          </el-table>
          
          <!-- 分页 -->
          <div
            v-if="tableDataTotal > 0"
            class="pagination-container"
          >
            <el-pagination
              v-model:current-page="tableDataPage"
              v-model:page-size="tableDataPageSize"
              :page-sizes="[20, 50, 100, 200]"
              :total="tableDataTotal"
              layout="total, sizes, prev, pager, next, jumper"
              @size-change="loadTableData"
              @current-change="loadTableData"
            />
          </div>
        </div>
        
        <!-- 未选择表时的提示 -->
        <el-empty
          v-if="!selectedTable"
          description="请从上方选择一个表来查看"
        />
      </div>
      <template #footer>
        <el-button @click="databaseDialogVisible = false">
          关闭
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, computed } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  ArrowDown, Back, Delete, Download, FolderOpened, Grid, InfoFilled, List, Loading, Monitor, Odometer, OfficeBuilding, Refresh, Search, Setting, Tools, Upload, User
} from '@element-plus/icons-vue'
import { authAPI, preferencesAPI } from '@/api'

const router = useRouter()
const route = useRoute()
const currentUser = ref(null)
const passwordDialogVisible = ref(false)
const changingPassword = ref(false)
const passwordFormRef = ref(null)

// 备份相关状态
const creatingBackup = ref(false)
const loadingBackups = ref(false)
const backupList = ref([])

// 数据库相关状态
const databaseDialogVisible = ref(false)
const loadingSchema = ref(false)
const databaseSchema = ref([])
const selectedTable = ref('')
const viewMode = ref('data')
const loadingTableData = ref(false)
const tableData = ref([])
const tableDataTotal = ref(0)
const tableDataPage = ref(1)
const tableDataPageSize = ref(50)

// 计算属性：获取选中表的列信息
const selectedTableColumns = computed(() => {
  if (!selectedTable.value || !databaseSchema.value.length) return []
  const table = databaseSchema.value.find(t => t.name === selectedTable.value)
  return table ? table.columns : []
})

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

// 加载备份列表
const loadBackupList = async () => {
  loadingBackups.value = true
  try {
    const response = await preferencesAPI.listBackups()
    if (response.data.success) {
      backupList.value = response.data.backups || []
    } else {
      ElMessage.error(response.data.message || '获取备份列表失败')
    }
  } catch (error) {
    const message = error.response?.data?.message || error.message || '网络连接失败'
    ElMessage.error(`获取备份列表失败: ${message}`)
  } finally {
    loadingBackups.value = false
  }
}

// 创建备份
const handleCreateBackup = async () => {
  creatingBackup.value = true
  try {
    const response = await preferencesAPI.createBackup()
    if (response.data.success) {
      ElMessage.success(`系统备份创建成功，文件大小: ${response.data.size_formatted}`)
      // 刷新备份列表
      await loadBackupList()
    } else {
      ElMessage.error(response.data.message || '创建备份失败')
    }
  } catch (error) {
    const message = error.response?.data?.message || error.message || '网络连接失败'
    ElMessage.error(`创建备份失败: ${message}`)
  } finally {
    creatingBackup.value = false
  }
}

// 下载备份
const handleDownloadBackup = async (backup) => {
  const downloadUrl = preferencesAPI.getBackupDownloadUrl(backup.backup_id)
  const token = localStorage.getItem('token')
  
  try {
    // 使用fetch获取文件并触发下载
    const response = await fetch(downloadUrl, {
      headers: {
        'Authorization': `Bearer ${token}`
      }
    })
    
    if (!response.ok) {
      // 尝试解析错误消息
      let errorMessage = '下载失败'
      try {
        const errorData = await response.json()
        errorMessage = errorData.message || errorMessage
      } catch (_e) {
        // 如果无法解析JSON，使用状态文本
        errorMessage = response.statusText || errorMessage
      }
      throw new Error(errorMessage)
    }
    
    const blob = await response.blob()
    // 创建下载链接
    const url = window.URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = backup.filename
    document.body.appendChild(a)
    a.click()
    window.URL.revokeObjectURL(url)
    document.body.removeChild(a)
    ElMessage.success('备份文件下载成功')
  } catch (error) {
    ElMessage.error(`下载备份失败: ${error.message}`)
  }
}

// 删除备份
const handleDeleteBackup = async (backup) => {
  try {
    await ElMessageBox.confirm(
      `确定要删除备份文件 "${backup.filename}" 吗？此操作不可恢复。`,
      '删除确认',
      {
        confirmButtonText: '确定删除',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )
    
    const response = await preferencesAPI.deleteBackup(backup.backup_id)
    if (response.data.success) {
      ElMessage.success('备份文件已删除')
      // 刷新备份列表
      await loadBackupList()
    } else {
      ElMessage.error(response.data.message || '删除备份失败')
    }
  } catch (error) {
    if (error !== 'cancel') {
      const message = error.response?.data?.message || error.message || '删除失败'
      ElMessage.error(`删除备份失败: ${message}`)
    }
  }
}

onMounted(async () => {
  const userStr = localStorage.getItem('user')
  if (userStr) {
    currentUser.value = JSON.parse(userStr)
  }
  // 加载备份列表
  await loadBackupList()
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

// 查看数据库
const handleViewDatabase = async () => {
  databaseDialogVisible.value = true
  loadingSchema.value = true
  selectedTable.value = ''
  tableData.value = []
  tableDataTotal.value = 0
  
  try {
    const response = await preferencesAPI.getDatabaseSchema()
    if (response.data.success) {
      databaseSchema.value = response.data.tables || []
      // 默认选中第一个表
      if (databaseSchema.value.length > 0) {
        selectedTable.value = databaseSchema.value[0].name
        await loadTableData()
      }
    } else {
      ElMessage.error(response.data.message || '获取数据库结构失败')
    }
  } catch (error) {
    const message = error.response?.data?.message || error.message || '网络连接失败'
    ElMessage.error(`获取数据库结构失败: ${message}`)
  } finally {
    loadingSchema.value = false
  }
}

// 处理表选择变化
const handleTableSelect = async () => {
  tableDataPage.value = 1
  tableData.value = []
  tableDataTotal.value = 0
  if (viewMode.value === 'data') {
    await loadTableData()
  }
}

// 加载表数据
const loadTableData = async () => {
  if (!selectedTable.value) return
  
  loadingTableData.value = true
  try {
    const response = await preferencesAPI.getDatabaseTableData(
      selectedTable.value,
      tableDataPage.value,
      tableDataPageSize.value
    )
    if (response.data.success) {
      tableData.value = response.data.data || []
      tableDataTotal.value = response.data.total || 0
    } else {
      ElMessage.error(response.data.message || '获取表数据失败')
    }
  } catch (error) {
    const message = error.response?.data?.message || error.message || '网络连接失败'
    ElMessage.error(`获取表数据失败: ${message}`)
  } finally {
    loadingTableData.value = false
  }
}

// 获取列宽度
const getColumnWidth = (col) => {
  const type = col.type.toLowerCase()
  if (type.includes('text') || type.includes('varchar(255)')) return 200
  if (type.includes('datetime')) return 180
  if (type.includes('integer') || type.includes('int')) return 100
  if (type.includes('boolean')) return 80
  return 150
}

// 格式化单元格值
const formatCellValue = (value) => {
  if (value === null || value === undefined) return '-'
  if (typeof value === 'boolean') return value ? '是' : '否'
  if (typeof value === 'string' && value.length > 100) {
    return value.substring(0, 100) + '...'
  }
  return String(value)
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

/* 备份卡片 */
.backup-card {
  border-radius: 16px;
  box-shadow: 0 4px 20px 0 rgba(0, 0, 0, 0.05);
  border: none;
}

.backup-card :deep(.el-card__header) {
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
  color: #67C23A;
}

.card-header-buttons {
  display: flex;
  gap: 10px;
}

.backup-content {
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

/* 备份列表 */
.backup-list {
  padding: 16px 0;
}

.backup-stats {
  display: flex;
  gap: 16px;
  margin-bottom: 20px;
}

.backup-filename {
  font-family: 'Monaco', 'Menlo', 'Consolas', monospace;
  font-size: 14px;
  font-weight: 500;
  color: #409EFF;
}

.backup-time {
  color: #606266;
  font-size: 14px;
}

/* 操作按钮容器 */
.operation-buttons {
  display: flex;
  gap: 8px;
  justify-content: center;
}

/* 数据库对话框样式 */
.database-content {
  max-height: 70vh;
  overflow-y: auto;
}

.database-toolbar {
  display: flex;
  align-items: center;
  margin-bottom: 16px;
  padding: 12px 16px;
  background: #f5f7fa;
  border-radius: 8px;
}

.section-title {
  font-size: 16px;
  font-weight: 600;
  color: #303133;
  margin: 0 0 12px 0;
}

.table-structure,
.table-data {
  margin-top: 16px;
}

.data-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 12px;
}

.table-header {
  display: flex;
  align-items: center;
  gap: 8px;
}

.table-name {
  font-weight: 600;
  color: #303133;
}

.primary-key {
  display: flex;
  align-items: center;
  gap: 8px;
  font-weight: 500;
  color: #E6A23C;
}

.primary-key-value {
  color: #E6A23C;
  font-weight: 500;
}

.default-value {
  font-family: 'Monaco', 'Menlo', 'Consolas', monospace;
  font-size: 12px;
  color: #909399;
}

.pagination-container {
  display: flex;
  justify-content: center;
  margin-top: 16px;
  padding-top: 16px;
  border-top: 1px solid #ebeef5;
}

.loading-container.small {
  padding: 30px 20px;
  flex-direction: row;
  gap: 8px;
}
</style>
