<template>
  <v-container>
    <v-row>
      <v-col cols="12">
        <h1 class="text-h4 mb-4">🏆 Niveles de Financiamiento</h1>
        <p class="text-body-2 text-grey mb-4">
          Configure los límites, porcentajes y cuotas para cada nivel de cliente
        </p>
      </v-col>
      
      <!-- Tabla de Niveles -->
      <v-col cols="12">
        <v-card class="rounded-xl" elevation="2">
          <v-card-title class="d-flex align-center pa-4 bg-primary-lighten-5">
            <span class="text-h6">Configuración por Nivel</span>
            <v-spacer></v-spacer>
            <v-btn 
              color="warning" 
              size="small"
              @click="resetNiveles"
              :loading="cargandoReset"
              class="rounded-xl"
            >
              <v-icon start>mdi-refresh</v-icon>
              Restaurar Default
            </v-btn>
          </v-card-title>
          
          <v-card-text class="pa-4">
            <!-- ✅ MOSTRAR ERRORES -->
            <v-alert v-if="errorMsg" type="error" class="mb-3" dismissible @click:close="errorMsg = ''">
              {{ errorMsg }}
            </v-alert>
            <v-alert v-if="successMsg" type="success" class="mb-3" dismissible @click:close="successMsg = ''">
              {{ successMsg }}
            </v-alert>

            <v-table class="rounded-lg">
              <thead>
                <tr>
                  <th class="text-left">Nivel</th>
                  <th class="text-left">Score</th>
                  <th class="text-right">Límite USD</th>
                  <th class="text-right">Entrada %</th>
                  <th class="text-right">Financia %</th>
                  <th class="text-center">Cuotas Base</th>
                  <th class="text-center">Cuotas Máx</th>
                  <th class="text-right">Mora %</th>
                  <th class="text-center">Aprobación</th>
                  <th class="text-center">Acciones</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="([nivel, config]) in nivelesOrdenados" :key="nivel">
                  <td>
                    <v-chip :color="nivelColor(nivel)" size="small" class="font-weight-bold">
                      {{ nivel.toUpperCase() }}
                    </v-chip>
                  </td>
                  <td>
                    {{ config.min_score }} - {{ config.max_score }}
                  </td>
                  <td>
                    <v-text-field
                      v-model="config.monto_max_usd"
                      type="number"
                      density="compact"
                      hide-details
                      variant="outlined"
                      prefix="$"
                      class="mt-2"
                    ></v-text-field>
                  </td>
                  <td>
                    <v-text-field
                      v-model="config.entrada_pct"
                      type="number"
                      density="compact"
                      hide-details
                      variant="outlined"
                      suffix="%"
                      class="mt-2"
                    ></v-text-field>
                  </td>
                  <td>
                    <v-text-field
                      v-model="config.financia_pct"
                      type="number"
                      density="compact"
                      hide-details
                      variant="outlined"
                      suffix="%"
                      class="mt-2"
                    ></v-text-field>
                  </td>
                  <td>
                    <v-text-field
                      v-model="config.cuotas_base"
                      type="number"
                      density="compact"
                      hide-details
                      variant="outlined"
                      class="mt-2"
                    ></v-text-field>
                  </td>
                  <td>
                    <v-text-field
                      v-model="config.cuotas_max"
                      type="number"
                      density="compact"
                      hide-details
                      variant="outlined"
                      class="mt-2"
                    ></v-text-field>
                  </td>
                  <td>
                    <v-text-field
                      v-model="config.mora_diaria"
                      type="number"
                      density="compact"
                      hide-details
                      variant="outlined"
                      suffix="%"
                      class="mt-2"
                    ></v-text-field>
                  </td>
                  <td class="text-center">
                    <v-checkbox
                      v-model="config.aprobacion_extra"
                      density="compact"
                      hide-details
                    ></v-checkbox>
                  </td>
                  <td class="text-center">
                    <v-btn 
                      color="success" 
                      size="small"
                      @click="guardarNivel(nivel)"
                      :loading="cargandoNivel === nivel"
                      class="rounded-xl"
                    >
                      <v-icon size="18">mdi-content-save</v-icon>
                    </v-btn>
                  </td>
                </tr>
              </tbody>
            </v-table>
          </v-card-text>
        </v-card>
      </v-col>
      
      <!-- Resumen Visual -->
      <v-col cols="12" class="mt-4">
        <v-card class="rounded-xl" color="primary" dark>
          <v-card-title class="pa-4">📊 Resumen de Límites</v-card-title>
          <v-card-text class="pa-4">
            <v-row>
              <v-col 
                v-for="([nivel, config]) in nivelesOrdenados" 
                :key="nivel"
                cols="12" 
                sm="6" 
                md="4" 
                lg="2"
              >
                <v-card 
                  :color="nivelColor(nivel)" 
                  dark 
                  class="text-center rounded-xl"
                  elevation="2"
                >
                  <v-card-text class="pa-3">
                    <div class="text-h6 font-weight-bold">{{ nivel.toUpperCase() }}</div>
                    <div class="text-h4">${{ config.monto_max_usd }}</div>
                    <div class="text-caption" style="opacity: 0.8;">Límite máximo</div>
                    <v-divider class="my-2" style="border-color: rgba(255,255,255,0.2);"></v-divider>
                    <div class="text-body-2">
                      Entrada: {{ config.entrada_pct }}%<br>
                      Cuotas: {{ config.cuotas_base }}-{{ config.cuotas_max }}
                    </div>
                  </v-card-text>
                </v-card>
              </v-col>
            </v-row>
          </v-card-text>
        </v-card>
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

