<template>
  <v-container fluid class="pa-0">
    <!-- ✅ FONDO MODERNO -->
    <div class="background-gradient"></div>

    <v-row class="ma-0">
      <v-col cols="12" class="pa-4">
        <!-- ✅ HEADER PREMIUM -->
        <div class="header-premium d-flex align-center justify-space-between flex-wrap">
          <div class="d-flex align-center">
            <div class="icon-wrapper pulse-animation">
              <v-icon size="32" color="white">mdi-chart-box</v-icon>
            </div>
            <div class="ml-3">
              <h1 class="text-h4 font-weight-bold text-white">Dashboard</h1>
              <p class="text-subtitle-2 text-white" style="opacity: 0.7;">Resumen del sistema de financiamiento</p>
            </div>
          </div>
          <div class="d-flex align-center" style="gap: 12px;">
            <div class="tasa-card glass-effect">
              <v-icon size="20" color="#FFD700">mdi-currency-usd</v-icon>
              <span class="font-weight-bold text-white ml-1">{{ stats.tasa || 0 }}</span>
              <span class="text-white" style="opacity: 0.6; font-size: 0.75rem;">BS/$</span>
            </div>
            <v-chip class="step-chip" color="transparent" size="large">
              <span class="text-white font-weight-bold">Actualizado</span>
              <span class="text-white ml-1" style="opacity: 0.6; font-size: 0.7rem;">{{ new Date().toLocaleTimeString() }}</span>
            </v-chip>
          </div>
        </div>

        <!-- ✅ KPIs PRINCIPALES -->
        <v-row class="mt-4">
          <v-col cols="12" sm="6" md="3" v-for="kpi in kpis" :key="kpi.label">
            <div class="kpi-card glass-effect" :class="kpi.color">
              <div class="d-flex align-center justify-space-between">
                <div>
                  <div class="kpi-label">{{ kpi.label }}</div>
                  <div class="kpi-value">{{ kpi.value }}</div>
                  <div class="kpi-sub" v-if="kpi.sub">
                    <v-icon size="14" :color="kpi.subColor || 'white'" class="mr-1">{{ kpi.subIcon }}</v-icon>
                    {{ kpi.sub }}
                  </div>
                </div>
                <div class="kpi-icon-wrapper" :style="`background: ${kpi.iconBg}`">
                  <v-icon size="32" color="white">{{ kpi.icon }}</v-icon>
                </div>
              </div>
            </div>
          </v-col>
        </v-row>

        <!-- ✅ GRÁFICA Y TABLA -->
        <v-row class="mt-4">
          <!-- Gráfica de Barras -->
          <v-col cols="12" lg="7">
            <v-card class="glass-card rounded-xl" elevation="0">
              <v-card-title class="text-h6 font-weight-bold text-white pa-4">
                <v-icon color="#FFD700" class="mr-2">mdi-chart-bar</v-icon>
                Financiamientos por Nivel
              </v-card-title>
              <v-card-text class="pa-4">
                <div class="chart-container">
                  <div
                    v-for="(nivel, idx) in nivelesData"
                    :key="idx"
                    class="chart-bar-wrapper"
                  >
                    <div class="d-flex justify-space-between align-center">
                      <div class="chart-label">{{ nivel.nombre }}</div>
                      <span class="chart-count">{{ nivel.cantidad }}</span>
                    </div>
                    <div class="chart-bar-bg">
                      <div
                        class="chart-bar-fill"
                        :style="{
                          width: `${(nivel.cantidad / maxNivel) * 100}%`,
                          background: `linear-gradient(90deg, ${nivel.color}80, ${nivel.color})`
                        }"
                      >
                        <span class="chart-value">{{ nivel.cantidad }}</span>
                      </div>
                    </div>
                  </div>
                </div>
                <div class="text-caption text-center mt-2" style="color: rgba(255,255,255,0.3);">
                  Distribución de clientes por nivel de financiamiento
                </div>
              </v-card-text>
            </v-card>
          </v-col>

          <!-- Actividad Reciente -->
          <v-col cols="12" lg="5">
            <v-card class="glass-card rounded-xl" elevation="0">
              <v-card-title class="text-h6 font-weight-bold text-white pa-4">
                <v-icon color="#4facfe" class="mr-2">mdi-history</v-icon>
                Financiamientos Recientes
              </v-card-title>
              <v-card-text class="pa-4">
                <div v-if="recientes.length > 0">
                  <div
                    v-for="(fin, idx) in recientes"
                    :key="idx"
                    class="recent-item glass-effect mb-2"
                  >
                    <div class="d-flex align-center justify-space-between">
                      <div class="d-flex align-center">
                        <v-avatar size="40" :color="fin.estado === 'activo' ? '#FFD700' : '#4caf50'" class="mr-3">
                          <v-icon size="20" color="white">
                            {{ fin.estado === 'activo' ? 'mdi-clock-outline' : 'mdi-check-circle' }}
                          </v-icon>
                        </v-avatar>
                        <div>
                          <div class="recent-code font-weight-bold text-white">
                            {{ fin.codigo }}
                            <v-chip size="x-small" :color="fin.estado === 'activo' ? 'warning' : 'success'" class="ml-2">
                              {{ fin.estado }}
                            </v-chip>
                          </div>
                          <div class="recent-cliente" style="color: rgba(255,255,255,0.6); font-size: 0.8rem;">
                            {{ fin.cliente }}
                          </div>
                        </div>
                      </div>
                      <div class="text-right">
                        <div class="recent-monto text-white font-weight-bold">
                          BS {{ formatearBS(fin.monto_total_bs) }}
                        </div>
                        <div class="recent-fecha" style="color: rgba(255,255,255,0.3); font-size: 0.65rem;">
                          {{ formatearFecha(fin.fecha_creacion) }}
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
                <div v-else class="empty-state glass-effect">
                  <v-icon color="rgba(255,255,255,0.3)" size="32">mdi-inbox</v-icon>
                  <div class="text-caption" style="color: rgba(255,255,255,0.4);">No hay financiamientos recientes</div>
                </div>
              </v-card-text>
            </v-card>
          </v-col>
        </v-row>

        <!-- ✅ ALERTAS Y RESUMEN -->
        <v-row class="mt-4">
          <v-col cols="12" md="6">
            <div class="alert-card glass-effect" style="border-left: 4px solid #ef5350;">
              <div class="d-flex align-center justify-space-between">
                <div class="d-flex align-center">
                  <div class="alert-icon-wrapper" style="background: rgba(239, 83, 80, 0.15);">
                    <v-icon size="28" color="#ef5350">mdi-alert-circle</v-icon>
                  </div>
                  <div class="ml-3">
                    <div class="alert-title text-white font-weight-bold">Cuotas Vencidas</div>
                    <div class="alert-value text-h3 font-weight-bold text-white">{{ stats.vencidas || 0 }}</div>
                  </div>
                </div>
                <v-btn
                  to="/conciliacion"
                  color="#ef5350"
                  variant="outlined"
                  size="small"
                  class="rounded-xl"
                >
                  Ver Conciliación
                </v-btn>
              </div>
            </div>
          </v-col>

          <v-col cols="12" md="6">
            <div class="alert-card glass-effect" style="border-left: 4px solid #7E57C2;">
              <div class="d-flex align-center justify-space-between">
                <div class="d-flex align-center">
                  <div class="alert-icon-wrapper" style="background: rgba(126, 87, 194, 0.15);">
                    <v-icon size="28" color="#7E57C2">mdi-wallet</v-icon>
                  </div>
                  <div class="ml-3">
                    <div class="alert-title text-white font-weight-bold">Cartera Total</div>
                    <div class="d-flex align-center" style="gap: 16px;">
                      <div>
                        <span class="text-caption" style="color: rgba(255,255,255,0.4);">BS</span>
                        <span class="alert-value text-h4 font-weight-bold text-white">{{ formatearBS(stats.cartera_bs) }}</span>
                      </div>
                      <div>
                        <span class="text-caption" style="color: rgba(255,255,255,0.4);">USD</span>
                        <span class="alert-value text-h4 font-weight-bold text-white">${{ formatearUSD(stats.cartera_usd) }}</span>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </v-col>
        </v-row>
      </v-col>
    </v-row>
  </v-container>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue'
