<template>
  <v-app class="app-premium">
    <v-app-bar 
      v-if="mostrarNav"
      dark
      elevation="0"
      class="app-bar-premium"
    >
      <v-app-bar-title class="font-weight-bold">
        <div class="d-flex align-center">
          <div class="logo-icon-small">
            <v-icon size="22" color="white">mdi-wallet</v-icon>
          </div>
          <span class="ml-2 logo-text">FinanCoop</span>
        </div>
      </v-app-bar-title>
      
      <v-spacer></v-spacer>
      
      <v-btn to="/inicio" variant="text" class="nav-btn mx-1" :class="{ 'nav-btn-active': $route.path === '/inicio' }">
        <v-icon start size="18">mdi-view-dashboard</v-icon>
        <span class="nav-text">Dashboard</span>
      </v-btn>
      
      <v-btn to="/cajero" variant="text" class="nav-btn mx-1 nav-btn-success" :class="{ 'nav-btn-active': $route.path === '/cajero' }">
        <v-icon start size="18">mdi-cart-plus</v-icon>
        <span class="nav-text">Cajero</span>
      </v-btn>
      
      <v-btn to="/clientes" variant="text" class="nav-btn mx-1" :class="{ 'nav-btn-active': $route.path === '/clientes' }">
        <v-icon start size="18">mdi-account-group</v-icon>
        <span class="nav-text">Clientes</span>
      </v-btn>

      <v-btn to="/mis-ventas" variant="text" class="nav-btn mx-1" :class="{ 'nav-btn-active': $route.path === '/mis-ventas' }">
        <v-icon start size="18">mdi-cart-check</v-icon>
        <span class="nav-text">Mis Ventas</span>
      </v-btn>
      
      <v-btn v-if="auth.esAdminOTienda" to="/financiamientos" variant="text" class="nav-btn mx-1" :class="{ 'nav-btn-active': $route.path === '/financiamientos' }">
        <v-icon start size="18">mdi-file-document-multiple</v-icon>
        <span class="nav-text">Financiamientos</span>
      </v-btn>
      
      <v-btn v-if="auth.esAdminOTienda" to="/conciliacion" variant="text" class="nav-btn mx-1 nav-btn-warning" :class="{ 'nav-btn-active': $route.path === '/conciliacion' }">
        <v-icon start size="18">mdi-cash-check</v-icon>
        <span class="nav-text">Conciliación</span>
      </v-btn>
      
      <v-menu v-if="auth.esAdmin">
        <template v-slot:activator="{ props }">
          <v-btn v-bind="props" variant="text" class="nav-btn mx-1 nav-btn-info" :class="{ 'nav-btn-active': $route.path.includes('/config') || $route.path.includes('/niveles') || $route.path.includes('/tiendas') || $route.path.includes('/usuarios') }">
            <v-icon start size="18">mdi-cog</v-icon>
            <span class="nav-text">Admin</span>
            <v-icon end size="14">mdi-chevron-down</v-icon>
          </v-btn>
        </template>
        <v-list class="glass-card-menu" elevation="0" rounded="lg">
  <v-list-item to="/tiendas" class="menu-item">
    <template v-slot:prepend><v-icon color="#4caf50" size="20">mdi-store</v-icon></template>
    <v-list-item-title class="text-white">Tiendas</v-list-item-title>
  </v-list-item>
  <v-list-item to="/usuarios" class="menu-item">
    <template v-slot:prepend><v-icon color="#f44336" size="20">mdi-shield-account</v-icon></template>
    <v-list-item-title class="text-white">Usuarios</v-list-item-title>
  </v-list-item>
  <v-divider style="border-color: rgba(255,255,255,0.06);" />
  <v-list-item to="/configuracion" class="menu-item">
    <template v-slot:prepend><v-icon color="#4facfe" size="20">mdi-currency-usd</v-icon></template>
    <v-list-item-title class="text-white">Tasa del Dólar</v-list-item-title>
  </v-list-item>
  <v-list-item to="/niveles" class="menu-item">
    <template v-slot:prepend><v-icon color="#ffd54f" size="20">mdi-trophy</v-icon></template>
    <v-list-item-title class="text-white">Niveles</v-list-item-title>
  </v-list-item>
  <v-divider style="border-color: rgba(255,255,255,0.06);" />
  <v-list-item to="/auditoria" class="menu-item">
    <template v-slot:prepend><v-icon color="#7E57C2" size="20">mdi-shield-check</v-icon></template>
    <v-list-item-title class="text-white">Auditoría</v-list-item-title>
  </v-list-item>
  <v-list-item to="/backup" class="menu-item">
    <template v-slot:prepend><v-icon color="#FFD700" size="20">mdi-backup-restore</v-icon></template>
    <v-list-item-title class="text-white">Backups</v-list-item-title>
  </v-list-item>
