import axios from 'axios'

const isDevelopment = import.meta.env.MODE === 'development'
const API_URL = isDevelopment 
  ? '/api/v1' 
  : 'https://financoop-agd5.onrender.com/api/v1'

console.log('🌐 Modo:', import.meta.env.MODE)
console.log('🔗 API_URL:', API_URL)

const api = axios.create({
  baseURL: API_URL
})

// 🔐 INTERCEPTOR DE REQUEST - Agregar token SIEMPRE
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

// 📦 INTERCEPTOR DE RESPONSE - Extraer arrays y manejar errores
api.interceptors.response.use(
  (response) => {
    const data = response.data
    
    if (data && typeof data === 'object') {
      if (Array.isArray(data.usuarios)) return data.usuarios
      if (Array.isArray(data.clientes)) return data.clientes
      if (Array.isArray(data.financiamientos)) return data.financiamientos
      if (Array.isArray(data.pagos)) return data.pagos
      if (Array.isArray(data.cuotas)) return data.cuotas
    }
    
    return data
  },
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