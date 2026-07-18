<template>
  <v-app>
    <v-app-bar 
      v-if="mostrarNav"
      color="primary" 
      dark
      elevation="4"
      class="app-bar-gradient"
    >
      <v-app-bar-title class="font-weight-bold">
        <v-icon size="28" class="mr-2" color="white">mdi-wallet</v-icon>
        FinanCoop
      </v-app-bar-title>
      
      <v-spacer></v-spacer>
      
      <v-btn to="/inicio" variant="text" class="nav-btn mx-1"
        :class="{ 'nav-btn-active': $route.path === '/inicio' }">
        <v-icon start>mdi-view-dashboard</v-icon>
        Dashboard
      </v-btn>
      
      <v-btn to="/cajero" color="success" variant="elevated" class="nav-btn mx-1"
        :class="{ 'nav-btn-active': $route.path === '/cajero' }">
        <v-icon start>mdi-cart-plus</v-icon>
        Cajero
      </v-btn>
      
      <v-btn to="/clientes" variant="text" class="nav-btn mx-1"
        :class="{ 'nav-btn-active': $route.path === '/clientes' }">
        <v-icon start>mdi-account-group</v-icon>
        Clientes
      </v-btn>

      <v-btn to="/mis-ventas" variant="text" class="nav-btn mx-1"
        :class="{ 'nav-btn-active': $route.path === '/mis-ventas' }">
        <v-icon start>mdi-cart-check</v-icon>
        Mis Ventas
      </v-btn>
      
      <v-btn v-if="auth.esAdminOTienda" to="/financiamientos" variant="text" class="nav-btn mx-1"
        :class="{ 'nav-btn-active': $route.path === '/financiamientos' }">
        <v-icon start>mdi-file-document-multiple</v-icon>
        Financiamientos
      </v-btn>
      
      <v-btn v-if="auth.esAdminOTienda" to="/conciliacion" color="warning" variant="elevated" class="nav-btn mx-1"
        :class="{ 'nav-btn-active': $route.path === '/conciliacion' }">
        <v-icon start>mdi-cash-check</v-icon>
        Conciliación
      </v-btn>
      
      <v-menu v-if="auth.esAdmin">
        <template v-slot:activator="{ props }">
          <v-btn v-bind="props" color="info" variant="elevated" class="nav-btn mx-1">
            <v-icon start>mdi-cog</v-icon>
            Admin
            <v-icon end size="14">mdi-chevron-down</v-icon>
          </v-btn>
        </template>
        <v-list elevation="4" rounded="lg">
          <v-list-item to="/tiendas">
            <template v-slot:prepend><v-icon color="green">mdi-store</v-icon></template>
            <v-list-item-title>Tiendas</v-list-item-title>
          </v-list-item>
          <v-list-item to="/usuarios">
            <template v-slot:prepend><v-icon color="error">mdi-shield-account</v-icon></template>
            <v-list-item-title>Usuarios</v-list-item-title>
          </v-list-item>
          <v-divider></v-divider>
          <v-list-item to="/configuracion">
            <template v-slot:prepend><v-icon color="primary">mdi-currency-usd</v-icon></template>
            <v-list-item-title>Tasa del Dólar</v-list-item-title>
          </v-list-item>
          <v-list-item to="/niveles">
            <template v-slot:prepend><v-icon color="amber">mdi-trophy</v-icon></template>
            <v-list-item-title>Niveles</v-list-item-title>
          </v-list-item>
        </v-list>
      </v-menu>
      
      <v-chip v-if="auth.tiendaNombre" class="ml-2" color="green-darken-1" variant="tonal" size="small" prepend-icon="mdi-store">
        {{ auth.tiendaNombre }}
      </v-chip>
      
      <v-chip class="ml-2" color="white" variant="outlined" size="small" prepend-icon="mdi-currency-usd">
        {{ auth.tasaActual }} BS/$
      </v-chip>
      
      <!-- Indicador de refresco automático -->
      <v-tooltip text="Refresco automático cada 30s">
        <template v-slot:activator="{ props }">
          <v-icon v-bind="props" size="14" class="ml-1" color="green-lighten-2">mdi-sync</v-icon>
        </template>
      </v-tooltip>
      
      <v-btn icon="mdi-logout" size="small" class="ml-2" @click="auth.logout()" title="Cerrar sesión"></v-btn>
    </v-app-bar>
    
    <v-main>
      <v-container fluid class="pa-6">
        <router-view :key="$route.fullPath"></router-view>
      </v-container>
    </v-main>
  </v-app>
</template>

<script setup>
import { computed, onMounted, onUnmounted, watch } from 'vue'
import { useRoute } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const route = useRoute()
const auth = useAuthStore()
const mostrarNav = computed(() => route.path !== '/login')

// ============================================================
// 🔄 POLLING INTELIGENTE - Refresco automático sin saturar
// ============================================================
let pollTimer = null
let visibilityTimer = null
const POLL_INTERVAL = 30000  // 30 segundos

const startPolling = () => {
  // Solo si hay sesión activa
  if (!auth.token) return
  
  // Limpiar timer anterior
  stopPolling()
  
  // Iniciar nuevo polling
  pollTimer = setInterval(() => {
    // Solo refrescar si la pestaña está visible (no satura cuando está en segundo plano)
    if (document.visibilityState === 'visible') {
      auth.cargarUsuario()
      auth.cargarTasa()
    }
  }, POLL_INTERVAL)
}

const stopPolling = () => {
  if (pollTimer) {
    clearInterval(pollTimer)
    pollTimer = null
  }
}

// Detectar cuando el usuario cambia de pestaña
const handleVisibilityChange = () => {
  if (document.visibilityState === 'visible') {
    // Al volver a la pestaña, refrescar inmediatamente
    auth.cargarUsuario()
    auth.cargarTasa()
    startPolling()
  } else {
    // Al minimizar, detener polling para no saturar
    stopPolling()
  }
}

// Iniciar/detener polling cuando cambia el token (login/logout)
watch(() => auth.token, (newToken) => {
  if (newToken) {
    startPolling()
  } else {
    stopPolling()
  }
})

onMounted(() => {
  auth.cargarTasa()
  auth.cargarUsuario()
  
  // Iniciar polling si hay sesión
  startPolling()
  
  // Detectar visibilidad de la pestaña
  document.addEventListener('visibilitychange', handleVisibilityChange)
})

onUnmounted(() => {
  stopPolling()
  document.removeEventListener('visibilitychange', handleVisibilityChange)
})
</script>

<style scoped>
.app-bar-gradient { background: linear-gradient(135deg, #1565c0 0%, #0d47a1 100%) !important; }
.nav-btn { text-transform: none; letter-spacing: 0.5px; font-weight: 500; border-radius: 10px; padding: 0 16px !important; height: 40px; transition: all 0.3s ease; }
.nav-btn:hover { transform: translateY(-2px); box-shadow: 0 4px 12px rgba(0,0,0,0.2); }
.nav-btn-active { background: rgba(255,255,255,0.15) !important; font-weight: 600; }
</style>