</v-list>
      </v-menu>
      
      <v-chip v-if="auth.tiendaNombre" class="ml-2 chip-tienda" size="small">
        <v-icon start size="14">mdi-store</v-icon>
        {{ auth.tiendaNombre }}
      </v-chip>
      
      <v-chip class="ml-2 chip-tasa" size="small">
        <v-icon start size="14">mdi-currency-usd</v-icon>
        {{ auth.tasaActual }} BS/$
      </v-chip>
      
      <v-tooltip text="Refresco automático cada 30s">
        <template v-slot:activator="{ props }">
          <v-icon v-bind="props" size="12" class="ml-1 icon-sync">mdi-sync</v-icon>
        </template>
      </v-tooltip>
      
      <v-btn icon="mdi-logout" size="small" class="ml-2 btn-logout" @click="auth.logout()" title="Cerrar sesión" />
    </v-app-bar>
    
    <v-main class="main-bg">
      <v-container fluid class="pa-4">
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

let pollTimer = null
const POLL_INTERVAL = 30000

const startPolling = () => {
  if (!auth.token) return
  stopPolling()
  pollTimer = setInterval(() => {
    if (document.visibilityState === 'visible') {
      auth.cargarUsuario()
      auth.cargarTasa()
    }
  }, POLL_INTERVAL)
}

const stopPolling = () => {
  if (pollTimer) { clearInterval(pollTimer); pollTimer = null }
}

const handleVisibilityChange = () => {
  if (document.visibilityState === 'visible') { auth.cargarUsuario(); auth.cargarTasa(); startPolling() }
  else { stopPolling() }
}

watch(() => auth.token, (newToken) => { if (newToken) startPolling(); else stopPolling() })

onMounted(() => { auth.cargarTasa(); auth.cargarUsuario(); startPolling(); document.addEventListener('visibilitychange', handleVisibilityChange) })
onUnmounted(() => { stopPolling(); document.removeEventListener('visibilitychange', handleVisibilityChange) })
</script>

<style>
/* ============================================================
   ESTILOS GLOBALES - PAGINACIÓN VISIBLE EN TODAS LAS VISTAS
   ============================================================ */

/* Fondo general */
html, body, .v-application {
  background: #0a0e1a !important;
}

/* Paginación - Números de página en BLANCO */
.v-data-table-footer__pagination,
.v-pagination__item {
  color: rgba(255, 255, 255, 0.85) !important;
  font-weight: 500 !important;
}

/* Página activa */
.v-pagination__item--active {
  background: #4facfe !important;
  color: #ffffff !important;
  font-weight: 700 !important;
  box-shadow: 0 2px 8px rgba(79, 172, 254, 0.3);
}

/* Hover en páginas */
.v-pagination__item:hover:not(.v-pagination__item--active) {
  background: rgba(255, 255, 255, 0.08) !important;
}

/* Selector de items por página */
.v-data-table-footer__select .v-field__input {
  color: #ffffff !important;
}
.v-data-table-footer__select .v-icon {
  color: rgba(255, 255, 255, 0.7) !important;
}

