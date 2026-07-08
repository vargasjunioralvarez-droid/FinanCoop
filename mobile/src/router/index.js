import { createRouter, createWebHistory } from 'vue-router'
import { useFinanCash } from '@/composables/useFinanCash'

// Lazy loading para mejor rendimiento
const LoginView = () => import('@/views/LoginView.vue')
const InicioView = () => import('@/views/InicioView.vue')
const CuotasView = () => import('@/views/CuotasView.vue')
const PagarView = () => import('@/views/PagarView.vue')
const ExplorarView = () => import('@/views/ExplorarView.vue')
const PerfilView = () => import('@/views/PerfilView.vue')

const routes = [
  {
    path: '/login',
    name: 'login',
    component: LoginView,
    meta: { public: true }
  },
  {
    path: '/',
    name: 'inicio',
    component: InicioView,
    meta: { requiresAuth: true, tab: 'inicio' }
  },
  {
    path: '/cuotas',
    name: 'cuotas',
    component: CuotasView,
    meta: { requiresAuth: true, tab: 'cuotas' }
  },
  {
    path: '/pagar',
    name: 'pagar',
    component: PagarView,
    meta: { requiresAuth: true, tab: 'pagar' }
  },
  {
    path: '/explorar',
    name: 'explorar',
    component: ExplorarView,
    meta: { requiresAuth: true, tab: 'explorar' }
  },
  {
    path: '/perfil',
    name: 'perfil',
    component: PerfilView,
    meta: { requiresAuth: true, tab: 'perfil' }
  },
  // Redirects
  {
    path: '/:pathMatch(.*)*',
    redirect: '/'
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes,
  scrollBehavior() {
    return { top: 0 }
  }
})

// Guard de navegación - protección de rutas
router.beforeEach((to, from, next) => {
  const { token } = useFinanCash()

  // Si no hay token y la ruta requiere auth → login
  if (to.meta.requiresAuth && !token.value) {
    next('/login')
    return
  }

  // Si hay token y va a login → inicio
  if (to.meta.public && token.value) {
    next('/')
    return
  }

  next()
})

export default router