<template>
  <v-container fluid class="dashboard-bg">
    <!-- Título con animación -->
    <v-row>
      <v-col cols="12">
        <div class="text-center mb-6">
          <h1 class="text-h3 font-weight-bold text-white dashboard-title">
            📊  FinanCoop
          </h1>
          <p class="text-subtitle-1 text-grey-lighten-2">
            Resumen del sistema de financiamiento
          </p>
        </div>
      </v-col>
    </v-row>

    <!-- KPIs Principales -->
    <v-row>
      <v-col cols="12" sm="6" md="3">
        <v-card class="kpi-card" elevation="8" color="primary" dark>
          <v-card-text>
            <div class="d-flex align-center justify-space-between">
              <div>
                <div class="text-caption text-grey-lighten-2">Total Clientes</div>
                <div class="text-h3 font-weight-bold">{{ stats.clientes }}</div>
                <div class="text-caption text-success mt-1">
                  <v-icon size="small">mdi-trending-up</v-icon>
                  Registrados
                </div>
              </div>
              <v-avatar size="64" color="primary-lighten-2" class="kpi-icon">
                <v-icon size="36">mdi-account-group</v-icon>
              </v-avatar>
            </div>
          </v-card-text>
        </v-card>
      </v-col>

      <v-col cols="12" sm="6" md="3">
        <v-card class="kpi-card" elevation="8" color="success" dark>
          <v-card-text>
            <div class="d-flex align-center justify-space-between">
              <div>
                <div class="text-caption text-grey-lighten-2">Financiamientos Activos</div>
                <div class="text-h3 font-weight-bold">{{ stats.activos }}</div>
                <div class="text-caption text-warning mt-1">
                  <v-icon size="small">mdi-clock-outline</v-icon>
                  En curso
                </div>
              </div>
              <v-avatar size="64" color="success-lighten-2" class="kpi-icon">
                <v-icon size="36">mdi-cash-multiple</v-icon>
              </v-avatar>
            </div>
          </v-card-text>
        </v-card>
      </v-col>

      <v-col cols="12" sm="6" md="3">
        <v-card class="kpi-card" elevation="8" color="warning" dark>
          <v-card-text>
            <div class="d-flex align-center justify-space-between">
              <div>
                <div class="text-caption text-grey-lighten-2">Cuotas Pendientes</div>
                <div class="text-h3 font-weight-bold">{{ stats.pendientes }}</div>
                <div class="text-caption text-error mt-1">
                  <v-icon size="small">mdi-alert-circle</v-icon>
                  Por cobrar
                </div>
              </div>
              <v-avatar size="64" color="warning-lighten-2" class="kpi-icon">
                <v-icon size="36">mdi-calendar-clock</v-icon>
              </v-avatar>
            </div>
          </v-card-text>
        </v-card>
      </v-col>

      <v-col cols="12" sm="6" md="3">
        <v-card class="kpi-card" elevation="8" color="info" dark>
          <v-card-text>
            <div class="d-flex align-center justify-space-between">
              <div>
                <div class="text-caption text-grey-lighten-2">Tasa del Día</div>
                <div class="text-h3 font-weight-bold">{{ stats.tasa }}</div>
                <div class="text-caption text-grey-lighten-2 mt-1">
                  <v-icon size="small">mdi-currency-usd</v-icon>
                  BS/$
                </div>
              </div>
              <v-avatar size="64" color="info-lighten-2" class="kpi-icon">
                <v-icon size="36">mdi-bank</v-icon>
              </v-avatar>
            </div>
          </v-card-text>
        </v-card>
      </v-col>
    </v-row>

    <!-- Gráfica y Tabla -->
    <v-row class="mt-4">
      <!-- Gráfica de Barras -->
      <v-col cols="12" lg="7">
        <v-card class="chart-card" elevation="6">
          <v-card-title class="text-h6 font-weight-bold">
            <v-icon color="primary" class="mr-2">mdi-chart-bar</v-icon>
            Financiamientos por Nivel
          </v-card-title>
          <v-card-text>
            <div class="chart-container">
              <div
                v-for="(nivel, idx) in nivelesData"
                :key="idx"
                class="chart-bar-wrapper"
              >
                <div class="chart-label">{{ nivel.nombre }}</div>
                <div class="chart-bar-bg">
                  <div
                    class="chart-bar-fill"
                    :style="{
                      width: `${(nivel.cantidad / maxNivel) * 100}%`,
                      backgroundColor: nivel.color
                    }"
                  >
                    <span class="chart-value">{{ nivel.cantidad }}</span>
                  </div>
                </div>
              </div>
            </div>
          </v-card-text>
        </v-card>
      </v-col>

      <!-- Tabla de Actividad Reciente -->
      <v-col cols="12" lg="5">
        <v-card class="recent-card" elevation="6">
          <v-card-title class="text-h6 font-weight-bold">
            <v-icon color="success" class="mr-2">mdi-history</v-icon>
            Financiamientos Recientes
          </v-card-title>
          <v-card-text>
            <v-list density="compact">
              <v-list-item
                v-for="(fin, idx) in recientes"
                :key="idx"
                :class="{
                  'bg-success-lighten-5': fin.estado === 'completado',
                  'bg-warning-lighten-5': fin.estado === 'activo'
                }"
                class="mb-2 rounded"
              >
                <template v-slot:prepend>
                  <v-avatar :color="fin.estado === 'activo' ? 'warning' : 'success'" size="36">
                    <v-icon size="20" color="white">
                      {{ fin.estado === 'activo' ? 'mdi-clock-outline' : 'mdi-check-circle' }}
                    </v-icon>
                  </v-avatar>
                </template>
                <v-list-item-title class="font-weight-bold">
                  {{ fin.codigo }}
                  <v-chip size="x-small" :color="fin.estado === 'activo' ? 'warning' : 'success'" class="ml-2">
                    {{ fin.estado }}
                  </v-chip>
                </v-list-item-title>
                <v-list-item-subtitle>
                  {{ fin.cliente }} — BS {{ formatearBS(fin.monto_total_bs) }}
                </v-list-item-subtitle>
                <template v-slot:append>
                  <div class="text-caption text-grey">
                    {{ formatearFecha(fin.fecha_creacion) }}
                  </div>
                </template>
              </v-list-item>
            </v-list>
            <v-alert
              v-if="recientes.length === 0"
              type="info"
              density="compact"
              class="mt-2"
            >
              No hay financiamientos recientes
            </v-alert>
          </v-card-text>
        </v-card>
      </v-col>
    </v-row>

    <!-- Alertas y Resumen -->
    <v-row class="mt-4">
      <v-col cols="12" md="6">
        <v-card class="alert-card" elevation="6" color="error" dark>
          <v-card-title class="text-h6">
            <v-icon class="mr-2">mdi-alert-circle</v-icon>
            Cuotas Vencidas
          </v-card-title>
          <v-card-text>
            <div class="d-flex align-center">
              <div class="text-h2 font-weight-bold mr-4">{{ stats.vencidas }}</div>
              <div>
                <div class="text-body-1">cuotas están vencidas</div>
                <v-btn
                  to="/conciliacion"
                  color="white"
                  variant="outlined"
                  size="small"
                  class="mt-2"
                >
                  Ver Conciliación
                </v-btn>
              </div>
            </div>
          </v-card-text>
        </v-card>
      </v-col>

      <v-col cols="12" md="6">
        <v-card class="alert-card" elevation="6" color="purple-darken-2" dark>
          <v-card-title class="text-h6">
            <v-icon class="mr-2">mdi-wallet</v-icon>
            Cartera Total
          </v-card-title>
          <v-card-text>
            <div class="d-flex align-center justify-space-between">
              <div>
                <div class="text-caption">En Bolívares</div>
                <div class="text-h4 font-weight-bold">BS {{ formatearBS(stats.cartera_bs) }}</div>
              </div>
              <div class="text-right">
                <div class="text-caption">Referencia USD</div>
                <div class="text-h4 font-weight-bold">$ {{ formatearUSD(stats.cartera_usd) }}</div>
              </div>
            </div>
          </v-card-text>
        </v-card>
      </v-col>
    </v-row>
  </v-container>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue'
