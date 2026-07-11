// frontend/src/router.js
import { createRouter, createWebHistory } from 'vue-router'

// Importar vistas principales
import InicioView from '@/views/InicioView.vue'
import CuotasView from '@/views/CuotasView.vue'
import PagarView from '@/views/PagarView.vue'
import ExplorarView from '@/views/ExplorarView.vue'
import PerfilView from '@/views/PerfilView.vue'
import LoginView from '@/views/LoginView.vue'
import RegisterView from '@/views/RegisterView.vue'
import RegisterSuccessView from '@/views/RegisterSuccessView.vue'

// ADMIN - Vistas de administración
import AdminLoginView from '@/views/AdminLogin.vue'
import UsuariosView from '@/views/UsuariosView.vue'
import ClientesAdminView from '@/views/ClientesAdmin.vue'

// CLIENTE - Vistas normales
import Dashboard from '@/views/Dashboard.vue'
import CajeroView from '@/views/CajeroView.vue'
import Clientes from '@/views/Clientes.vue'
import Financiamientos from '@/views/Financiamientos.vue'
import Cuotas from '@/views/Cuotas.vue'
import ConciliacionView from '@/views/ConciliacionView.vue'
import ConfiguracionView from '@/views/ConfiguracionView.vue'
import NivelesView from '@/views/NivelesView.vue'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    // ... (todas tus rutas, igual que antes)
  ]
})

// ✅ Guardia de navegación (sin importar useFinanCash)
router.beforeEach((to, from, next) => {
  const token = localStorage.getItem('financoop_token')
  const adminToken = localStorage.getItem('admin_token')
  const adminRol = localStorage.getItem('admin_rol')
  
  const isPublic = to.meta.public
  const requiresAuth = to.meta.requiresAuth
  const requiresAdmin = to.meta.requiresAdmin

  console.log('🛣️ Navegando a:', to.path, 'Token:', !!token, 'AdminToken:', !!adminToken)

  // 1. RUTAS DE ADMINISTRADOR
  if (requiresAdmin) {
    if (!adminToken || adminRol !== 'admin') {
      console.log('⛔ Requiere rol admin, redirigiendo a admin-login')
      next('/admin-login')
      return
    }
    next()
    return
  }

  // 2. RUTAS DE CLIENTE
  if (requiresAuth) {
    if (!token) {
      console.log('⛔ Requiere autenticación, redirigiendo a login')
      next('/login')
      return
    }
    next()
    return
  }

  // 3. RUTAS PÚBLICAS
  if (isPublic) {
    if (token && to.path !== '/login' && to.path !== '/registro' && to.path !== '/registro-exitoso') {
      console.log('🔓 Pública pero con token, redirigiendo a /inicio')
      next('/inicio')
      return
    }
    if (adminToken && to.path === '/admin-login') {
      console.log('🔓 Pública pero con admin token, redirigiendo a /usuarios')
      next('/usuarios')
      return
    }
    next()
    return
  }

  next()
})

export default router