import { api } from '@/config/api'

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

const kpis = computed(() => [
  { 
    label: 'Total Clientes', 
    value: stats.value.clientes, 
    icon: 'mdi-account-group', 
    color: 'primary',
    iconBg: 'rgba(79, 172, 254, 0.2)',
    sub: 'Registrados',
    subIcon: 'mdi-trending-up',
    subColor: '#4caf50'
  },
  { 
    label: 'Financiamientos Activos', 
    value: stats.value.activos, 
    icon: 'mdi-cash-multiple', 
    color: 'success',
    iconBg: 'rgba(76, 175, 80, 0.2)',
    sub: 'En curso',
    subIcon: 'mdi-clock-outline',
    subColor: '#FFD700'
  },
  { 
    label: 'Cuotas Pendientes', 
    value: stats.value.pendientes, 
    icon: 'mdi-calendar-clock', 
    color: 'warning',
    iconBg: 'rgba(255, 193, 7, 0.2)',
    sub: 'Por cobrar',
    subIcon: 'mdi-alert-circle',
    subColor: '#ef5350'
  },
  { 
    label: 'Tasa del Día', 
    value: stats.value.tasa || 0, 
    icon: 'mdi-bank', 
    color: 'info',
    iconBg: 'rgba(0, 188, 212, 0.2)',
    sub: 'BS/$',
    subIcon: 'mdi-currency-usd',
    subColor: 'rgba(255,255,255,0.6)'
  }
])

