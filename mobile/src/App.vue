<template>
  <v-app :theme="tema" class="mobile-app">
    <!-- Toast de inactividad -->
    <v-snackbar
      v-model="mostrarMensajeInactividad"
      color="warning"
      timeout="3000"
      location="top"
      variant="tonal"
    >
      <v-icon start color="warning">mdi-clock-alert</v-icon>
      {{ mensajeInactividad }}
    </v-snackbar>

    <!-- REGISTRO (sin layout) -->
    <router-view v-if="route.path === '/registro' || route.path === '/registro-exitoso'" />

    <!-- LOGIN (sin layout) cuando NO hay token o la ruta es login -->
    <router-view v-else-if="route.path === '/login' || !token" />

    <!-- DASHBOARD CON ROUTER -->
    <div v-else class="app-content">
      <!-- Header flotante -->
      <div class="app-header" :class="{ 'header-scrolled': scrolled }">
        <div class="d-flex align-center justify-space-between px-4 py-2">
          <div class="d-flex align-center">
            <v-img
              src="/icons/icon-192x192.png"
              width="32"
              height="32"
              class="mr-2"
              contain
            />
            <span class="text-subtitle-1 font-weight-bold">FinanCoop</span>
          </div>
          <div class="d-flex gap-2">
            <v-btn
              :icon="tema === 'dark' ? 'mdi-weather-sunny' : 'mdi-weather-night'"
              variant="text"
              size="small"
              density="comfortable"
              @click="toggleTema"
            />
            <v-btn
              icon="mdi-help-circle"
              variant="text"
              size="small"
              density="comfortable"
              color="info"
              @click="mostrarAyuda = true"
            />
          </div>
        </div>
      </div>

      <!-- Modal de Ayuda -->
      <v-dialog v-model="mostrarAyuda" max-width="480" scrollable>
        <v-card>
          <v-card-title class="py-4 d-flex align-center" :class="tema === 'dark' ? 'bg-surface-variant' : 'bg-primary'">
            <v-icon start class="mr-2">mdi-information</v-icon>
            <span>¿Qué es FinanCoop?</span>
          </v-card-title>

          <v-card-text class="pa-4">
            <div class="seccion mb-4">
              <h3 class="text-subtitle-1 font-weight-bold mb-2">
                <v-icon start color="primary">mdi-wallet</v-icon>
                ¿Qué es?
              </h3>
              <p class="text-body-2 text-medium-emphasis">
                FinanCoop es el sistema de financiamiento de Cecosesola. 
                Tu deuda se mantiene en dólares, pero pagas en bolívares al tipo de cambio del día.
              </p>
            </div>

            <v-divider class="my-3"></v-divider>

            <div class="seccion mb-4">
              <h3 class="text-subtitle-1 font-weight-bold mb-2">
                <v-icon start color="amber-darken-2">mdi-trophy</v-icon>
                Tu Nivel de Confianza
              </h3>
              <p class="text-caption text-medium-emphasis mb-2">
                Cada compra que completas aumenta tu score y sube de nivel.
                <strong>Las cuotas no se rebajan</strong>, pero desbloqueas mejores condiciones:
              </p>

              <v-list density="compact" class="pa-0 bg-transparent">
                <v-list-item v-for="(config, key) in nivelesConfig" :key="key" class="px-0 py-2">
                  <template v-slot:prepend>
                    <v-icon :color="colorNivel(key)" size="22">{{ iconoNivel(key) }}</v-icon>
                  </template>
                  <v-list-item-title class="text-body-2 font-weight-medium text-capitalize">
                    {{ key }}
                  </v-list-item-title>
                  <v-list-item-subtitle class="text-caption">
                    Hasta ${{ config.monto_max_usd }} | {{ config.entrada_pct }}% entrada | {{ config.cuotas_max }} cuotas
                  </v-list-item-subtitle>
                </v-list-item>
              </v-list>
            </div>

            <v-divider class="my-3"></v-divider>

            <div class="seccion mb-4">
              <h3 class="text-subtitle-1 font-weight-bold mb-2">
                <v-icon start color="error">mdi-alert-circle</v-icon>
                Importante
              </h3>
              <ul class="text-body-2 text-medium-emphasis lista">
                <li>La deuda se mantiene en USD, pagas en Bs al tipo de cambio del día</li>
                <li>Mora diaria según tu nivel si excedes los días de gracia</li>
                <li>Si tienes cuotas vencidas, no puedes comprar más</li>
                <li>Las cuotas no se rebajan, siempre pagas lo que corresponde</li>
              </ul>
            </div>

            <v-divider class="my-3"></v-divider>

            <div class="seccion">
              <h3 class="text-subtitle-1 font-weight-bold mb-2">
                <v-icon start color="success">mdi-cash-check</v-icon>
                Paga fácil
              </h3>
              <p class="text-body-2 text-medium-emphasis">
                Reporta tu pago por Pago Móvil, Transferencia, Zelle o Binance. 
                El establecimiento lo confirma y listo.
              </p>
            </div>
          </v-card-text>

          <v-card-actions class="pa-4">
            <v-btn color="primary" block rounded="pill" @click="mostrarAyuda = false">
              <v-icon start>mdi-check</v-icon>
              Entendido
            </v-btn>
          </v-card-actions>
        </v-card>
      </v-dialog>

      <!-- Bottom Navigation -->
      <v-bottom-navigation
        :model-value="activeTab"
        grow
        color="primary"
        elevation="8"
        class="bottom-nav"
        mode="shift"
      >
        <v-btn value="inicio" :active="activeTab === 'inicio'" @click="navigateTo('inicio')">
          <v-icon>mdi-home</v-icon>
          <span>Inicio</span>
        </v-btn>

        <v-btn value="cuotas" :active="activeTab === 'cuotas'" @click="navigateTo('cuotas')">
          <template v-if="badgeCount > 0">
            <v-badge :content="badgeCount" color="error" offset-x="-10" offset-y="6">
              <v-icon>mdi-calendar-clock</v-icon>
            </v-badge>
          </template>
          <template v-else>
            <v-icon>mdi-calendar-clock</v-icon>
          </template>
          <span>Cuotas</span>
        </v-btn>

        <v-btn value="pagar" :active="activeTab === 'pagar'" class="pagar-btn" @click="navigateTo('pagar')">
          <div class="pagar-icon-wrapper">
            <v-icon size="28">mdi-credit-card</v-icon>
          </div>
          <span>Pagar</span>
        </v-btn>

        <v-btn value="explorar" :active="activeTab === 'explorar'" @click="navigateTo('explorar')">
          <v-icon>mdi-store-search</v-icon>
          <span>Explorar</span>
        </v-btn>

        <v-btn value="perfil" :active="activeTab === 'perfil'" @click="navigateTo('perfil')">
          <v-icon>mdi-account</v-icon>
          <span>Perfil</span>
        </v-btn>
      </v-bottom-navigation>

      <!-- Contenido -->
      <v-main class="pb-16 pt-14">
        <router-view v-slot="{ Component }">
          <transition name="slide-fade" mode="out-in">
            <component :is="Component" />
          </transition>
        </router-view>
      </v-main>
    </div>
  </v-app>
