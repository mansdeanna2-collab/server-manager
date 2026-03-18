import axios from 'axios'
import { ElMessage } from 'element-plus'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || '/api'
const isDevelopment = import.meta.env.DEV

const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json'
  }
})

// Request interceptor to add token
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => {
    // 仅在开发环境中输出调试信息
    if (isDevelopment) {
      // eslint-disable-next-line no-console
      console.error('Request error:', error)
    }
    return Promise.reject(error)
  }
)

// Response interceptor to handle errors
api.interceptors.response.use(
  (response) => response,
  (error) => {
    const { response } = error
    
    if (!response) {
      ElMessage.error('网络异常，请检查连接。')
      return Promise.reject(error)
    }
    
    switch (response.status) {
      case 401:
        localStorage.removeItem('token')
        localStorage.removeItem('user')
        if (window.location.pathname !== '/login') {
          ElMessage.warning('登录已过期，请重新登录。')
          window.location.href = '/login'
        }
        break
      case 403:
        ElMessage.error('没有权限')
        break
      case 404:
        ElMessage.error('资源未找到')
        break
      case 429:
        ElMessage.error('请求过于频繁，请稍后再试。')
        break
      case 500:
        ElMessage.error('服务器错误，请稍后再试。')
        break
      default:
        ElMessage.error(response.data?.message || '发生错误')
    }
    
    return Promise.reject(error)
  }
)

// Auth API
export const authAPI = {
  login: (credentials) => api.post('/auth/login', credentials),
  logout: () => api.post('/auth/logout'),
  getCurrentUser: () => api.get('/auth/me'),
  refreshToken: () => api.post('/auth/refresh'),
  changePassword: (passwords) => api.post('/auth/change-password', passwords),
  // TOTP (Google Authenticator) APIs
  setupTotp: () => api.post('/auth/totp/setup'),
  enableTotp: (code) => api.post('/auth/totp/enable', { code }),
  disableTotp: (code) => api.post('/auth/totp/disable', { code }),
  getTotpStatus: () => api.get('/auth/totp/status')
}

// Servers API
export const serversAPI = {
  getAll: () => api.get('/servers'),
  getById: (id) => api.get(`/servers/${id}`),
  getPassword: (id) => api.get(`/servers/${id}/password`),
  create: (server) => api.post('/servers', server),
  update: (id, server) => api.put(`/servers/${id}`, server),
  delete: (id) => api.delete(`/servers/${id}`),
  check: (id) => api.post(`/servers/${id}/check`),
  checkAll: () => api.post('/servers/check-all'),
  checkIpStatus: (ipAddress) => api.post('/servers/check-ip-status', { ip_address: ipAddress }),
  verifyPassword: (id) => api.post(`/servers/${id}/verify-password`),
  checkPort: (id) => api.post(`/servers/${id}/check-port`),
  getSystemInfo: (id) => api.get(`/servers/${id}/system-info`),
  getIpRegion: (ipAddress) => api.get(`/servers/ip-region/${ipAddress}`),
  getPortType: (port) => api.get(`/servers/port-type/${port}`),
  importFromFiles: () => api.post('/servers/import-from-files'),
  readFile: (id, filePath) => api.post(`/servers/${id}/read-file`, { file_path: filePath }),
  listDirectory: (id, dirPath) => api.post(`/servers/${id}/list-directory`, { dir_path: dirPath }),
  saveFile: (id, filePath, content) => api.post(`/servers/${id}/save-file`, { file_path: filePath, content }),
  queryId: (ipAddress) => api.post('/servers/query-id', { ip_address: ipAddress }, { timeout: 300000 }),  // 5 minutes timeout
  getRdpFileUrl: (id, settings = {}) => {
    const params = new URLSearchParams()
    if (settings.width) params.set('width', settings.width)
    if (settings.height) params.set('height', settings.height)
    if (settings.fullscreen) params.set('fullscreen', '1')
    if (settings.clipboard === false) params.set('clipboard', '0')
    if (settings.drives) params.set('drives', '1')
    if (settings.admin) params.set('admin', '1')
    if (settings.multimon) params.set('multimon', '1')
    const query = params.toString()
    return `${API_BASE_URL}/servers/${id}/rdp-file${query ? '?' + query : ''}`
  },
  downloadRdpFile: (id, settings = {}) => {
    const params = new URLSearchParams()
    if (settings.width) params.set('width', settings.width)
    if (settings.height) params.set('height', settings.height)
    if (settings.fullscreen) params.set('fullscreen', '1')
    if (settings.clipboard === false) params.set('clipboard', '0')
    if (settings.drives) params.set('drives', '1')
    if (settings.admin) params.set('admin', '1')
    if (settings.multimon) params.set('multimon', '1')
    const query = params.toString()
    return api.get(`/servers/${id}/rdp-file${query ? '?' + query : ''}`, { responseType: 'blob' })
  }
}

