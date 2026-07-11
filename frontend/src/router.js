// frontend/src/router.js
import { createRouter, createWebHistory } from 'vue-router'

// ✅ IMPORTAR VISTAS (SOLO LAS QUE EXISTEN)
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

// ✅ NOTA: NO hay InicioView.vue, se usa Dashboard

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    // ============================================================
    // 🔓 RUTAS PÚBLICAS
    // ============================================================
    {
      path: '/',
      redirect: '/login'
    },
    {
      path: '/login',
      component: AdminLoginView,
      meta: { public: true }
    },

    // ============================================================
    // 🔒 RUTAS DE CLIENTE
    // ============================================================
    {
      path: '/inicio',
      component: Dashboard,  // ✅ Usa Dashboard en lugar de InicioView
      meta: { requiresAuth: true }
    },
    {
      path: '/cajero',
      component: CajeroView,
      meta: { requiresAuth: true }
    },
    {
      path: '/clientes',
      component: Clientes,
      meta: { requiresAuth: true }
    },
    {
      path: '/financiamientos',
      component: Financiamientos,
      meta: { requiresAuth: true }
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
      meta: { requiresAuth: true }
    },
    {
      path: '/configuracion',
      component: ConfiguracionView,
      meta: { requiresAuth: true }
    },
    {
      path: '/niveles',
      component: NivelesView,
      meta: { requiresAuth: true }
    },

    // ============================================================
    // 👑 RUTAS DE ADMIN
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

  console.log('🛣️ Navegando a:', to.path)
  console.log('🔑 Token cliente:', !!token)
  console.log('🔑 Token admin:', !!adminToken)

  // 1. RUTAS DE ADMINISTRADOR
  if (requiresAdmin) {
    if (!adminToken || adminRol !== 'admin') {
      console.log('⛔ Requiere rol admin, redirigiendo a login')
      next('/login')
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
    // Si tiene token de cliente, redirigir a inicio
    if (token) {
      console.log('🔓 Pública pero con token, redirigiendo a /inicio')
      next('/inicio')
      return
    }
    // Si tiene token de admin, redirigir a usuarios
    if (adminToken) {
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