// 🔥 ORDENAR: "nuevo" primero, luego por min_score
const nivelesOrdenados = computed(() => {
  const entries = Object.entries(niveles.value)
  return entries.sort((a, b) => a[1].min_score - b[1].min_score)
})

const nivelColor = (nivel) => {
  const colores = { 
    nuevo: 'grey darken-2', 
    bronce: 'brown darken-2', 
    plata: 'blue-grey darken-2', 
    oro: 'amber darken-2', 
    platino: 'deep-purple darken-2' 
  }
  return colores[nivel] || 'grey'
}

const cargarNiveles = async () => {
  try {
    const data = await api.get('/config/niveles')
    niveles.value = data.niveles
    console.log('📥 Niveles cargados:', niveles.value)
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
    
    // ✅ SOLO ENVIAR LOS CAMPOS QUE ESPERA EL BACKEND
    // NO incluir min_score, max_score, creado_en, actualizado_en, id
    const payload = {
      monto_max_usd: parseFloat(config.monto_max_usd) || 100,
      entrada_pct: parseFloat(config.entrada_pct) || 30,
      financia_pct: parseFloat(config.financia_pct) || 70,
      cuotas_base: parseInt(config.cuotas_base) || 3,
      cuotas_max: parseInt(config.cuotas_max) || 6,
      mora_diaria: parseFloat(config.mora_diaria) || 2,
      aprobacion_extra: config.aprobacion_extra || false
    }
    
    console.log(`📤 Guardando ${nivel}:`, payload)
    
    const response = await api.put(`/config/niveles/${nivel}`, payload)
    
    console.log(`✅ Respuesta para ${nivel}:`, response)
    successMsg.value = `✅ Nivel ${nivel.toUpperCase()} actualizado correctamente`
    
    // Recargar datos para asegurar consistencia
    await cargarNiveles()
    
  } catch (e) {
    console.error(`❌ Error guardando ${nivel}:`, e)
    
    // Mostrar mensaje de error más detallado
    let errorDetail = 'Error guardando nivel'
    if (e.response) {
      console.error('❌ Response status:', e.response.status)
      console.error('❌ Response data:', e.response.data)
      
      if (e.response.data?.detail) {
        errorDetail = e.response.data.detail
      } else if (e.response.data?.message) {
        errorDetail = e.response.data.message
      } else {
        errorDetail = `Error ${e.response.status}: ${JSON.stringify(e.response.data)}`
      }
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
.rounded-xl {
  border-radius: 16px !important;
  overflow: hidden;
}

.v-table {
  border-radius: 12px !important;
  overflow: hidden;
}

.v-table thead th {
  background: rgba(0, 0, 0, 0.03) !important;
  font-weight: 600 !important;
  font-size: 0.75rem !important;
  text-transform: uppercase !important;
  letter-spacing: 0.5px !important;
  color: rgba(0,0,0,0.6) !important;
}

.v-alert {
  border-radius: 12px !important;
}
</style>