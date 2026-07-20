<template>
  <v-container fluid class="pa-0">
    <div class="background-gradient"></div>

    <v-row class="ma-0">
      <v-col cols="12" class="pa-4">
        <!-- HEADER -->
        <div class="header-premium d-flex align-center justify-space-between flex-wrap">
          <div class="d-flex align-center">
            <div class="icon-wrapper pulse-animation">
              <v-icon size="32" color="white">mdi-trophy</v-icon>
            </div>
            <div class="ml-3">
              <h1 class="text-h4 font-weight-bold text-white">Niveles de Financiamiento</h1>
              <p class="text-subtitle-2 text-white" style="opacity: 0.7;">Configuración de niveles por score crediticio</p>
            </div>
          </div>
          <v-btn 
            color="#FFD700" 
            size="small"
            @click="resetNiveles"
            :loading="cargandoReset"
            class="rounded-xl"
          >
            <v-icon start>mdi-refresh</v-icon>
            Restaurar Default
          </v-btn>
        </div>

        <!-- ALERTAS -->
        <div class="mt-4">
          <v-alert v-if="errorMsg" type="error" class="rounded-xl" dismissible @click:close="errorMsg = ''">
            <v-icon start>mdi-alert-circle</v-icon>
            {{ errorMsg }}
          </v-alert>
          <v-alert v-if="successMsg" type="success" class="rounded-xl" dismissible @click:close="successMsg = ''">
            <v-icon start>mdi-check-circle</v-icon>
            {{ successMsg }}
          </v-alert>
        </div>

        <!-- TABLA -->
        <v-row class="mt-4">
          <v-col cols="12">
            <v-card class="glass-card rounded-xl" elevation="0">
              <v-card-text class="pa-4">
                <div class="table-wrapper">
                  <v-table class="premium-table">
                    <thead>
                      <tr>
                        <th class="text-left" style="color: rgba(255,255,255,0.8); font-weight: 700;">Nivel</th>
                        <th class="text-left" style="color: rgba(255,255,255,0.8); font-weight: 700;">Score</th>
                        <th class="text-right" style="color: rgba(255,255,255,0.8); font-weight: 700;">
                          <div>Límite USD</div>
                          <div style="font-weight: 600; font-size: 0.75rem; color: #000000; text-align: center;">Monto máximo</div>
                        </th>
                        <th class="text-right" style="color: rgba(255,255,255,0.8); font-weight: 700;">
                          <div>Entrada %</div>
                          <div style="font-weight: 600; font-size: 0.75rem; color: #000000; text-align: center;">Pago inicial</div>
                        </th>
                        <th class="text-right" style="color: rgba(255,255,255,0.8); font-weight: 700;">
                          <div>Financia %</div>
                          <div style="font-weight: 600; font-size: 0.75rem; color: #000000; text-align: center;">Saldo a financiar</div>
                        </th>
                        <th class="text-center" style="color: rgba(255,255,255,0.8); font-weight: 700;">
                          <div>Cuotas Base</div>
                          <div style="font-weight: 600; font-size: 0.75rem; color: #000000; text-align: center;">Mínimo</div>
                        </th>
                        <th class="text-center" style="color: rgba(255,255,255,0.8); font-weight: 700;">
                          <div>Cuotas Máx</div>
                          <div style="font-weight: 600; font-size: 0.75rem; color: #000000; text-align: center;">Máximo</div>
                        </th>
                        <th class="text-right" style="color: rgba(255,255,255,0.8); font-weight: 700;">
                          <div>Mora %</div>
                          <div style="font-weight: 600; font-size: 0.75rem; color: #000000; text-align: center;">Interés diario</div>
                        </th>
                        <th class="text-center" style="color: rgba(255,255,255,0.8); font-weight: 700;">Aprobación</th>
                        <th class="text-center" style="color: rgba(255,255,255,0.8); font-weight: 700;">Acciones</th>
                      </tr>
                    </thead>
                    <tbody>
                      <tr v-for="([nivel, config]) in nivelesOrdenados" :key="nivel">
                        <td>
                          <div class="d-flex align-center">
                            <div class="level-dot" :style="`background: ${nivelColor(nivel)}`"></div>
                            <span class="font-weight-bold" :style="{ color: nivelColor(nivel), fontSize: '0.9rem' }">{{ nivel.toUpperCase() }}</span>
                          </div>
                        </td>
                        <td style="color: rgba(255,255,255,0.9); font-weight: 500;">
                          {{ config.min_score }} - {{ config.max_score }}
                        </td>
                        <td>
                          <v-text-field
                            v-model="config.monto_max_usd"
                            type="number"
                            density="compact"
                            hide-details
                            variant="outlined"
                            class="premium-input"
                            bg-color="white"
                          >
                            <template v-slot:prepend-inner>
                              <span style="color: #666; font-weight: 600;">$</span>
                            </template>
                          </v-text-field>
                        </td>
                        <td>
                          <v-text-field
                            v-model="config.entrada_pct"
                            @update:model-value="actualizarEntrada(nivel, $event)"
                            type="number"
                            density="compact"
                            hide-details
                            variant="outlined"
                            class="premium-input"
                            bg-color="white"
                            min="0"
                            max="100"
                            step="1"
                          >
                            <template v-slot:append-inner>
                              <span style="color: #666; font-weight: 600;">%</span>
                            </template>
                          </v-text-field>
                        </td>
                        <td>
                          <v-text-field
                            v-model="config.financia_pct"
                            @update:model-value="actualizarFinancia(nivel, $event)"
                            type="number"
                            density="compact"
                            hide-details
                            variant="outlined"
                            class="premium-input"
                            bg-color="white"
                            min="0"
                            max="100"
                            step="1"
                          >
                            <template v-slot:append-inner>
                              <span style="color: #666; font-weight: 600;">%</span>
                            </template>
                          </v-text-field>
                        </td>
                        <td>
                          <v-text-field
                            v-model="config.cuotas_base"
                            type="number"
                            density="compact"
                            hide-details
                            variant="outlined"
                            class="premium-input"
                            bg-color="white"
                            min="1"
                          ></v-text-field>
                        </td>
                        <td>
                          <v-text-field
                            v-model="config.cuotas_max"
                            type="number"
                            density="compact"
                            hide-details
                            variant="outlined"
                            class="premium-input"
                            bg-color="white"
                            min="1"
                          ></v-text-field>
                        </td>
                        <td>
                          <v-text-field
                            v-model="config.mora_diaria"
                            type="number"
                            density="compact"
                            hide-details
                            variant="outlined"
                            class="premium-input"
                            bg-color="white"
                            step="0.1"
                            min="0"
                          >
                            <template v-slot:append-inner>
                              <span style="color: #666; font-weight: 600;">%</span>
                            </template>
                          </v-text-field>
                        </td>
                        <td class="text-center">
                          <v-checkbox
                            v-model="config.aprobacion_extra"
                            density="compact"
                            hide-details
                            color="#4facfe"
                          ></v-checkbox>
                        </td>
                        <td class="text-center">
                          <v-btn 
                            color="#4caf50" 
                            size="small"
                            @click="guardarNivel(nivel)"
                            :loading="cargandoNivel === nivel"
                            class="rounded-xl"
                          >
                            <v-icon size="18" color="white">mdi-content-save</v-icon>
                          </v-btn>
                        </td>
                      </tr>
                    </tbody>
                  </v-table>
                </div>
              </v-card-text>
            </v-card>
          </v-col>
        </v-row>

        <!-- RESUMEN VISUAL -->
        <v-row class="mt-4">
          <v-col cols="12">
            <v-card class="glass-card rounded-xl" elevation="0">
              <v-card-title class="text-h6 font-weight-bold text-white pa-4">
                <v-icon color="#FFD700" class="mr-2">mdi-chart-pie</v-icon>
                Resumen de Límites por Nivel
              </v-card-title>
              <v-card-text class="pa-4">
                <v-row>
                  <v-col 
                    v-for="([nivel, config]) in nivelesOrdenados" 
                    :key="nivel"
                    cols="6" 
                    sm="4" 
                    md="3" 
                    lg="2"
                  >
                    <div class="level-summary-card" :style="`border-color: ${nivelColor(nivel)}`">
                      <div class="level-summary-icon" :style="`background: ${nivelColor(nivel)}30`">
                        <v-icon :color="nivelColor(nivel)">{{ nivelIcono(nivel) }}</v-icon>
                      </div>
                      <div class="level-summary-name" :style="{ color: nivelColor(nivel) }">{{ nivel.toUpperCase() }}</div>
                      <div class="level-summary-amount text-white">${{ config.monto_max_usd }}</div>
                      <div class="level-summary-label" style="color: rgba(255,255,255,0.3); font-size: 0.5rem; text-transform: uppercase; letter-spacing: 0.5px;">Límite máximo</div>
                      <div class="level-summary-details" style="color: rgba(255,255,255,0.6); margin-top: 8px;">
                        <div>
                          <span style="color: #4caf50; font-weight: 600;">{{ config.entrada_pct }}%</span>
                          <span style="color: rgba(255,255,255,0.3); font-size: 0.5rem; display: block;">ENTRADA</span>
                        </div>
                        <div style="margin-top: 4px;">
                          <span style="color: #ffd54f; font-weight: 600;">{{ config.financia_pct }}%</span>
                          <span style="color: rgba(255,255,255,0.3); font-size: 0.5rem; display: block;">FINANCIA</span>
                        </div>
                      </div>
                      <div class="level-summary-details" style="color: rgba(255,255,255,0.4); font-size: 0.6rem; margin-top: 6px;">
                        <span>{{ config.cuotas_base }}-{{ config.cuotas_max }} cuotas</span>
                        <span style="color: rgba(255,255,255,0.2); font-size: 0.5rem; display: block;">MORA: {{ config.mora_diaria }}%</span>
                      </div>
                    </div>
                  </v-col>
                </v-row>
              </v-card-text>
            </v-card>
          </v-col>
        </v-row>
      </v-col>
    </v-row>
  </v-container>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue'
