import { createRouter, createWebHistory } from 'vue-router'
import { useFinanCash } from '@/composables/useFinanCash'

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
      redirect: '/inicio'  // ✅ Redirige / a /inicio
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

// ✅ Guardia de navegación
router.beforeEach((to, from, next) => {
  const { token } = useFinanCash()
  const isPublic = to.meta.public
  const requiresAuth = to.meta.requiresAuth

  console.log('🛣️ Navegando a:', to.path, 'Token:', !!token.value)

  if (requiresAuth && !token.value) {
    console.log('⛔ Requiere autenticación, redirigiendo a login')
    next('/login')
  } else if (isPublic && token.value && to.path !== '/registro-exitoso') {
    console.log('🔓 Pública pero con token, redirigiendo a /inicio')
    next('/inicio')
  } else {
    next()
  }
})

export default router