import { api } from '@/config/api'  // ✅ Usar 'api'

const stats = ref({
  clientes: 0,
  activos: 0,
  pendientes: 0,
  vencidas: 0,
  tasa: 0,
  cartera_bs: 0,
  cartera_usd: 0
})

const recientes = ref([])
const nivelesData = ref([])

const maxNivel = computed(() => {
  const max = Math.max(...nivelesData.value.map(n => n.cantidad))
  return max > 0 ? max : 1
})

const formatearBS = (monto) => {
  if (!monto) return '0,00'
  return Number(monto).toLocaleString('es-VE', {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2
  })
}

const formatearUSD = (monto) => {
  if (!monto) return '0.00'
  return Number(monto).toLocaleString('en-US', {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2
  })
}

const formatearFecha = (fechaStr) => {
  if (!fechaStr) return ''
  const fecha = new Date(fechaStr)
  return fecha.toLocaleDateString('es-VE', {
    day: '2-digit',
    month: 'short',
    year: 'numeric'
  })
}

const cargarDatos = async () => {
  try {
    // Tasa
    const tasaData = await api.get('/config/tasa-dolar')
    stats.value.tasa = tasaData.tasa

    // Clientes
    const clientesData = await api.get('/clientes')
    const listaClientes = clientesData.clientes || clientesData
    stats.value.clientes = listaClientes.length
    // Financiamientos
    const financiamientos = await api.get('/financiamientos')
    const activos = financiamientos.filter(f => f.estado === 'activo')
    const completados = financiamientos.filter(f => f.estado === 'completado')
    stats.value.activos = activos.length

    // Cuotas y cartera
    let pendientes = 0
    let vencidas = 0
    let cartera_bs = 0
    let cartera_usd = 0

    const nivelesConteo = { nuevo: 0, bronce: 0, plata: 0, oro: 0, platino: 0 }
    const colores = {
      nuevo: '#9E9E9E',
      bronce: '#8D6E63',
      plata: '#42A5F5',
      oro: '#FFD700',
      platino: '#AB47BC'
    }

    for (const fin of financiamientos) {
      // Contar por nivel
      if (nivelesConteo[fin.nivel_aplicado] !== undefined) {
        nivelesConteo[fin.nivel_aplicado]++
      }

      const cuotas = await api.get(`/financiamientos/${fin.id}/cuotas`)
      const cuotasPendientes = cuotas.filter(c => c.estado === 'pendiente')
      const cuotasVencidas = cuotas.filter(c => {
        return c.estado === 'pendiente' && new Date(c.fecha_vencimiento) < new Date()
      })

      pendientes += cuotasPendientes.length
      vencidas += cuotasVencidas.length

      if (fin.estado === 'activo') {
        cartera_bs += fin.monto_financia_bs || 0
        cartera_usd += fin.monto_financia_usd || 0
      }
    }

    stats.value.pendientes = pendientes
    stats.value.vencidas = vencidas
    stats.value.cartera_bs = cartera_bs
    stats.value.cartera_usd = cartera_usd

    // Preparar datos de niveles para gráfica
    nivelesData.value = Object.keys(nivelesConteo).map(n => ({
      nombre: n.toUpperCase(),
      cantidad: nivelesConteo[n],
      color: colores[n]
    }))

    // Recientes (últimos 5)
    recientes.value = financiamientos
      .sort((a, b) => new Date(b.fecha_creacion) - new Date(a.fecha_creacion))
      .slice(0, 5)
      .map(f => ({
        codigo: f.codigo,
        cliente: f.cliente?.nombre || 'Sin nombre',
        monto_total_bs: f.monto_total_bs,
        estado: f.estado,
        fecha_creacion: f.fecha_creacion
      }))

  } catch (error) {
    console.error('Error cargando datos:', error)
  }
}

