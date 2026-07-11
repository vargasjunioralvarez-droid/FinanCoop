// frontend/src/config/api.js
import axios from 'axios'

// Usar variable de entorno o fallback local
const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

const api = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json'
  }
})

// ============================================================
// ✅ INTERCEPTOR PARA AGREGAR EL TOKEN AUTOMÁTICAMENTE
// ============================================================
api.interceptors.request.use(
  (config) => {
    // Buscar token de administrador
    const adminToken = localStorage.getItem('admin_token')
    
    // Si hay un token de admin, usarlo
    if (adminToken) {
      config.headers.Authorization = `Bearer ${adminToken}`
      console.log('🔑 Token de admin agregado a:', config.url)
    } else {
      // Si no, buscar token de cliente
      const clienteToken = localStorage.getItem('financoop_token')
      if (clienteToken) {
        config.headers.Authorization = `Bearer ${clienteToken}`
        console.log('🔑 Token de cliente agregado a:', config.url)
      } else {
        console.log('⚠️ No hay token para:', config.url)
      }
    }
    
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

// ============================================================
// ✅ INTERCEPTOR PARA MANEJAR ERRORES 401
// ============================================================
api.interceptors.response.use(
  (response) => {
    return response
  },
  (error) => {
    if (error.response && error.response.status === 401) {
      console.warn('⚠️ Token inválido o expirado')
      
      // Si la petición era para una ruta de admin, limpiar el token de admin
      if (error.config.url.includes('/admin/')) {
        localStorage.removeItem('admin_token')
        localStorage.removeItem('admin_rol')
        localStorage.removeItem('admin_username')
        
        // Redirigir al login de admin
        if (!window.location.pathname.includes('/admin-login')) {
          window.location.href = '/admin-login'
        }
      }
    }
    return Promise.reject(error)
  }
)

export default api