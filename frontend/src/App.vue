<template>
  <v-app>
    <!-- App Bar con fondo degradado -->
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
      
      <!-- Botones principales con estilo mejorado -->
      <v-btn 
        to="/" 
        variant="text" 
        class="nav-btn mx-1"
        :class="{ 'nav-btn-active': $route.path === '/' }"
      >
        <v-icon start>mdi-view-dashboard</v-icon>
        Dashboard
      </v-btn>
      
      <v-btn 
        to="/cajero" 
        color="success" 
        variant="elevated"
        class="nav-btn mx-1 nav-btn-cajero"
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
      
      <!-- Menú Configuración con dropdown -->
      <v-menu>
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
          <v-list-item to="/configuracion" :active="$route.path === '/configuracion'">
            <template v-slot:prepend>
              <v-icon color="primary">mdi-currency-usd</v-icon>
            </template>
            <v-list-item-title>Tasa del Dólar</v-list-item-title>
          </v-list-item>
          <v-list-item to="/niveles" :active="$route.path === '/niveles'">
            <template v-slot:prepend>
              <v-icon color="amber-darken-2">mdi-trophy</v-icon>
            </template>
            <v-list-item-title>Niveles</v-list-item-title>
          </v-list-item>
        </v-list>
      </v-menu>
      
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
import axios from 'axios'
import { API_URL } from '@/config/api'  // ✅ Importación al principio

const tasaActual = ref(40.0)

const cargarTasa = async () => {
  try {
    // ✅ Usar API_URL directamente (ya importado)
    const res = await axios.get(`${API_URL}/config/tasa-dolar`)
    tasaActual.value = res.data.tasa
  } catch (e) {
    console.error('Error cargando tasa:', e)
  }
}

onMounted(() => {
  cargarTasa()
  setInterval(cargarTasa, 300000) // Actualizar cada 5 minutos
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

.nav-btn-cajero {
  box-shadow: 0 4px 12px rgba(76, 175, 80, 0.3);
}

.nav-btn-cajero:hover {
  box-shadow: 0 6px 16px rgba(76, 175, 80, 0.5);
}

/* Animación para el menú dropdown */
.v-list {
  border-radius: 12px !important;
  overflow: hidden;
}
</style>