</template>

<script setup>
import { ref, onMounted, computed, watch, onBeforeUnmount } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useFinanCash } from '@/composables/useFinanCash'

const { 
  token, 
  nivelesConfig,
  badgeCount,
  cargarDatos,
  colorNivel,
  iconoNivel,
  cerrarSesion,
  resetInactivityTimer
} = useFinanCash()

const route = useRoute()
const router = useRouter()

const mostrarAyuda = ref(false)
const tema = ref(localStorage.getItem('financoop_theme') || 'light')
const scrolled = ref(false)

// ✅ FIX: Flag para evitar redirección múltiple
const redirigiendo = ref(false)

// ============ MENSAJE DE INACTIVIDAD ============
const mostrarMensajeInactividad = ref(false)
const mensajeInactividad = ref('')

const handleInactividad = (event) => {
  mensajeInactividad.value = event.detail?.mensaje || 'Sesión cerrada por inactividad'
  mostrarMensajeInactividad.value = true
}

// ============ COMPUTED ============
const activeTab = computed(() => {
  return route.meta?.tab || route.name?.toLowerCase() || 'inicio'
})

// ============ NAVEGACIÓN ============
const navigateTo = (tab) => {
  const routes = {
    inicio: '/inicio',
    cuotas: '/cuotas',
    pagar: '/pagar',
    explorar: '/explorar',
    perfil: '/perfil'
  }
  router.push(routes[tab])
}

// ============ TEMAS ============
const toggleTema = () => {
  tema.value = tema.value === 'light' ? 'dark' : 'light'
  localStorage.setItem('financoop_theme', tema.value)
}