// Preferences API - 用户偏好设置（存储在服务器数据库）
export const preferencesAPI = {
  // IP检测状态
  getIpCheckStatus: () => api.get('/preferences/ip-check-status'),
  saveIpCheckStatus: (data) => api.post('/preferences/ip-check-status', data),
  saveIpCheckStatusBatch: (data) => api.post('/preferences/ip-check-status/batch', data),

  // IP ID查询结果
  getIpIdResults: () => api.get('/preferences/ip-id-results'),
  saveIpIdResult: (data) => api.post('/preferences/ip-id-results', data),

  // IP段备注
  getSegmentNotes: () => api.get('/preferences/segment-notes'),
  saveSegmentNote: (segment, note) => api.post('/preferences/segment-notes', { segment, note }),

  // IP段收藏
  getSegmentFavorites: () => api.get('/preferences/segment-favorites'),
  toggleSegmentFavorite: (segment) => api.post('/preferences/segment-favorites', { segment }),

  // 服务器收藏
  getServerFavorites: () => api.get('/preferences/server-favorites'),
  toggleServerFavorite: (serverId) => api.post('/preferences/server-favorites', { server_id: serverId }),

  // 更新Cookie
  updateCookie: () => api.post('/preferences/update-cookie', {}, { timeout: 120000 }),  // 2 minutes timeout

  // 获取服务器任务状态（持久化到数据库）
  getFetchServerTasks: () => api.get('/preferences/fetch-server-tasks'),
  getFetchServerTask: (ipAddress) => api.get(`/preferences/fetch-server-tasks/${ipAddress}`),
  getRunningFetchServerTasks: () => api.get('/preferences/fetch-server-tasks/running'),
  saveFetchServerTask: (data) => api.post('/preferences/fetch-server-tasks', data),
  deleteFetchServerTask: (ipAddress) => api.delete(`/preferences/fetch-server-tasks/${ipAddress}`),

  // 系统备份
  createBackup: () => api.post('/preferences/backup/create', {}, { timeout: 300000 }),  // 5 minutes timeout
  listBackups: () => api.get('/preferences/backup/list'),
  deleteBackup: (backupId) => api.delete(`/preferences/backup/delete/${backupId}`),
  verifyBackup: (backupId) => api.get(`/preferences/backup/verify/${backupId}`),
  getBackupStats: () => api.get('/preferences/backup/stats'),
  // 下载备份使用特殊方法，因为需要处理文件流
  getBackupDownloadUrl: (backupId) => `${API_BASE_URL}/preferences/backup/download/${backupId}`,

  // 数据库结构和数据查看
  getDatabaseSchema: () => api.get('/preferences/database/schema'),
  getDatabaseTableData: (tableName, page = 1, perPage = 50) => 
    api.get(`/preferences/database/data/${tableName}?page=${page}&per_page=${perPage}`),

  // 系统设置
  getSystemSettings: () => api.get('/preferences/system-settings'),
  updateSystemSettings: (settings) => api.post('/preferences/system-settings', { settings }),

  // SSL自动配置
  detectSSLAddress: (address) => api.post('/preferences/ssl/detect-address', { address }),
  detectServerAddress: () => api.get('/preferences/ssl/detect-server'),
  autoConfigureSSL: (address = '') => api.post('/preferences/ssl/auto-configure', { address }),
  verifySSLCertificate: (certPath, keyPath) => 
    api.post('/preferences/ssl/verify', { cert_path: certPath, key_path: keyPath }),

  // 系统日志
  getSystemLogs: (params = {}) => {
    const { page = 1, perPage = 100, logType, status } = params
    let url = `/preferences/system-logs?page=${page}&per_page=${perPage}`
    if (logType) url += `&log_type=${logType}`
    if (status) url += `&status=${status}`
    return api.get(url)
  },
  getLogTypes: () => api.get('/preferences/system-logs/types'),
  getLogStats: () => api.get('/preferences/system-logs/stats'),

  // 版本检测
  getVersionInfo: () => api.get('/preferences/version'),
  checkForUpdates: () => api.get('/preferences/version/check')
}

export default api
