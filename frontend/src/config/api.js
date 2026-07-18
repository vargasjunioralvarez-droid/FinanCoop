// frontend/src/config/api.js
import axios from 'axios'

// 🔥 URL dinámica con /api/v1 para desarrollo y producción
const isDevelopment = import.meta.env.MODE === 'development'
const API_URL = isDevelopment 
  ? '/api/v1' 
  : (import.meta.env.VITE_API_URL || 'https://financoop-backend.onrender.com/api/v1')

console.log('🌐 Modo:', import.meta.env.MODE)
console.log('🔗 API_URL:', API_URL)

const api = axios.create({
  baseURL: API_URL
})

// Interceptor para agregar token
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('admin_token') || localStorage.getItem('financoop_token')
    
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    
    // Solo setear Content-Type si no fue definido manualmente
    if (!config.headers['Content-Type']) {
      config.headers['Content-Type'] = 'application/json'
    }
    
    return config
  },
  (error) => Promise.reject(error)
)

// Interceptor para manejar respuestas
api.interceptors.response.use(
  (response) => {
    return response.data
  },
  (error) => {
    if (error.response?.status === 401) {
      console.warn('⚠️ [API] 401 - Token expirado o inválido')
      if (!window.location.pathname.includes('/login')) {
        localStorage.clear()
        window.location.href = '/login'
      }
    }
    if (error.response?.status === 429) {
      console.warn('⚠️ [API] 429 - Demasiados intentos')
    }
    return Promise.reject(error)
  }
)

export { api, API_URL }
export default api