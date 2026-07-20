<template>
  <v-container fluid class="pa-0">
    <div class="background-gradient"></div>
    
    <v-row class="ma-0">
      <v-col cols="12" class="pa-4">
        <!-- HEADER PREMIUM -->
        <div class="header-premium d-flex align-center justify-space-between flex-wrap">
          <div class="d-flex align-center">
            <div class="icon-wrapper pulse-animation">
              <v-icon size="32" color="white">mdi-cog</v-icon>
            </div>
            <div class="ml-3">
              <h1 class="text-h4 font-weight-bold text-white">Configuración del Sistema</h1>
              <p class="text-subtitle-2 text-white" style="opacity: 0.7;">Tasa del dólar y parámetros generales</p>
            </div>
          </div>
          <v-chip class="step-chip" color="transparent" size="large">
            <span class="text-white font-weight-bold">{{ tasaActual }} BS/$</span>
          </v-chip>
        </div>

        <v-row class="mt-4">
          <!-- TASA DEL DÓLAR -->
          <v-col cols="12" md="6">
            <v-card class="glass-card rounded-xl" elevation="0">
              <v-card-title class="text-h6 font-weight-bold text-white pa-4" style="background: linear-gradient(135deg, rgba(79,172,254,0.15), rgba(99,102,241,0.1));">
                <v-icon color="#4facfe" class="mr-2">mdi-currency-usd</v-icon>
                Tasa del Dólar
              </v-card-title>
              <v-card-text class="pa-4">
                <div class="tasa-display text-center mb-4">
                  <div class="tasa-number">{{ tasaActual }}</div>
                  <div class="tasa-label">BS/$</div>
                </div>
                
                <div class="d-flex justify-space-between text-caption mb-4" style="color: rgba(255,255,255,0.4);">
                  <span>Actualizado: {{ fechaActualizacion }}</span>
                  <span>Fuente: {{ fuenteActual }}</span>
                </div>
                
                <v-text-field
                  v-model="nuevaTasa"
                  label="Nueva Tasa (BS por $)"
                  type="number"
                  variant="outlined"
                  density="comfortable"
                  dark
                  class="custom-input mb-3"
                  placeholder="Ej: 45.50"
                >
                  <template v-slot:prepend-inner>
                    <span style="color: #4facfe; font-weight: 700;">BS</span>
                  </template>
                  <template v-slot:append-inner>
                    <span style="color: rgba(255,255,255,0.4);">por $</span>
                  </template>
                </v-text-field>
                
                <v-btn color="#ffd54f" block rounded="pill" size="large" @click="actualizarTasaManual" :loading="cargando" elevation="0" class="mb-2 btn-premium">
                  <v-icon start>mdi-refresh</v-icon>Actualizar Manualmente
                </v-btn>
                
                <v-btn color="#4caf50" block rounded="pill" size="large" @click="actualizarTasaBCV" :loading="cargandoBCV" elevation="0" class="btn-premium">
                  <v-icon start>mdi-web</v-icon>Consultar BCV
                </v-btn>
                
                <v-alert type="info" variant="tonal" class="mt-3 rounded-xl" density="compact" border="start">
                  <v-icon start size="16">mdi-information</v-icon>
                  <strong>Importante:</strong> Al cambiar la tasa se recalcularán TODAS las cuotas pendientes.
                </v-alert>
              </v-card-text>
            </v-card>
          </v-col>

          <!-- IMPACTO -->
          <v-col cols="12" md="6">
            <v-card class="glass-card rounded-xl" elevation="0">
              <v-card-title class="text-h6 font-weight-bold text-white pa-4" style="background: linear-gradient(135deg, rgba(76,175,80,0.15), rgba(46,125,50,0.1));">
                <v-icon color="#4caf50" class="mr-2">mdi-chart-bar</v-icon>
                Impacto de la Última Actualización
              </v-card-title>
              <v-card-text class="pa-4">
                <div class="impact-grid">
                  <div class="impact-item glass-effect rounded-lg">
                    <div class="d-flex align-center pa-3">
                      <div class="impact-icon" style="background: rgba(79,172,254,0.15);">
                        <v-icon color="#4facfe">mdi-file-document</v-icon>
                      </div>
                      <div class="ml-3 flex-grow-1">
                        <div class="text-caption" style="color: rgba(255,255,255,0.4);">Financiamientos Activos</div>
                        <div class="text-h6 text-white font-weight-bold">{{ stats.financiamientos_activos }}</div>
                      </div>
                    </div>
                  </div>
                  
                  <div class="impact-item glass-effect rounded-lg mt-2">
                    <div class="d-flex align-center pa-3">
                      <div class="impact-icon" style="background: rgba(255,213,79,0.15);">
                        <v-icon color="#ffd54f">mdi-clock-outline</v-icon>
                      </div>
                      <div class="ml-3 flex-grow-1">
                        <div class="text-caption" style="color: rgba(255,255,255,0.4);">Cuotas Pendientes</div>
                        <div class="text-h6 text-white font-weight-bold">{{ stats.cuotas_pendientes }}</div>
                      </div>
                    </div>
                  </div>
                  
                  <div class="impact-item glass-effect rounded-lg mt-2">
                    <div class="d-flex align-center pa-3">
                      <div class="impact-icon" style="background: rgba(76,175,80,0.15);">
                        <v-icon color="#4caf50">mdi-currency-usd</v-icon>
                      </div>
                      <div class="ml-3 flex-grow-1">
                        <div class="text-caption" style="color: rgba(255,255,255,0.4);">Total Cartera (USD)</div>
                        <div class="text-h6 text-white font-weight-bold">${{ stats.total_cartera_usd }}</div>
                      </div>
                    </div>
                  </div>
                  
                  <div class="impact-item glass-effect rounded-lg mt-2">
                    <div class="d-flex align-center pa-3">
                      <div class="impact-icon" style="background: rgba(244,67,54,0.15);">
                        <v-icon color="#f44336">mdi-cash</v-icon>
                      </div>
                      <div class="ml-3 flex-grow-1">
                        <div class="text-caption" style="color: rgba(255,255,255,0.4);">Total Cartera (BS)</div>
                        <div class="text-h6 text-white font-weight-bold">BS {{ stats.total_cartera_bs }}</div>
                      </div>
                    </div>
                  </div>
                </div>
              </v-card-text>
            </v-card>
          </v-col>
        </v-row>

        <!-- HISTORIAL -->
        <v-row class="mt-4">
          <v-col cols="12">
            <v-card class="glass-card rounded-xl" elevation="0">
              <v-card-title class="text-h6 font-weight-bold text-white pa-4">
                <v-icon color="#ffd54f" class="mr-2">mdi-history</v-icon>
                Historial de Tasas (Últimas 20)
              </v-card-title>
              <v-card-text class="pa-4 pt-0">
                <div class="table-wrapper">
                  <v-data-table :items="historialTasas" :headers="headersTasas" density="compact" class="premium-table">
                    <template v-slot:item.tasa="{ item }">
                      <strong :class="item.fuente === 'bcv' ? 'text-success' : 'text-warning'">
                        {{ item.tasa }} BS/$
                      </strong>
                    </template>
                    <template v-slot:item.fuente="{ item }">
                      <v-chip :color="item.fuente === 'bcv' ? 'success' : 'warning'" size="x-small" variant="flat">
                        {{ item.fuente }}
                      </v-chip>
                    </template>
                    <template v-slot:item.fecha="{ item }">
                      <span class="text-white">{{ formatearFecha(item.fecha) }}</span>
                    </template>
                  </v-data-table>
                </div>
                <div v-if="historialTasas.length === 0" class="empty-state glass-effect rounded-xl mt-2">
                  <v-icon size="32" color="rgba(255,255,255,0.1)">mdi-history</v-icon>
                  <div class="text-caption" style="color: rgba(255,255,255,0.3);">Sin historial de tasas</div>
                </div>
              </v-card-text>
            </v-card>
          </v-col>
        </v-row>
      </v-col>
    </v-row>
  </v-container>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { api } from '@/config/api'