const maxNivel = computed(() => {
  if (nivelesData.value.length === 0) return 1
  const max = Math.max(...nivelesData.value.map(n => n.cantidad || 0))
  return max > 0 ? max : 1
})

const formatearBS = (monto) => {
  if (!monto && monto !== 0) return '0,00'
  return Number(monto).toLocaleString('es-VE', {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2
  })
}

const formatearUSD = (monto) => {
  if (!monto && monto !== 0) return '0.00'
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
    // ✅ Tasa del dólar
    const tasaData = await api.get('/config/tasa-dolar')
    stats.value.tasa = tasaData.tasa || 0

    // ✅ Clientes
    const clientesData = await api.get('/clientes')
    stats.value.clientes = Array.isArray(clientesData) ? clientesData.length : 0

    // ✅ Financiamientos
    const financiamientos = await api.get('/financiamientos')
    const listaFinanciamientos = Array.isArray(financiamientos) ? financiamientos : []
    
    const activos = listaFinanciamientos.filter(f => f.estado === 'activo')
    stats.value.activos = activos.length

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

    for (const fin of listaFinanciamientos) {
      if (fin.nivel_aplicado && nivelesConteo[fin.nivel_aplicado] !== undefined) {
        nivelesConteo[fin.nivel_aplicado]++
      }

      try {
        const cuotasData = await api.get(`/financiamientos/${fin.id}/cuotas`)
        const cuotas = Array.isArray(cuotasData) ? cuotasData : (cuotasData?.cuotas || [])
        
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
      } catch (e) {
        // Continuar
      }
    }

    stats.value.pendientes = pendientes
    stats.value.vencidas = vencidas
    stats.value.cartera_bs = cartera_bs
    stats.value.cartera_usd = cartera_usd

    nivelesData.value = Object.keys(nivelesConteo).map(n => ({
      nombre: n.toUpperCase(),
      cantidad: nivelesConteo[n],
      color: colores[n]
    }))

    recientes.value = listaFinanciamientos
      .sort((a, b) => new Date(b.creado_en || b.fecha_creacion || 0) - new Date(a.creado_en || a.fecha_creacion || 0))
      .slice(0, 5)
      .map(f => ({
        codigo: f.codigo || 'N/A',
        cliente: f.cliente_nombre || 'Sin nombre',
        monto_total_bs: f.monto_total_bs || 0,
        estado: f.estado || 'activo',
        fecha_creacion: f.creado_en || f.fecha_creacion || new Date().toISOString()
      }))

  } catch (error) {
    console.error('Error cargando datos:', error)
  }
}

onMounted(cargarDatos)
</script>

<style scoped>
/* ✅ FONDO MODERNO */
.background-gradient {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: radial-gradient(ellipse at 20% 50%, rgba(79, 172, 254, 0.12), transparent 70%),
              radial-gradient(ellipse at 80% 50%, rgba(99, 102, 241, 0.08), transparent 70%),
              #0a0e1a;
  z-index: 0;
}

