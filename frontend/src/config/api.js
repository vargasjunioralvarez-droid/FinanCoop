// frontend/src/config/api.js
import axios from 'axios'

const isDevelopment = import.meta.env.MODE === 'development'

// ✅ FORZAR URL CORRECTA en producción
const API_URL = isDevelopment 
  ? '/api/v1' 
  : 'https://financoop-backend.onrender.com/api/v1'  // ← CAMBIADO

console.log('🌐 Modo:', import.meta.env.MODE)
console.log('🔗 API_URL:', API_URL)

const api = axios.create({
  baseURL: API_URL
})

api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('admin_token') || localStorage.getItem('financoop_token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    if (!config.headers['Content-Type']) {
      config.headers['Content-Type'] = 'application/json'
    }
    return config
  },
  (error) => Promise.reject(error)
)

api.interceptors.response.use(
  (response) => response.data,
  (error) => {
    if (error.response?.status === 401) {
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