const tasaActual = ref(40.0)
const nuevaTasa = ref(40.0)
const fechaActualizacion = ref('')
const fuenteActual = ref('manual')
const cargando = ref(false)
const cargandoBCV = ref(false)
const stats = ref({ financiamientos_activos: 0, cuotas_pendientes: 0, total_cartera_usd: 0, total_cartera_bs: 0 })
const historialTasas = ref([])

const headersTasas = [
  { title: 'Tasa', key: 'tasa' },
  { title: 'Fecha', key: 'fecha' },
  { title: 'Fuente', key: 'fuente' }
]

const cargarTasa = async () => {
  try {
    const data = await api.get('/config/tasa-dolar')
    tasaActual.value = data.tasa; nuevaTasa.value = data.tasa
    fechaActualizacion.value = formatearFecha(data.fecha)
    if (data.historial?.length > 0) { fuenteActual.value = data.historial[0].fuente; historialTasas.value = data.historial }
  } catch (e) {}
}

const actualizarTasaManual = async () => {
  if (!nuevaTasa.value || nuevaTasa.value <= 0) { alert('Ingrese una tasa válida'); return }
  if (parseFloat(nuevaTasa.value) === parseFloat(tasaActual.value)) { alert('La tasa es igual a la actual'); return }
  if (!confirm(`¿Actualizar tasa a ${nuevaTasa.value} BS/$?`)) return
  cargando.value = true
  try {
    const data = await api.post('/config/tasa-dolar', { tasa: parseFloat(nuevaTasa.value), actualizado_por: "admin" })
    alert(data.mensaje); await cargarTasa(); await cargarStats()
  } catch (e) { alert('Error actualizando tasa') }
  finally { cargando.value = false }
}

