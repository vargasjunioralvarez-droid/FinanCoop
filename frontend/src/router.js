// frontend/src/router.js
import { createRouter, createWebHistory } from 'vue-router'

// ✅ IMPORTAR VISTAS
import Dashboard from '@/views/Dashboard.vue'
import CajeroView from '@/views/CajeroView.vue'
import Clientes from '@/views/Clientes.vue'
import Financiamientos from '@/views/Financiamientos.vue'
import Cuotas from '@/views/Cuotas.vue'
import ConciliacionView from '@/views/ConciliacionView.vue'
import ConfiguracionView from '@/views/ConfiguracionView.vue'
import NivelesView from '@/views/NivelesView.vue'

// ✅ IMPORTAR VISTAS DE ADMIN
import AdminLoginView from '@/views/AdminLogin.vue'
import UsuariosView from '@/views/UsuariosView.vue'
import ClientesAdminView from '@/views/ClientesAdmin.vue'

// ✅ IMPORTAR LoginView
import LoginView from '@/views/LoginView.vue'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    // ============================================================
    // 🔓 RUTAS PÚBLICAS
    // ============================================================
    {
      path: '/login',
      component: LoginView,
      meta: { public: true }
    },
    {
      path: '/admin-login',
      component: AdminLoginView,
      meta: { public: true }
    },

    // ============================================================
    // 🏠 REDIRECCIÓN
    // ============================================================
    {
      path: '/',
      redirect: '/inicio'
    },

    // ============================================================
    // 🔒 RUTAS DE CLIENTE
    // ============================================================
    {
      path: '/inicio',
      component: Dashboard,
      meta: { requiresAuth: true, tab: 'inicio' }
    },
    {
      path: '/cajero',
      component: CajeroView,
      meta: { requiresAuth: true, tab: 'cajero' }
    },
    {
      path: '/clientes',
      component: Clientes,
      meta: { requiresAuth: true, tab: 'clientes' }
    },
    {
      path: '/financiamientos',
      component: Financiamientos,
      meta: { requiresAuth: true, tab: 'financiamientos' }
    },
    {
      path: '/cuotas/:id',
      component: Cuotas,
      props: true,
      meta: { requiresAuth: true }
    },
    {
      path: '/conciliacion',
      component: ConciliacionView,
      meta: { requiresAuth: true, tab: 'conciliacion' }
    },
    {
      path: '/configuracion',
      component: ConfiguracionView,
      meta: { requiresAuth: true, tab: 'configuracion' }
    },
    {
      path: '/niveles',
      component: NivelesView,
      meta: { requiresAuth: true, tab: 'niveles' }
    },

    // ============================================================
    // 👑 RUTAS DE ADMINISTRADOR
    // ============================================================
    {
      path: '/usuarios',
      component: UsuariosView,
      meta: { requiresAdmin: true }
    },
    {
      path: '/clientes-admin',
      component: ClientesAdminView,
      meta: { requiresAdmin: true }
    }
  ]
})

// ============================================================
// ✅ GUARDIA DE NAVEGACIÓN
// ============================================================
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
    if (token && to.path !== '/login') {
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