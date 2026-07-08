<template>
  <v-row>
    <v-col cols="12">
      <h1 class="text-h4 mb-4">⚙️ Configuración del Sistema</h1>
    </v-col>
    
    <!-- TASA DEL DÓLAR -->
    <v-col cols="12" md="6">
      <v-card color="primary" dark>
        <v-card-title>💰 Tasa del Dólar</v-card-title>
        <v-card-text>
          <div class="text-h2 text-center mb-4">
            {{ tasaActual }} <span class="text-h6">BS/$</span>
          </div>
          <div class="text-caption text-center mb-4">
            Última actualización: {{ fechaActualizacion }}
          </div>
          <div class="text-caption text-center mb-4">
            Fuente: {{ fuenteActual }}
          </div>
          
          <v-text-field
            v-model="nuevaTasa"
            label="Nueva Tasa (BS por $)"
            type="number"
            prefix="BS"
            suffix="por $"
            variant="outlined"
            bg-color="white"
            class="mb-4"
            color="primary"
          ></v-text-field>
          
          <v-btn 
            color="warning" 
            block 
            size="large"
            @click="actualizarTasaManual"
            :loading="cargando"
          >
            🔄 Actualizar Manualmente
          </v-btn>
          
          <v-btn 
            color="success" 
            block 
            class="mt-2"
            @click="actualizarTasaBCV"
            :loading="cargandoBCV"
          >
            🌐 Consultar BCV
          </v-btn>
          
          <v-alert type="info" class="mt-3" density="compact">
            <strong>⚠️ Importante:</strong><br>
            Al cambiar la tasa se recalculan TODAS las cuotas pendientes 
            para proteger contra la devaluación.
          </v-alert>
        </v-card-text>
      </v-card>
    </v-col>
    
    <!-- IMPACTO -->
    <v-col cols="12" md="6">
      <v-card>
        <v-card-title>📊 Impacto de la Última Actualización</v-card-title>
        <v-card-text>
          <v-list>
            <v-list-item>
              <v-list-item-title>Financiamientos Activos</v-list-item-title>
              <template v-slot:append>
                <v-chip color="primary">{{ stats.financiamientos_activos }}</v-chip>
              </template>
            </v-list-item>
            
            <v-list-item>
              <v-list-item-title>Cuotas Pendientes</v-list-item-title>
              <template v-slot:append>
                <v-chip color="warning">{{ stats.cuotas_pendientes }}</v-chip>
              </template>
            </v-list-item>
            
            <v-list-item>
              <v-list-item-title>Total en Cartera (USD)</v-list-item-title>
              <template v-slot:append>
                <v-chip color="success">${{ stats.total_cartera_usd }}</v-chip>
              </template>
            </v-list-item>
            
            <v-list-item>
              <v-list-item-title>Total en Cartera (BS)</v-list-item-title>
              <template v-slot:append>
                <v-chip color="info">BS {{ stats.total_cartera_bs }}</v-chip>
              </template>
            </v-list-item>
          </v-list>
        </v-card-text>
      </v-card>
    </v-col>
    
    <!-- HISTORIAL -->
    <v-col cols="12">
      <v-card>
        <v-card-title>📈 Historial de Tasas (Últimas 20)</v-card-title>
        <v-card-text>
          <v-data-table
            :items="historialTasas"
            :headers="headersTasas"
            density="compact"
          >
            <template v-slot:item.tasa="{ item }">
              <strong :class="item.fuente === 'bcv' ? 'text-success' : 'text-warning'">
                {{ item.tasa }} BS/$
              </strong>
            </template>
            
            <template v-slot:item.fuente="{ item }">
              <v-chip :color="item.fuente === 'bcv' ? 'success' : 'warning'" size="small">
                {{ item.fuente }}
              </v-chip>
            </template>
            
            <template v-slot:item.fecha_actualizacion="{ item }">
              {{ formatearFecha(item.fecha_actualizacion) }}
            </template>
          </v-data-table>
        </v-card-text>
      </v-card>
    </v-col>
  </v-row>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import axios from 'axios'

const API_URL = 'http://localhost:8000'

const tasaActual = ref(40.0)
const nuevaTasa = ref(40.0)
const fechaActualizacion = ref('')
const fuenteActual = ref('manual')
const cargando = ref(false)
const cargandoBCV = ref(false)
const stats = ref({ 
  financiamientos_activos: 0, 
  cuotas_pendientes: 0, 
  total_cartera_usd: 0,
  total_cartera_bs: 0 
})
const historialTasas = ref([])

