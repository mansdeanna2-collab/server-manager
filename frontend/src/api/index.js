import axios from 'axios'
import { ElMessage } from 'element-plus'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || '/api'

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
    console.error('Request error:', error)
    return Promise.reject(error)
  }
)

// Response interceptor to handle errors
api.interceptors.response.use(
  (response) => response,
  (error) => {
    const { response } = error
    
    if (!response) {
      ElMessage.error('Network error. Please check your connection.')
      return Promise.reject(error)
    }
    
    switch (response.status) {
      case 401:
        localStorage.removeItem('token')
        localStorage.removeItem('user')
        if (window.location.pathname !== '/login') {
          ElMessage.warning('Session expired. Please login again.')
          window.location.href = '/login'
        }
        break
      case 403:
        ElMessage.error('Access denied')
        break
      case 404:
        ElMessage.error('Resource not found')
        break
      case 429:
        ElMessage.error('Too many requests. Please try again later.')
        break
      case 500:
        ElMessage.error('Server error. Please try again later.')
        break
      default:
        ElMessage.error(response.data?.message || 'An error occurred')
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