import { api } from '@/config/api'

const niveles = ref({})
const cargandoNivel = ref('')
const cargandoReset = ref(false)
const errorMsg = ref('')
const successMsg = ref('')

const nivelesOrdenados = computed(() => {
  const entries = Object.entries(niveles.value)
  return entries.sort((a, b) => a[1].min_score - b[1].min_score)
})

const nivelColor = (nivel) => {
  const colores = { 
    nuevo: '#78909C', 
    bronce: '#A1887F', 
    plata: '#90A4AE', 
    oro: '#FFD54F', 
    platino: '#7E57C2' 
  }
  return colores[nivel] || '#78909C'
}

const nivelIcono = (nivel) => {
  const iconos = { 
    nuevo: 'mdi-star-outline', 
    bronce: 'mdi-medal-outline', 
    plata: 'mdi-silverware', 
    oro: 'mdi-gold', 
    platino: 'mdi-diamond-stone'
  }
  return iconos[nivel] || 'mdi-star'
}

const actualizarEntrada = (nivel, valor) => {
  const config = niveles.value[nivel]
  let entrada = parseInt(valor) || 0
  entrada = Math.min(100, Math.max(0, entrada))
  config.entrada_pct = entrada
  config.financia_pct = 100 - entrada
}

const actualizarFinancia = (nivel, valor) => {
  const config = niveles.value[nivel]
  let financia = parseInt(valor) || 0
  financia = Math.min(100, Math.max(0, financia))
  config.financia_pct = financia
  config.entrada_pct = 100 - financia
}