/* ✅ HEADER PREMIUM */
.header-premium {
  position: relative;
  z-index: 1;
  padding: 16px 24px;
  background: rgba(255, 255, 255, 0.05);
  backdrop-filter: blur(20px);
  border-radius: 20px;
  border: 1px solid rgba(255, 255, 255, 0.06);
}

.icon-wrapper {
  width: 48px;
  height: 48px;
  background: linear-gradient(135deg, #4facfe, #6366f1);
  border-radius: 14px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.pulse-animation {
  animation: pulse 2s infinite;
}

@keyframes pulse {
  0%, 100% { transform: scale(1); }
  50% { transform: scale(1.05); }
}

.tasa-card {
  padding: 8px 16px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  gap: 6px;
}

.step-chip {
  background: rgba(255, 255, 255, 0.08) !important;
  padding: 8px 16px !important;
  border-radius: 50px !important;
}

/* ✅ GLASS EFFECT */
.glass-effect {
  background: rgba(255, 255, 255, 0.05) !important;
  backdrop-filter: blur(16px) !important;
  border: 1px solid rgba(255, 255, 255, 0.08) !important;
  border-radius: 16px !important;
}

.glass-card {
  background: rgba(255, 255, 255, 0.03) !important;
  backdrop-filter: blur(24px) !important;
  border: 1px solid rgba(255, 255, 255, 0.06) !important;
  border-radius: 24px !important;
}

/* ✅ KPIs */
.kpi-card {
  padding: 16px 20px;
  transition: all 0.3s ease;
}

.kpi-card:hover {
  transform: translateY(-4px);
  border-color: rgba(79, 172, 254, 0.3) !important;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.2) !important;
}

.kpi-label {
  font-size: 0.7rem;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  color: rgba(255, 255, 255, 0.4);
}

.kpi-value {
  font-size: 2rem;
  font-weight: 800;
  color: white;
  line-height: 1.2;
}

.kpi-sub {
  font-size: 0.7rem;
  color: rgba(255, 255, 255, 0.5);
  margin-top: 4px;
}

.kpi-icon-wrapper {
  width: 56px;
  height: 56px;
  border-radius: 14px;
  display: flex;
  align-items: center;
  justify-content: center;
}

/* ✅ GRÁFICA */
.chart-container {
  padding: 8px 0;
}

.chart-bar-wrapper {
  margin-bottom: 12px;
}

.chart-label {
  font-size: 0.8rem;
  font-weight: 600;
  color: rgba(255, 255, 255, 0.7);
}

.chart-count {
  font-size: 0.8rem;
  font-weight: 700;
  color: white;
}

.chart-bar-bg {
  background: rgba(255, 255, 255, 0.05);
  border-radius: 8px;
  height: 28px;
  overflow: hidden;
  position: relative;
  margin-top: 2px;
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
  font-weight: 700;
  font-size: 0.8rem;
  text-shadow: 0 1px 4px rgba(0, 0, 0, 0.3);
}

/* ✅ RECIENTES */
.recent-item {
  padding: 12px 16px;
  transition: all 0.3s ease;
}

.recent-item:hover {
  transform: translateX(4px);
  border-color: rgba(79, 172, 254, 0.2) !important;
}

.recent-code {
  font-size: 0.85rem;
}

.recent-cliente {
  font-size: 0.75rem;
}

.recent-monto {
  font-size: 0.9rem;
}

/* ✅ ALERTAS */
.alert-card {
  padding: 16px 20px;
}

.alert-icon-wrapper {
  width: 48px;
  height: 48px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.alert-title {
  font-size: 0.75rem;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  opacity: 0.6;
}

.alert-value {
  line-height: 1.2;
}

/* ✅ EMPTY STATE */
.empty-state {
  padding: 24px;
  text-align: center;
  border: 1px dashed rgba(255, 255, 255, 0.08);
}

/* ✅ RESPONSIVE */
@media (max-width: 600px) {
  .header-premium {
    flex-direction: column;
    gap: 12px;
    align-items: stretch !important;
  }
  
  .kpi-value {
    font-size: 1.5rem;
  }
  
  .kpi-icon-wrapper {
    width: 44px;
    height: 44px;
  }
  
  .kpi-icon-wrapper .v-icon {
    font-size: 24px !important;
  }
  
  .alert-card {
    flex-direction: column;
    gap: 12px;
  }
}
</style>