/* Texto "1-10 of 50" */
.v-data-table-footer__info {
  color: rgba(255, 255, 255, 0.6) !important;
}

/* Scrollbar premium */
::-webkit-scrollbar { width: 6px; height: 6px; }
::-webkit-scrollbar-track { background: rgba(255,255,255,0.02); }
::-webkit-scrollbar-thumb { background: rgba(255,255,255,0.1); border-radius: 3px; }
::-webkit-scrollbar-thumb:hover { background: rgba(255,255,255,0.2); }
</style>

<style scoped>
/* App Bar Premium */
.app-premium { background: #0a0e1a; }
.main-bg { background: #0a0e1a !important; min-height: 100vh; }

.app-bar-premium {
  background: rgba(10, 14, 26, 0.9) !important;
  backdrop-filter: blur(20px) !important;
  -webkit-backdrop-filter: blur(20px) !important;
  border-bottom: 1px solid rgba(255, 255, 255, 0.06) !important;
  padding: 0 8px !important;
}

.logo-icon-small {
  width: 32px; height: 32px;
  background: linear-gradient(135deg, #4facfe, #6366f1);
  border-radius: 8px;
  display: flex; align-items: center; justify-content: center;
}

.logo-text {
  font-size: 1.1rem; font-weight: 700;
  background: linear-gradient(135deg, #ffffff, #94a3b8);
  -webkit-background-clip: text; -webkit-text-fill-color: transparent;
  background-clip: text;
}

/* Botones de navegación */
.nav-btn {
  text-transform: none !important;
  letter-spacing: 0.3px !important;
  font-weight: 500 !important;
  border-radius: 10px !important;
  padding: 0 12px !important;
  height: 36px !important;
  transition: all 0.3s ease !important;
  color: rgba(255, 255, 255, 0.7) !important;
}

.nav-btn:hover {
  background: rgba(255, 255, 255, 0.08) !important;
  color: #ffffff !important;
  transform: translateY(-1px);
}

.nav-btn-active {
  background: rgba(79, 172, 254, 0.15) !important;
  color: #4facfe !important;
  font-weight: 600 !important;
}

.nav-btn-success.nav-btn-active { background: rgba(76, 175, 80, 0.15) !important; color: #4caf50 !important; }
.nav-btn-warning.nav-btn-active { background: rgba(255, 213, 79, 0.15) !important; color: #ffd54f !important; }
.nav-btn-info.nav-btn-active { background: rgba(79, 172, 254, 0.15) !important; color: #4facfe !important; }

.nav-text { margin-left: 2px; }

@media (max-width: 960px) {
  .nav-text { display: none; }
  .nav-btn { padding: 0 8px !important; min-width: 36px !important; }
}

/* Menú desplegable */
.glass-card-menu {
  background: rgba(20, 25, 45, 0.95) !important;
  backdrop-filter: blur(20px) !important;
  border: 1px solid rgba(255, 255, 255, 0.08) !important;
  margin-top: 8px;
}
.menu-item:hover { background: rgba(255, 255, 255, 0.05) !important; }

/* Chips */
.chip-tienda {
  background: rgba(76, 175, 80, 0.15) !important;
  color: #4caf50 !important;
  border: 1px solid rgba(76, 175, 80, 0.2) !important;
  font-weight: 500 !important;
}
.chip-tasa {
  background: rgba(255, 255, 255, 0.06) !important;
  color: rgba(255, 255, 255, 0.8) !important;
  border: 1px solid rgba(255, 255, 255, 0.1) !important;
}
.icon-sync { color: rgba(76, 175, 80, 0.6) !important; animation: spin 3s linear infinite; }
@keyframes spin { 0% { transform: rotate(0deg); } 100% { transform: rotate(360deg); } }

.btn-logout { color: rgba(255, 255, 255, 0.4) !important; }
.btn-logout:hover { color: #f44336 !important; background: rgba(244, 67, 54, 0.1) !important; }
</style>