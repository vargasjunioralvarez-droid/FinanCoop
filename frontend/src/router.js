// frontend/src/router.js
import { createRouter, createWebHistory } from 'vue-router'

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
import AdminTiendas from '@/views/AdminTiendas.vue'
import MisVentas from '@/views/MisVentas.vue'
import AuditoriaView from '@/views/AuditoriaView.vue'
import BackupView from '@/views/BackupView.vue'


const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    // 🔓 PÚBLICAS
    { path: '/', redirect: '/login' },
    { path: '/login', component: AdminLoginView, meta: { public: true } },

    // 🔒 TODOS LOS AUTENTICADOS (cajero, admin_tienda, admin_central)
    { path: '/inicio', component: Dashboard, meta: { requiresAuth: true } },
    { path: '/cajero', component: CajeroView, meta: { requiresAuth: true } },
    { path: '/clientes', component: Clientes, meta: { requiresAuth: true } },
    { path: '/mis-ventas', component: MisVentas, meta: { requiresAuth: true } },

    // 🔒 ADMIN TIENDA + ADMIN CENTRAL
    { path: '/financiamientos', component: Financiamientos, meta: { requiresAuth: true, requiresAdminTienda: true } },
    { path: '/cuotas/:id', component: Cuotas, props: true, meta: { requiresAuth: true, requiresAdminTienda: true } },
    { path: '/conciliacion', component: ConciliacionView, meta: { requiresAuth: true, requiresAdminTienda: true } },

    // 👑 SOLO ADMIN CENTRAL
    { path: '/usuarios', component: UsuariosView, meta: { requiresAuth: true, requiresAdmin: true } },
    { path: '/tiendas', component: AdminTiendas, meta: { requiresAuth: true, requiresAdmin: true } },
    { path: '/configuracion', component: ConfiguracionView, meta: { requiresAuth: true, requiresAdmin: true } },
    { path: '/niveles', component: NivelesView, meta: { requiresAuth: true, requiresAdmin: true } },
    { path: '/auditoria', component: AuditoriaView, meta: { requiresAuth: true, requiresAdmin: true } },
    { path: '/backup', component: BackupView, meta: { requiresAuth: true, requiresAdmin: true } },

  ]
})

router.beforeEach((to, from, next) => {
  const token = localStorage.getItem('admin_token')
  const rol = localStorage.getItem('admin_rol')

  // Público
  if (to.meta.public) {
    if (token) {
      if (rol === 'admin_central') next('/usuarios')
      else if (rol === 'admin_tienda') next('/inicio')
      else next('/cajero')
      return
    }
    next()
    return
  }

  // Autenticación
  if (!token) {
    next('/login')
    return
  }

  // Solo admin_central
  if (to.meta.requiresAdmin && rol !== 'admin_central') {
    next('/inicio')
    return
  }

  // Solo admin_tienda o admin_central
  if (to.meta.requiresAdminTienda && rol === 'cajero') {
    next('/mis-ventas')
    return
  }

  next()
})

export default router