// frontend/src/config/api.js
import axios from 'axios'

// 🔥 FORZAR A USAR /api EN DESARROLLO
const isDevelopment = import.meta.env.MODE === 'development'
const API_URL = isDevelopment ? '/api' : (import.meta.env.VITE_API_URL || 'https://financoop.onrender.com')

console.log('🌐 Modo:', import.meta.env.MODE)
console.log('🔗 API_URL:', API_URL)

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
    
    // 🔥 IMPORTANTE: Mostrar la URL completa
    console.log('📡 [API] URL completa:', config.baseURL + config.url)
    
    return config
  },
  (error) => Promise.reject(error)
)

// Interceptor para manejar respuestas
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