const cargarNiveles = async () => {
  try {
    const data = await api.get('/config/niveles')
    niveles.value = data.niveles
    console.log('📥 Niveles cargados:', JSON.stringify(niveles.value, null, 2))
  } catch (e) {
    console.error('Error cargando niveles:', e)
    errorMsg.value = 'Error cargando configuración de niveles'
  }
}

const guardarNivel = async (nivel) => {
  cargandoNivel.value = nivel
  errorMsg.value = ''
  successMsg.value = ''
  
  try {
    const config = niveles.value[nivel]
    
    // ✅ VALIDAR SUMA = 100%
    const entrada = parseInt(config.entrada_pct) || 0
    const financia = parseInt(config.financia_pct) || 0
    
    if (entrada + financia !== 100) {
      errorMsg.value = `❌ La suma de entrada (${entrada}%) + financiamiento (${financia}%) debe ser 100%`
      cargandoNivel.value = ''
      return
    }
    
    // ✅ ENVIAR COMO ENTEROS (el backend espera 50, 50)
    const payload = {
      monto_max_usd: parseFloat(config.monto_max_usd) || 100,
      entrada_pct: parseInt(entrada),   // ✅ ENTERO
      financia_pct: parseInt(financia), // ✅ ENTERO
      cuotas_base: parseInt(config.cuotas_base) || 3,
      cuotas_max: parseInt(config.cuotas_max) || 6,
      mora_diaria: parseFloat(config.mora_diaria) || 2,
      aprobacion_extra: config.aprobacion_extra || false
    }
    
    console.log(`📤 Guardando ${nivel}:`, JSON.stringify(payload, null, 2))
    
    await api.put(`/config/niveles/${nivel}`, payload)
    
    successMsg.value = `✅ Nivel ${nivel.toUpperCase()} actualizado correctamente`
    await cargarNiveles()
    
  } catch (e) {
    console.error(`❌ Error guardando ${nivel}:`, e)
    
    let errorDetail = 'Error guardando nivel'
    if (e.response?.data?.detail) {
      errorDetail = e.response.data.detail
    } else if (e.response?.data?.message) {
      errorDetail = e.response.data.message
    } else if (e.message) {
      errorDetail = e.message
    }
    
    errorMsg.value = `❌ ${errorDetail}`
    
  } finally {
    cargandoNivel.value = ''
  }
}