// ============ SCROLL ============
const onScroll = () => {
  scrolled.value = window.scrollY > 10
}

// ============ INICIALIZAR APP ============
const iniciarApp = async () => {
  console.log('📱 Iniciando app...')

  const tokenGuardado = localStorage.getItem('financoop_token')

  if (tokenGuardado && !token.value) {
    token.value = tokenGuardado
  }

  if (token.value) {
    console.log('🔄 Token presente, cargando datos...')
    try {
      await cargarDatos()
      console.log('✅ Datos cargados correctamente')
      if (resetInactivityTimer) {
        resetInactivityTimer()
      }
    } catch (error) {
      console.error('❌ Error cargando datos:', error)
      localStorage.removeItem('financoop_token')
      token.value = null
      // ✅ FIX: Solo redirigir si no estamos ya en una ruta pública
      if (!['/login', '/registro', '/registro-exitoso'].includes(route.path) && !redirigiendo.value) {
        redirigiendo.value = true
        await router.push('/login')
        redirigiendo.value = false
      }
    }
  } else {
    console.log('❌ No hay token')
    if (!['/login', '/registro', '/registro-exitoso'].includes(route.path) && !redirigiendo.value) {
      redirigiendo.value = true
      await router.push('/login')
      redirigiendo.value = false
    }
  }
}

// ============ WATCHERS ============
// ✅ FIX: watch con flag de protección contra bucles
watch(token, (newToken, oldToken) => {
  console.log('🔄 Token cambiado:', newToken ? 'Token presente' : 'Sin token')

  // Solo redirigir si el token pasó de tener valor a null (logout)
  // NO redirigir en el inicial (oldToken es undefined al inicio)
  if (!newToken && oldToken !== undefined && !redirigiendo.value) {
    if (!['/login', '/registro', '/registro-exitoso'].includes(route.path)) {
      redirigiendo.value = true
      router.push('/login').finally(() => {
        redirigiendo.value = false
      })
    }
  }
})

// ============ CICLO DE VIDA ============
onMounted(async () => {
  console.log('📱 App montada')
  window.addEventListener('inactividad', handleInactividad)
  window.addEventListener('scroll', onScroll)
  await iniciarApp()
})

onBeforeUnmount(() => {
  window.removeEventListener('inactividad', handleInactividad)
  window.removeEventListener('scroll', onScroll)
})
</script>

<style scoped>
.mobile-app {
  min-height: 100vh;
}

.app-content {
  padding-bottom: 80px;
  position: relative;
}

.app-header {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  z-index: 1000;
  background: transparent;
  transition: all 0.3s ease;
}

.app-header.header-scrolled {
  background: rgb(var(--v-theme-surface));
  box-shadow: 0 2px 8px rgba(0,0,0,0.08);
  backdrop-filter: blur(10px);
}

.bottom-nav {
  position: fixed;
  bottom: 0;
  left: 0;
  right: 0;
  z-index: 100;
  border-radius: 20px 20px 0 0;
  box-shadow: 0 -4px 20px rgba(0,0,0,0.1);
  padding-bottom: env(safe-area-inset-bottom, 0);
}

.pagar-btn {
  position: relative;
}

.pagar-icon-wrapper {
  background: linear-gradient(135deg, #1976d2, #1565c0);
  border-radius: 50%;
  width: 48px;
  height: 48px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  margin-top: -24px;
  box-shadow: 0 4px 12px rgba(25, 118, 210, 0.4);
  border: 3px solid rgb(var(--v-theme-surface));
}

@supports (padding-bottom: env(safe-area-inset-bottom)) {
  .bottom-nav {
    padding-bottom: env(safe-area-inset-bottom);
  }
  .app-content {
    padding-bottom: calc(80px + env(safe-area-inset-bottom));
  }
}

::-webkit-scrollbar {
  display: none;
}

.v-btn:active {
  transform: scale(0.96);
  transition: transform 0.15s ease;
}

.slide-fade-enter-active {
  transition: all 0.3s ease;
}
.slide-fade-leave-active {
  transition: all 0.2s ease;
}
.slide-fade-enter-from {
  opacity: 0;
  transform: translateX(20px);
}
.slide-fade-leave-to {
  opacity: 0;
  transform: translateX(-20px);
}

.seccion {
  padding: 0 4px;
}

.lista {
  padding-left: 16px;
  margin: 0;
}

.lista li {
  margin-bottom: 6px;
}

.gap-2 {
  gap: 8px;
}
</style>