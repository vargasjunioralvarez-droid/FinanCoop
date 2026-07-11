<template>
  <v-app>
    <!-- App Bar -->
    <v-app-bar 
      color="primary" 
      dark
      elevation="4"
      class="app-bar-gradient"
    >
      <v-app-bar-title class="font-weight-bold">
        <v-icon size="28" class="mr-2" color="white">mdi-wallet</v-icon>
        FinanCash
      </v-app-bar-title>
      
      <v-spacer></v-spacer>
      
      <!-- Botones para TODOS -->
      <v-btn 
        to="/inicio" 
        variant="text" 
        class="nav-btn mx-1"
        :class="{ 'nav-btn-active': $route.path === '/inicio' }"
      >
        <v-icon start>mdi-view-dashboard</v-icon>
        Dashboard
      </v-btn>
      
      <v-btn 
        to="/cajero" 
        color="success" 
        variant="elevated"
        class="nav-btn mx-1"
        :class="{ 'nav-btn-active': $route.path === '/cajero' }"
      >
        <v-icon start>mdi-cart-plus</v-icon>
        Cajero
      </v-btn>
      
      <v-btn 
        to="/clientes" 
        variant="text" 
        class="nav-btn mx-1"
        :class="{ 'nav-btn-active': $route.path === '/clientes' }"
      >
        <v-icon start>mdi-account-group</v-icon>
        Clientes
      </v-btn>
      
      <v-btn 
        to="/financiamientos" 
        variant="text" 
        class="nav-btn mx-1"
        :class="{ 'nav-btn-active': $route.path === '/financiamientos' }"
      >
        <v-icon start>mdi-file-document-multiple</v-icon>
        Financiamientos
      </v-btn>
      
      <v-btn 
        to="/conciliacion" 
        color="warning" 
        variant="elevated"
        class="nav-btn mx-1"
        :class="{ 'nav-btn-active': $route.path === '/conciliacion' }"
      >
        <v-icon start>mdi-cash-check</v-icon>
        Conciliación
      </v-btn>
      
      <!-- ✅ SOLO ADMIN: Configuración -->
      <v-menu v-if="esAdmin">
        <template v-slot:activator="{ props }">
          <v-btn 
            v-bind="props"
            color="info" 
            variant="elevated"
            class="nav-btn mx-1"
          >
            <v-icon start>mdi-cog</v-icon>
            Config
            <v-icon end size="14">mdi-chevron-down</v-icon>
          </v-btn>
        </template>
        <v-list elevation="4" rounded="lg">
          <v-list-item to="/configuracion">
            <template v-slot:prepend>
              <v-icon color="primary">mdi-currency-usd</v-icon>
            </template>
            <v-list-item-title>Tasa del Dólar</v-list-item-title>
          </v-list-item>
          <v-list-item to="/niveles">
            <template v-slot:prepend>
              <v-icon color="amber-darken-2">mdi-trophy</v-icon>
            </template>
            <v-list-item-title>Niveles</v-list-item-title>
          </v-list-item>
        </v-list>
      </v-menu>
      
      <!-- ✅ SOLO ADMIN: Usuarios -->
      <v-btn 
        v-if="esAdmin"
        to="/usuarios" 
        color="error" 
        variant="elevated"
        class="nav-btn mx-1"
        :class="{ 'nav-btn-active': $route.path === '/usuarios' }"
      >
        <v-icon start>mdi-shield-account</v-icon>
        Usuarios
      </v-btn>
      
      <!-- Tasa en la barra -->
      <v-chip 
        class="ml-3" 
        color="white" 
        variant="outlined" 
        size="small"
        prepend-icon="mdi-currency-usd"
      >
        {{ tasaActual }} BS/$
      </v-chip>
      
      <!-- Cerrar sesión -->
      <v-btn 
        icon="mdi-logout" 
        size="small"
        class="ml-2"
        @click="cerrarSesion"
        title="Cerrar sesión"
      ></v-btn>
    </v-app-bar>
    
    <v-main>
      <v-container fluid class="pa-6">
        <router-view></router-view>
      </v-container>
    </v-main>
  </v-app>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import axios from 'axios'
import { API_URL } from '@/config/api'

const router = useRouter()
const tasaActual = ref(40.0)

// ✅ VERIFICAR SI ES ADMIN
const esAdmin = localStorage.getItem('admin_rol') === 'admin'

const cargarTasa = async () => {
  try {
    const res = await axios.get(`${API_URL}/config/tasa-dolar`)
    tasaActual.value = res.data.tasa
  } catch (e) {
    console.error('Error cargando tasa:', e)
  }
}

const cerrarSesion = () => {
  localStorage.removeItem('admin_token')
  localStorage.removeItem('admin_rol')
  localStorage.removeItem('admin_username')
  localStorage.removeItem('admin_nombre')
  router.push('/login')
}

onMounted(() => {
  cargarTasa()
  setInterval(cargarTasa, 300000)
})
</script>

<style scoped>
.app-bar-gradient {
  background: linear-gradient(135deg, #1565c0 0%, #0d47a1 100%) !important;
}

.nav-btn {
  text-transform: none;
  letter-spacing: 0.5px;
  font-weight: 500;
  border-radius: 10px;
  padding: 0 16px !important;
  height: 40px;
  transition: all 0.3s ease;
}

.nav-btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0,0,0,0.2);
}

.nav-btn-active {
  background: rgba(255,255,255,0.15) !important;
  font-weight: 600;
}
</style>