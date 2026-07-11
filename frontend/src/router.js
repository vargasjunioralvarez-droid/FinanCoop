import { createRouter, createWebHistory } from 'vue-router'
import Dashboard from './views/Dashboard.vue'
import CajeroView from './views/CajeroView.vue'
import Clientes from './views/Clientes.vue'
import Financiamientos from './views/Financiamientos.vue'
import Cuotas from './views/Cuotas.vue'
import ConciliacionView from './views/ConciliacionView.vue'
import ConfiguracionView from './views/ConfiguracionView.vue'
import NivelesView from './views/NivelesView.vue'

// ============================================================
// ✅ NUEVAS VISTAS PARA ADMINISTRACIÓN
// ============================================================
import AdminLoginView from './views/AdminLogin.vue'
import UsuariosView from './views/UsuariosView.vue'
import ClientesAdminView from './views/ClientesAdmin.vue'  // Vista con editar/eliminar

// ============================================================
// ✅ FUNCIÓN PARA VERIFICAR SI ES ADMIN
// ============================================================
const isAdmin = () => {
  const token = localStorage.getItem('admin_token')
  const rol = localStorage.getItem('admin_rol')
  return token && rol === 'admin'
}

const routes = [
  // ============================================================
  // 🔓 RUTAS PÚBLICAS
  // ============================================================
  { 
    path: '/admin-login', 
    component: AdminLoginView,
    meta: { public: true }
  },

  // ============================================================
  // 🔒 RUTAS PROTEGIDAS (requieren token de cliente)
  // ============================================================
  { 
    path: '/', 
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

// ============================================================
// ✅ GUARDIA DE NAVEGACIÓN
// ============================================================
const router = createRouter({
  history: createWebHistory(),
  routes
})

router.beforeEach((to, from, next) => {
  const token = localStorage.getItem('financoop_token')
  const isPublic = to.meta.public
  const requiresAuth = to.meta.requiresAuth
  const requiresAdmin = to.meta.requiresAdmin

  console.log('🛣️ Navegando a:', to.path, 'Token:', !!token)

  // 1. Si requiere autenticación y no hay token → redirigir a login
  if (requiresAuth && !token) {
    console.log('⛔ Requiere autenticación, redirigiendo a login')
    next('/admin-login')
    return
  }

  // 2. Si requiere admin y no es admin → redirigir a admin-login
  if (requiresAdmin && !isAdmin()) {
    console.log('⛔ Requiere rol admin, redirigiendo a admin-login')
    next('/admin-login')
    return
  }

  // 3. Si es pública y hay token → redirigir a dashboard
  if (isPublic && token && to.path !== '/admin-login') {
    console.log('🔓 Pública pero con token, redirigiendo a /')
    next('/')
    return
  }

  // 4. Todo bien → continuar
  next()
})

export default router