const headersTasas = [
  { title: 'Tasa', key: 'tasa' },
  { title: 'Fecha', key: 'fecha_actualizacion' },
  { title: 'Fuente', key: 'fuente' },
  { title: 'Actualizado por', key: 'actualizado_por' }
]

const cargarTasa = async () => {
  try {
    const res = await axios.get(`${API_URL}/config/tasa-dolar`)
    tasaActual.value = res.data.tasa
    nuevaTasa.value = res.data.tasa
    fechaActualizacion.value = formatearFecha(res.data.fecha)
    
    if (res.data.historial && res.data.historial.length > 0) {
      fuenteActual.value = res.data.historial[0].fuente
    }
  } catch (e) {
    console.error('Error cargando tasa:', e)
  }
}

const actualizarTasaManual = async () => {
  if (!nuevaTasa.value || nuevaTasa.value <= 0) {
    alert('Ingrese una tasa válida')
    return
  }
  
  if (parseFloat(nuevaTasa.value) === parseFloat(tasaActual.value)) {
    alert('La tasa es igual a la actual')
    return
  }
  
  if (!confirm(`¿Actualizar tasa a ${nuevaTasa.value} BS/$?\n\nEsto recalculará TODAS las cuotas pendientes.`)) {
    return
  }
  
  cargando.value = true
  try {
    const res = await axios.post(`${API_URL}/config/tasa-dolar`, {
      tasa: parseFloat(nuevaTasa.value),
      actualizado_por: "admin"
    })
    
    alert(res.data.mensaje + 
          `\n\nFinanciamientos afectados: ${res.data.financiamientos_afectados}` +
          `\nCuotas recalculadas: ${res.data.cuotas_recalculadas}`)
    
    await cargarTasa()
    await cargarStats()
    await cargarHistorial()
    
  } catch (e) {
    alert('Error actualizando tasa')
    console.error(e)
  } finally {
    cargando.value = false
  }
}

const actualizarTasaBCV = async () => {
  cargandoBCV.value = true
  try {
    const res = await axios.post(`${API_URL}/config/tasa-dolar/bcv`)
    
    if (res.data.error) {
      alert(res.data.mensaje + `\nTasa actual: ${res.data.tasa_actual} BS/$`)
      return
    }
    
    alert(res.data.mensaje + 
          `\nCuotas recalculadas: ${res.data.cuotas_recalculadas}`)
    
    await cargarTasa()
    await cargarStats()
    await cargarHistorial()
    
  } catch (e) {
    alert('Error consultando BCV')
    console.error(e)
  } finally {
    cargandoBCV.value = false
  }
}

const cargarStats = async () => {
  try {
    const fin = await axios.get(`${API_URL}/financiamientos`)
    const activos = fin.data.filter(f => f.estado === 'activo')
    stats.value.financiamientos_activos = activos.length
    
    let cuotasPendientes = 0
    let totalCarteraUSD = 0
    let totalCarteraBS = 0
    
    for (const f of activos) {
      const cuotas = await axios.get(`${API_URL}/financiamientos/${f.id}/cuotas`)
      const pendientes = cuotas.data.filter(c => c.estado === 'pendiente')
      cuotasPendientes += pendientes.length
      totalCarteraUSD += pendientes.reduce((sum, c) => sum + (c.monto_total_usd || 0), 0)
      totalCarteraBS += pendientes.reduce((sum, c) => sum + (c.monto_total_bs || 0), 0)
    }
    
    stats.value.cuotas_pendientes = cuotasPendientes
    stats.value.total_cartera_usd = totalCarteraUSD.toFixed(2)
    stats.value.total_cartera_bs = totalCarteraBS.toFixed(2)
  } catch (e) {
    console.error('Error cargando stats:', e)
  }
}

const cargarHistorial = async () => {
  try {
    const res = await axios.get(`${API_URL}/config/historial-tasas`)
    historialTasas.value = res.data
  } catch (e) {
    console.error('Error cargando historial:', e)
  }
}

const formatearFecha = (fechaStr) => {
  if (!fechaStr) return ''
  const fecha = new Date(fechaStr)
  return fecha.toLocaleString('es-VE', {
    day: '2-digit',
    month: '2-digit',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit'
  })
}

onMounted(() => {
  cargarTasa()
  cargarStats()
  cargarHistorial()
})
</script>