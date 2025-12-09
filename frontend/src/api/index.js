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
  refreshToken: () => api.post('/auth/refresh')
}

// Servers API
export const serversAPI = {
  getAll: () => api.get('/servers'),
  getById: (id) => api.get(`/servers/${id}`),
  create: (server) => api.post('/servers', server),
  update: (id, server) => api.put(`/servers/${id}`, server),
  delete: (id) => api.delete(`/servers/${id}`),
  check: (id) => api.post(`/servers/${id}/check`),
  checkAll: () => api.post('/servers/check-all'),
  verifyPassword: (id) => api.post(`/servers/${id}/verify-password`),
  checkPort: (id) => api.post(`/servers/${id}/check-port`),
  getSystemInfo: (id) => api.get(`/servers/${id}/system-info`)
}

export default api
