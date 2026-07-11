// frontend/src/router.js
import { createRouter, createWebHistory } from 'vue-router'

// Importar vistas
import Dashboard from '@/views/Dashboard.vue'
import CajeroView from '@/views/CajeroView.vue'
import Clientes from '@/views/Clientes.vue'
import Financiamientos from '@/views/Financiamientos.vue'
import Cuotas from '@/views/Cuotas.vue'
import ConciliacionView from '@/views/ConciliacionView.vue'
import ConfiguracionView from '@/views/ConfiguracionView.vue'
import NivelesView from '@/views/NivelesView.vue'
import AdminLoginView from '@/views/AdminLogin.vue'
import UsuariosView from '@/views/UsuariosView.vue'

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
    // 🔒 RUTAS PARA TODOS LOS AUTENTICADOS (admin, cajero, usuario)
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

    // ============================================================
    // 👑 RUTAS SOLO PARA ADMINISTRADOR
    // ============================================================
    {
      path: '/usuarios',
      component: UsuariosView,
      meta: { requiresAuth: true, requiresAdmin: true }
    },
    {
      path: '/configuracion',
      component: ConfiguracionView,
      meta: { requiresAuth: true, requiresAdmin: true }
    },
    {
      path: '/niveles',
      component: NivelesView,
      meta: { requiresAuth: true, requiresAdmin: true }
    }
  ]
})

// ============================================================
// ✅ GUARDIA DE NAVEGACIÓN CON ROLES
// ============================================================
router.beforeEach((to, from, next) => {
  const token = localStorage.getItem('admin_token')
  const rol = localStorage.getItem('admin_rol')

  const isPublic = to.meta.public
  const requiresAuth = to.meta.requiresAuth
  const requiresAdmin = to.meta.requiresAdmin

  // 1. RUTAS PÚBLICAS (login)
  if (isPublic) {
    if (token) {
      // Ya está logueado, redirigir según rol
      next(rol === 'admin' ? '/usuarios' : '/inicio')
      return
    }
    next()
    return
  }

  // 2. REQUIERE AUTENTICACIÓN
  if (!token) {
    next('/login')
    return
  }

  // 3. REQUIERE SER ADMIN
  if (requiresAdmin && rol !== 'admin') {
    alert('⛔ No tienes permisos para acceder a esta sección')
    next('/inicio')
    return
  }

  next()
})

export default router