const resetNiveles = async () => {
  if (!confirm('¿Está seguro de restaurar los valores por defecto?\n\nSe perderán todos los cambios personalizados.')) {
    return
  }
  
  cargandoReset.value = true
  errorMsg.value = ''
  successMsg.value = ''
  
  try {
    await api.post('/config/niveles/reset')
    successMsg.value = '✅ Niveles restaurados a valores por defecto'
    await cargarNiveles()
  } catch (e) {
    console.error('Error restaurando niveles:', e)
    errorMsg.value = 'Error restaurando niveles'
  } finally {
    cargandoReset.value = false
  }
}

onMounted(cargarNiveles)
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

/* ✅ GLASS EFFECT */
.glass-effect {
  background: rgba(255, 255, 255, 0.05) !important;
  backdrop-filter: blur(16px) !important;
  border: 1px solid rgba(255, 255, 255, 0.08) !important;
}

.glass-card {
  background: rgba(255, 255, 255, 0.03) !important;
  backdrop-filter: blur(24px) !important;
  border: 1px solid rgba(255, 255, 255, 0.06) !important;
  border-radius: 24px !important;
}

.rounded-xl {
  border-radius: 16px !important;
  overflow: hidden;
}

/* ✅ TABLA PREMIUM */
.table-wrapper {
  overflow-x: auto;
}

.premium-table {
  width: 100%;
  border-collapse: collapse;
}

.premium-table thead th {
  background: rgba(255, 255, 255, 0.03) !important;
  padding: 12px 8px !important;
  border-bottom: 1px solid rgba(255, 255, 255, 0.05) !important;
}

.premium-table tbody td {
  padding: 8px 6px !important;
  border-bottom: 1px solid rgba(255, 255, 255, 0.03) !important;
}

.premium-table tbody tr:hover {
  background: rgba(255, 255, 255, 0.02) !important;
}

.level-dot {
  width: 10px;
  height: 10px;
  border-radius: 50%;
  margin-right: 10px;
  flex-shrink: 0;
}

/* ✅ INPUTS PREMIUM */
.premium-input :deep(.v-field) {
  background: #ffffff !important;
  border-radius: 10px !important;
  border: 1px solid rgba(0, 0, 0, 0.1) !important;
}

.premium-input :deep(.v-field--focused) {
  border-color: #4facfe !important;
  box-shadow: 0 0 0 3px rgba(79, 172, 254, 0.2) !important;
}

.premium-input :deep(.v-field__input) {
  color: #000000 !important;
  font-size: 0.9rem !important;
  font-weight: 600 !important;
}

.premium-input input {
  color: #000000 !important;
  -webkit-text-fill-color: #000000 !important;
}

.premium-input :deep(.v-field__prepend-inner),
.premium-input :deep(.v-field__append-inner) {
  color: #666 !important;
}

/* ✅ RESUMEN DE NIVELES */
.level-summary-card {
  background: rgba(255, 255, 255, 0.05);
  border-radius: 16px;
  padding: 16px;
  text-align: center;
  border: 2px solid rgba(255, 255, 255, 0.05);
  transition: all 0.3s ease;
}

.level-summary-card:hover {
  transform: translateY(-4px);
  background: rgba(255, 255, 255, 0.08);
  border-color: rgba(255, 255, 255, 0.15);
}

.level-summary-icon {
  width: 48px;
  height: 48px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  margin: 0 auto 8px;
}

.level-summary-name {
  font-size: 0.7rem;
  text-transform: uppercase;
  letter-spacing: 1px;
  font-weight: 700;
}

.level-summary-amount {
  font-size: 1.5rem;
  font-weight: 800;
}

.level-summary-label {
  font-size: 0.5rem;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  margin-top: -2px;
}

.level-summary-details {
  font-size: 0.65rem;
  margin-top: 4px;
}

/* ✅ RESPONSIVE */
@media (max-width: 600px) {
  .header-premium {
    flex-direction: column;
    gap: 12px;
    align-items: stretch !important;
  }
  
  .premium-table thead th,
  .premium-table tbody td {
    font-size: 0.7rem !important;
    padding: 4px !important;
  }
  
  .level-summary-card {
    padding: 12px;
  }
  
  .level-summary-amount {
    font-size: 1.2rem;
  }
}
</style>