// mobile/src/router/index.js
import { createRouter, createWebHistory } from 'vue-router'

// Importar vistas
import InicioView from '@/views/InicioView.vue'
import CuotasView from '@/views/CuotasView.vue'
import PagarView from '@/views/PagarView.vue'
import ExplorarView from '@/views/ExplorarView.vue'
import PerfilView from '@/views/PerfilView.vue'
import LoginView from '@/views/LoginView.vue'

// Importar registro
import RegisterView from '@/views/RegisterView.vue'
import RegisterSuccessView from '@/views/RegisterSuccessView.vue'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    // 🔓 Rutas públicas
    {
      path: '/login',
      name: 'Login',
      component: LoginView,
      meta: { public: true }
    },
    {
      path: '/registro',
      name: 'Register',
      component: RegisterView,
      meta: { public: true }
    },
    {
      path: '/registro-exitoso/:cedula?',
      name: 'RegisterSuccess',
      component: RegisterSuccessView,
      meta: { public: true }
    },
    
    // 🔒 Rutas protegidas
    {
      path: '/',
      redirect: '/inicio'
    },
    {
      path: '/inicio',
      name: 'Inicio',
      component: InicioView,
      meta: { tab: 'inicio', requiresAuth: true }
    },
    {
      path: '/cuotas',
      name: 'Cuotas',
      component: CuotasView,
      meta: { tab: 'cuotas', requiresAuth: true }
    },
    {
      path: '/pagar',
      name: 'Pagar',
      component: PagarView,
      meta: { tab: 'pagar', requiresAuth: true }
    },
    {
      path: '/explorar',
      name: 'Explorar',
      component: ExplorarView,
      meta: { tab: 'explorar', requiresAuth: true }
    },
    {
      path: '/perfil',
      name: 'Perfil',
      component: PerfilView,
      meta: { tab: 'perfil', requiresAuth: true }
    }
  ]
})

// ✅ Guardia de navegación - CORREGIDA
router.beforeEach((to, from, next) => {
  // 🔥 USAR localStorage DIRECTAMENTE (no useFinanCash)
  const token = localStorage.getItem('financoop_token')
  const isPublic = to.meta.public
  const requiresAuth = to.meta.requiresAuth

  console.log('🛣️ Navegando a:', to.path, 'Token:', !!token)

  // 1. Si la ruta requiere autenticación y no hay token
  if (requiresAuth && !token) {
    console.log('⛔ Requiere autenticación, redirigiendo a login')
    next('/login')
    return
  }

  // 2. Si la ruta es pública y hay token (excepto registro-exitoso)
  if (isPublic && token && to.path !== '/registro-exitoso') {
    console.log('🔓 Pública pero con token, redirigiendo a /inicio')
    next('/inicio')
    return
  }

  // 3. Si la ruta es pública y NO hay token (login, registro, etc.)
  // o si la ruta está protegida y hay token
  next()
})

export default router