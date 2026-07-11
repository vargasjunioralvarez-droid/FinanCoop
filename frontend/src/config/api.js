// frontend/src/config/api.js
import axios from 'axios'

const API_URL = import.meta.env.VITE_API_URL || 'https://financoop.onrender.com'

const api = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json'
  }
})

// Interceptor para agregar token
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('admin_token') || localStorage.getItem('financoop_token')
    
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
      console.log('🔑 [API] Token enviado a:', config.url)
    } else {
      console.log('⚠️ [API] Sin token para:', config.url)
    }
    
    return config
  },
  (error) => Promise.reject(error)
)

// Interceptor para devolver data directamente
api.interceptors.response.use(
  (response) => {
    console.log('✅ [API] OK:', response.config.url, response.status)
    return response.data
  },
  (error) => {
    if (error.response?.status === 401) {
      console.warn('⚠️ [API] 401:', error.config?.url)
      if (!window.location.pathname.includes('/login')) {
        localStorage.clear()
        window.location.href = '/login'
      }
    }
    return Promise.reject(error)
  }
)

export { api, API_URL }
export default api