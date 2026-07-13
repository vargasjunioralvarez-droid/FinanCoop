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
        <v-card>
          <v-card-title class="d-flex align-center">
            <span>Configuración por Nivel</span>
            <v-spacer></v-spacer>
            <v-btn 
              color="warning" 
              size="small"
              @click="resetNiveles"
              :loading="cargandoReset"
            >
              <v-icon start>mdi-refresh</v-icon>
              Restaurar Default
            </v-btn>
          </v-card-title>
          
          <v-card-text>
            <v-table>
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
                <!-- 🔥 nivelesOrdenados asegura el orden correcto -->
                <tr v-for="([nivel, config], index) in nivelesOrdenados" :key="nivel">
                  <td>
                    <v-chip :color="colorNivel(nivel)" size="small">
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
                    >
                      <v-icon>mdi-content-save</v-icon>
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
        <v-card color="primary" dark>
          <v-card-title>📊 Resumen de Límites</v-card-title>
          <v-card-text>
            <v-row>
              <v-col 
                v-for="([nivel, config]) in nivelesOrdenados" 
                :key="nivel"
                cols="12" 
                sm="6" 
                md="4" 
                lg="2"
              >
                <v-card :color="colorNivel(nivel)" dark class="text-center">
                  <v-card-text>
                    <div class="text-h6">{{ nivel.toUpperCase() }}</div>
                    <div class="text-h4">${{ config.monto_max_usd }}</div>
                    <div class="text-caption">Límite máximo</div>
                    <v-divider class="my-2"></v-divider>
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

// 🔥 ORDENAR: "nuevo" primero, luego por min_score
const nivelesOrdenados = computed(() => {
  const entries = Object.entries(niveles.value)
  
  // Ordenar por min_score (ascendente)
  return entries.sort((a, b) => {
    return a[1].min_score - b[1].min_score
  })
})

const colorNivel = (nivel) => {
  const colores = { 
    nuevo: 'grey', 
    bronce: 'brown', 
    plata: 'blue', 
    oro: 'amber', 
    platino: 'purple' 
  }
  return colores[nivel] || 'grey'
}

const cargarNiveles = async () => {
  try {
    const data = await api.get('/config/niveles')
    niveles.value = data.niveles
  } catch (e) {
    console.error('Error cargando niveles:', e)
    alert('Error cargando configuración de niveles')
  }
}

const guardarNivel = async (nivel) => {
  cargandoNivel.value = nivel
  try {
    const config = niveles.value[nivel]
    await api.put(`/config/niveles/${nivel}`, {
      monto_max_usd: parseFloat(config.monto_max_usd),
      entrada_pct: parseFloat(config.entrada_pct),
      financia_pct: parseFloat(config.financia_pct),
      cuotas_base: parseInt(config.cuotas_base),
      cuotas_max: parseInt(config.cuotas_max),
      mora_diaria: parseFloat(config.mora_diaria),
      aprobacion_extra: config.aprobacion_extra
    })
    alert(`✅ Nivel ${nivel.toUpperCase()} actualizado correctamente`)
  } catch (e) {
    console.error('Error guardando nivel:', e)
    alert('Error guardando nivel')
  } finally {
    cargandoNivel.value = ''
  }
}

const resetNiveles = async () => {
  if (!confirm('¿Está seguro de restaurar los valores por defecto?\n\nSe perderán todos los cambios personalizados.')) {
    return
  }
  
  cargandoReset.value = true
  try {
    await api.post('/config/niveles/reset')
    alert('✅ Niveles restaurados a valores por defecto')
    await cargarNiveles()
  } catch (e) {
    console.error('Error restaurando niveles:', e)
    alert('Error restaurando niveles')
  } finally {
    cargandoReset.value = false
  }
}

onMounted(cargarNiveles)
</script>