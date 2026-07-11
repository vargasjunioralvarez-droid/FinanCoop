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
      component: Dashboard,
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
// ✅ GUARDIA DE NAVEGACIÓN (SIMPLIFICADA)
// ============================================================
router.beforeEach((to, from, next) => {
  const token = localStorage.getItem('financoop_token')
  const adminToken = localStorage.getItem('admin_token')
  const adminRol = localStorage.getItem('admin_rol')

  console.log('🛣️ Navegando a:', to.path)
  console.log('🔑 Token cliente:', !!token)
  console.log('🔑 Token admin:', !!adminToken)

  // Si es ruta pública → permitir
  if (to.meta.public) {
    // Si tiene token de admin, redirigir a usuarios
    if (adminToken && to.path === '/login') {
      next('/usuarios')
      return
    }
    // Si tiene token de cliente, redirigir a inicio
    if (token && to.path === '/login') {
      next('/inicio')
      return
    }
    next()
    return
  }

  // Si requiere admin
  if (to.meta.requiresAdmin) {
    if (!adminToken || adminRol !== 'admin') {
      next('/login')
      return
    }
    next()
    return
  }

  // Si requiere autenticación
  if (to.meta.requiresAuth) {
    if (!token) {
      next('/login')
      return
    }
    next()
    return
  }

  next()
})

export default router