const actualizarTasaBCV = async () => {
  cargandoBCV.value = true
  try {
    const data = await api.post('/config/tasa-dolar/bcv')
    if (data.error) { alert(data.mensaje); return }
    alert(data.mensaje); await cargarTasa(); await cargarStats()
  } catch (e) { alert('Error consultando BCV') }
  finally { cargandoBCV.value = false }
}

const cargarStats = async () => {
  try {
    const financiamientos = await api.get('/financiamientos')
    const activos = financiamientos.filter(f => f.estado === 'activo')
    stats.value.financiamientos_activos = activos.length
    let cp = 0, cusd = 0, cbs = 0
    for (const f of activos) {
      const cuotas = await api.get(`/financiamientos/${f.id}/cuotas`)
      const pendientes = cuotas.filter(c => c.estado === 'pendiente')
      cp += pendientes.length
      cusd += pendientes.reduce((s, c) => s + (c.monto_total_usd || 0), 0)
      cbs += pendientes.reduce((s, c) => s + (c.monto_total_bs || 0), 0)
    }
    stats.value.cuotas_pendientes = cp
    stats.value.total_cartera_usd = cusd.toFixed(2)
    stats.value.total_cartera_bs = cbs.toFixed(2)
  } catch (e) {}
}

const formatearFecha = (f) => f ? new Date(f).toLocaleString('es-VE', { day: '2-digit', month: '2-digit', year: 'numeric', hour: '2-digit', minute: '2-digit' }) : ''

onMounted(() => { cargarTasa(); cargarStats() })
</script>

<style scoped>
.background-gradient { position: fixed; top: 0; left: 0; right: 0; bottom: 0; background: radial-gradient(ellipse at 20% 50%, rgba(79,172,254,0.12), transparent 70%), radial-gradient(ellipse at 80% 50%, rgba(99,102,241,0.08), transparent 70%), #0a0e1a; z-index: 0; }
.header-premium { position: relative; z-index: 1; padding: 16px 24px; background: rgba(255,255,255,0.05); backdrop-filter: blur(20px); border-radius: 20px; border: 1px solid rgba(255,255,255,0.06); }
.icon-wrapper { width: 48px; height: 48px; background: linear-gradient(135deg, #4facfe, #6366f1); border-radius: 14px; display: flex; align-items: center; justify-content: center; }
.pulse-animation { animation: pulse 2s infinite; }
@keyframes pulse { 0%, 100% { transform: scale(1); } 50% { transform: scale(1.05); } }
.step-chip { background: rgba(255,255,255,0.08) !important; padding: 8px 16px !important; border-radius: 50px !important; }
.glass-effect { background: rgba(255,255,255,0.05) !important; backdrop-filter: blur(16px) !important; border: 1px solid rgba(255,255,255,0.08) !important; border-radius: 12px !important; }
.glass-card { background: rgba(255,255,255,0.03) !important; backdrop-filter: blur(24px) !important; border: 1px solid rgba(255,255,255,0.06) !important; border-radius: 24px !important; }

.tasa-display { padding: 16px; }
.tasa-number { font-size: 4rem; font-weight: 800; color: #4facfe; line-height: 1; }
.tasa-label { font-size: 1rem; color: rgba(255,255,255,0.4); text-transform: uppercase; letter-spacing: 2px; margin-top: 4px; }

.custom-input :deep(.v-field) { background: rgba(255,255,255,0.05) !important; border-radius: 12px !important; border: 1px solid rgba(255,255,255,0.08) !important; }
.custom-input :deep(.v-field--focused) { border-color: #4facfe !important; }
.custom-input :deep(.v-label) { color: rgba(255,255,255,0.5) !important; }
.custom-input :deep(.v-field__input) { color: white !important; }
.custom-input :deep(.v-field__input::placeholder) { color: rgba(255,255,255,0.5) !important; font-weight: 500 !important; }

.btn-premium { font-weight: 700 !important; transition: all 0.3s ease !important; }
.btn-premium:hover { transform: translateY(-2px); }

.impact-grid { display: flex; flex-direction: column; }
.impact-icon { width: 44px; height: 44px; border-radius: 12px; display: flex; align-items: center; justify-content: center; }

.table-wrapper { overflow-x: auto; }
.premium-table { background: transparent !important; }
.premium-table :deep(th) { color: rgba(255,255,255,0.7) !important; font-weight: 700 !important; font-size: 0.75rem !important; text-transform: uppercase; padding: 12px 8px !important; border-bottom: 1px solid rgba(255,255,255,0.06) !important; }
.premium-table :deep(td) { color: rgba(255,255,255,0.9) !important; padding: 10px 8px !important; border-bottom: 1px solid rgba(255,255,255,0.03) !important; }
.premium-table :deep(tr:hover) { background: rgba(255,255,255,0.02) !important; }
.text-success { color: #4caf50 !important; }
.text-warning { color: #ffd54f !important; }
.empty-state { padding: 24px; text-align: center; border: 1px dashed rgba(255,255,255,0.08); }

@media (max-width: 600px) {
  .header-premium { flex-direction: column; gap: 12px; align-items: stretch !important; }
  .tasa-number { font-size: 3rem; }
}
</style>