onMounted(cargarDatos)
</script>

<style scoped>
.dashboard-bg {
  background: linear-gradient(135deg, #1a237e 0%, #0d47a1 50%, #01579b 100%);
  min-height: 100vh;
  padding: 24px;
}

.dashboard-title {
  text-shadow: 2px 2px 4px rgba(0, 0, 0, 0.3);
  animation: fadeInDown 0.8s ease;
}

.kpi-card {
  border-radius: 16px;
  transition: transform 0.3s ease, box-shadow 0.3s ease;
  overflow: hidden;
}

.kpi-card:hover {
  transform: translateY(-8px);
  box-shadow: 0 12px 24px rgba(0, 0, 0, 0.3) !important;
}

.kpi-icon {
  opacity: 0.9;
}

.chart-card,
.recent-card,
.alert-card {
  border-radius: 16px;
  background: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(10px);
}

.chart-container {
  padding: 16px 0;
}

.chart-bar-wrapper {
  margin-bottom: 16px;
}

.chart-label {
  font-size: 0.85rem;
  font-weight: 600;
  color: #424242;
  margin-bottom: 4px;
  text-transform: uppercase;
}

.chart-bar-bg {
  background: #e0e0e0;
  border-radius: 8px;
  height: 32px;
  overflow: hidden;
  position: relative;
}

.chart-bar-fill {
  height: 100%;
  border-radius: 8px;
  transition: width 1s ease;
  display: flex;
  align-items: center;
  justify-content: flex-end;
  padding-right: 8px;
  min-width: 40px;
}

.chart-value {
  color: white;
  font-weight: bold;
  font-size: 0.9rem;
  text-shadow: 1px 1px 2px rgba(0, 0, 0, 0.3);
}

@keyframes fadeInDown {
  from {
    opacity: 0;
    transform: translateY(-20px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

@media (max-width: 600px) {
  .dashboard-title {
    font-size: 1.5rem !important;
  }
  .kpi-card .text-h3 {
    font-size: 1.5rem !important;
  }
}
</style>