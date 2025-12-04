import axios from 'axios'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || '/api'

const api = axios.create({
  baseURL: API_BASE_URL,
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
    return Promise.reject(error)
  }
)

// Response interceptor to handle errors
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('token')
      localStorage.removeItem('user')
      window.location.href = '/login'
    }
    return Promise.reject(error)
  }
)

// Auth API
export const authAPI = {
  login: (credentials) => api.post('/auth/login', credentials),
  logout: () => api.post('/auth/logout'),
  getCurrentUser: () => api.get('/auth/me')
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
