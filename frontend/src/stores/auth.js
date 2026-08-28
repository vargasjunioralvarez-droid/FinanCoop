import { defineStore } from 'pinia'
import { api } from '@/config/api'

export const useAuthStore = defineStore('auth', {
  state: () => ({
    token: localStorage.getItem('admin_token') || null,
    rol: localStorage.getItem('admin_rol') || null,
    username: localStorage.getItem('admin_username') || '',
    nombre: localStorage.getItem('admin_nombre') || '',
    tiendaNombre: '',
    tasaActual: null,  // Cambiado de 40 a null
  }),

  getters: {
    estaLogueado: (state) => !!state.token,
    esAdmin: (state) => state.rol === 'admin_central',
    esAdminOTienda: (state) => state.rol === 'admin_central' || state.rol === 'admin_tienda',
    esCajero: (state) => state.rol === 'cajero',
  },

  actions: {
    async login(username, password) {
      const data = await api.post('/auth/login-json', { username, password })
      this.token = data.access_token
      this.rol = data.rol
      this.username = data.username
      this.nombre = data.nombre || ''
      this.tiendaNombre = data.tienda_nombre || ''
      localStorage.setItem('admin_token', data.access_token)
      localStorage.setItem('admin_rol', data.rol)
      localStorage.setItem('admin_username', data.username)
      localStorage.setItem('admin_nombre', data.nombre || '')
      return data
    },

    async cargarUsuario() {
      if (!this.token) return
      try {
        const data = await api.get('/auth/verificar')
        if (data) this.tiendaNombre = data.tienda_nombre || ''
      } catch (e) {}
    },

    async cargarTasa() {
      try {
        const data = await api.get('/config/tasa-dolar')
        if (data && data.tasa) this.tasaActual = data.tasa
      } catch (e) {}
    },

    logout() {
      this.token = null
      this.rol = null
      this.username = ''
      this.nombre = ''
      this.tiendaNombre = ''
      localStorage.removeItem('admin_token')
      localStorage.removeItem('admin_rol')
      localStorage.removeItem('admin_username')
      localStorage.removeItem('admin_nombre')
      window.location.href = '/login'
    }
  }
})