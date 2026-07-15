<template>
  <v-row>
    <v-col cols="12">
      <h1 class="text-h4 mb-4">💰 Conciliación de Pagos</h1>
    </v-col>
    
    <!-- Pagos Pendientes -->
    <v-col cols="12">
      <v-card>
        <v-card-title>
          Pagos Pendientes de Conciliación
          <v-spacer></v-spacer>
          <v-chip color="warning">{{ pagosPendientes.length }} pendientes</v-chip>
          <v-btn 
            size="small" 
            color="info" 
            class="ml-2" 
            @click="cargarPagos"
            :loading="cargando"
          >
            <v-icon start>mdi-refresh</v-icon>
            Actualizar
          </v-btn>
        </v-card-title>
        
        <v-card-text>
          <v-alert v-if="pagosPendientes.length === 0" type="success">
            No hay pagos pendientes de conciliación
          </v-alert>
          
          <v-data-table
            v-else
            :items="pagosPendientes"
            :headers="headers"
            :items-per-page="10"
            class="elevation-1"
          >
            <template v-slot:item.fecha_reporte="{ item }">
              {{ formatearFecha(item.fecha_reporte) }}
            </template>
            
            <template v-slot:item.cliente_nombre="{ item }">
              <div>
                <div class="font-weight-bold">{{ item.cliente_nombre }}</div>
                <div class="text-caption text-grey">{{ item.cliente_cedula }}</div>
              </div>
            </template>
            
            <template v-slot:item.monto_reportado_bs="{ item }">
              <div class="text-right">
                <div class="font-weight-bold">BS {{ formatearNumero(item.monto_reportado_bs) }}</div>
                <div class="text-caption text-grey">${{ formatearNumero(item.monto_reportado_usd) }}</div>
              </div>
            </template>
            
            <template v-slot:item.metodo="{ item }">
              <v-chip :color="colorMetodo(item.metodo)" size="small">
                {{ formatoMetodo(item.metodo) }}
              </v-chip>
            </template>
            
            <template v-slot:item.comprobante="{ item }">
              <v-btn 
                v-if="item.comprobante || item.comprobante_url" 
                size="small" 
                color="info"
                @click="verComprobante(item.comprobante || item.comprobante_url)"
                variant="tonal"
              >
                <v-icon start size="16">mdi-image</v-icon>
                Ver
              </v-btn>
              <span v-else class="text-grey text-caption">Sin foto</span>
            </template>
            
            <template v-slot:item.acciones="{ item }">
              <div class="d-flex gap-2">
                <v-btn 
                  color="success" 
                  size="small" 
                  @click="abrirConciliar(item, true)"
                  variant="tonal"
                >
                  ✅ Aprobar
                </v-btn>
                <v-btn 
                  color="error" 
                  size="small" 
                  @click="abrirConciliar(item, false)"
                  variant="tonal"
                >
                  ❌ Rechazar
                </v-btn>
              </div>
            </template>
          </v-data-table>
        </v-card-text>
      </v-card>
    </v-col>
  </v-row>
  
  <!-- Dialog Confirmar -->
  <v-dialog v-model="dialogConfirmar" max-width="500">
    <v-card>
      <v-card-title :class="accionAprobar ? 'bg-success' : 'bg-error'" class="text-white">
        {{ accionAprobar ? '✅ Aprobar Pago' : '❌ Rechazar Pago' }}
      </v-card-title>
      <v-card-text class="pt-4">
        <div class="mb-3">
          <div class="text-subtitle-2 font-weight-bold">Detalles del pago:</div>
          <v-divider class="my-2"></v-divider>
          <p><strong>Cliente:</strong> {{ pagoSeleccionado?.cliente_nombre }}</p>
          <p><strong>Cédula:</strong> {{ pagoSeleccionado?.cliente_cedula }}</p>
          <p><strong>Cuota:</strong> #{{ pagoSeleccionado?.cuota_numero }}</p>
          <p><strong>Monto reportado:</strong> BS {{ formatearNumero(pagoSeleccionado?.monto_reportado_bs) }}</p>
          <p><strong>Referencia:</strong> {{ pagoSeleccionado?.referencia || 'N/A' }}</p>
          <p><strong>Método:</strong> {{ formatoMetodo(pagoSeleccionado?.metodo) }}</p>
          <p><strong>Banco Origen:</strong> {{ pagoSeleccionado?.banco_origen || 'N/A' }}</p>
          <p><strong>Teléfono:</strong> {{ pagoSeleccionado?.telefono_pago || 'N/A' }}</p>
          
          <!-- Mostrar comprobante en el diálogo -->
          <div v-if="pagoSeleccionado?.comprobante || pagoSeleccionado?.comprobante_url" class="mt-3">
            <div class="text-subtitle-2 font-weight-bold">Comprobante:</div>
            <v-img
              :src="pagoSeleccionado.comprobante || pagoSeleccionado.comprobante_url"
              max-height="200"
              contain
              class="mt-2 rounded"
              @click="verComprobante(pagoSeleccionado.comprobante || pagoSeleccionado.comprobante_url)"
            >
              <template v-slot:placeholder>
                <v-row class="fill-height ma-0" align="center" justify="center">
                  <v-progress-circular indeterminate color="grey-lighten-5"></v-progress-circular>
                </v-row>
              </template>
            </v-img>
          </div>
        </div>
        
        <v-text-field
          v-if="accionAprobar"
          v-model.number="montoConfirmado"
          label="Monto a confirmar (BS)"
          type="number"
          prefix="BS"
          hint="Monto en Bolívares que se confirma"
          persistent-hint
          variant="outlined"
          density="comfortable"
          :rules="[v => v > 0 || 'El monto debe ser mayor a 0']"
        ></v-text-field>
        
        <v-alert v-if="!accionAprobar" type="warning" class="mt-3" border="start">
          El pago será rechazado y la cuota volverá a estado pendiente.
        </v-alert>
      </v-card-text>
      <v-card-actions>
        <v-btn @click="dialogConfirmar = false">Cancelar</v-btn>
        <v-btn 
          :color="accionAprobar ? 'success' : 'error'" 
          @click="confirmarAccion"
          :loading="cargando"
          size="large"
          :disabled="accionAprobar && (!montoConfirmado || montoConfirmado <= 0)"
        >
          {{ accionAprobar ? '✅ Aprobar' : '❌ Rechazar' }}
        </v-btn>
      </v-card-actions>
    </v-card>
  </v-dialog>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import { api } from '@/config/api'

const pagosPendientes = ref([])
const dialogConfirmar = ref(false)
const pagoSeleccionado = ref(null)
const accionAprobar = ref(true)
const montoConfirmado = ref(0)
const cargando = ref(false)
let refreshInterval = null

const headers = [
  { title: 'Fecha', key: 'fecha_reporte', width: '150px' },
  { title: 'Cliente', key: 'cliente_nombre', width: '200px' },
  { title: 'Cuota #', key: 'cuota_numero', width: '80px' },
  { title: 'Monto', key: 'monto_reportado_bs', align: 'end', width: '150px' },
  { title: 'Método', key: 'metodo', width: '120px' },
  { title: 'Referencia', key: 'referencia', width: '120px' },
  { title: 'Comprobante', key: 'comprobante', width: '120px' },
  { title: 'Acciones', key: 'acciones', width: '180px' }
]

const colorMetodo = (metodo) => {
  const colores = {
    pago_movil: 'purple',
    transferencia: 'blue',
    zelle: 'green',
    binance: 'amber',
    efectivo: 'grey'
  }
  return colores[metodo] || 'grey'
}

const formatoMetodo = (metodo) => {
  const nombres = {
    pago_movil: 'Pago Móvil',
    transferencia: 'Transferencia',
    zelle: 'Zelle',
    binance: 'Binance',
    efectivo: 'Efectivo'
  }
  return nombres[metodo] || metodo
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

const formatearNumero = (num) => {
  if (!num && num !== 0) return '0,00'
  return Number(num).toLocaleString('es-VE', {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2
  })
}

const cargarPagos = async () => {
  cargando.value = true
  try {
    const data = await api.get('/pagos/pendientes')
    pagosPendientes.value = Array.isArray(data) ? data : []
    console.log('📋 Pagos cargados:', pagosPendientes.value.length)
    
    // Debug: mostrar los comprobantes
    pagosPendientes.value.forEach((p, i) => {
      console.log(`Pago ${i+1} - comprobante:`, p.comprobante || p.comprobante_url || 'SIN FOTO')
    })
  } catch (e) {
    console.error('Error cargando pagos:', e)
    pagosPendientes.value = []
  } finally {
    cargando.value = false
  }
}

const abrirConciliar = (pago, aprobar) => {
  pagoSeleccionado.value = pago
  accionAprobar.value = aprobar
  montoConfirmado.value = pago.monto_reportado_bs || 0
  dialogConfirmar.value = true
}

const confirmarAccion = async () => {
  if (!pagoSeleccionado.value) return
  
  cargando.value = true
  
  try {
    const payload = {
      pago_id: Number(pagoSeleccionado.value.id || pagoSeleccionado.value.pago_id),
      monto_confirmado_bs: accionAprobar.value ? Number(montoConfirmado.value) : 0,
      estado: accionAprobar.value ? 'conciliado' : 'rechazado',
      conciliado_por: 'admin'
    }
    
    console.log('📤 Enviando payload:', payload)
    
    const data = await api.post('/pagos/conciliar', payload)
    
    alert(data.mensaje || (accionAprobar.value ? '✅ Pago aprobado exitosamente' : '❌ Pago rechazado'))
    dialogConfirmar.value = false
    await cargarPagos()
    
  } catch (e) {
    console.error('Error en conciliación:', e)
    const errorMsg = e.response?.data?.detail || e.message || 'Error en conciliación'
    alert('Error: ' + errorMsg)
  } finally {
    cargando.value = false
  }
}

const verComprobante = (comprobante) => {
  if (!comprobante) {
    alert('No hay comprobante disponible')
    return
  }
  
  console.log('📷 Abriendo comprobante:', comprobante)
  
  // Si es URL de Cloudflare o imagen
  if (comprobante.startsWith('http') || comprobante.startsWith('data:image')) {
    const win = window.open('', '_blank')
    if (win) {
      win.document.write(`
        <html>
          <head>
            <title>Comprobante de Pago</title>
            <style>
              body { 
                margin: 0; 
                display: flex; 
                justify-content: center; 
                align-items: center; 
                min-height: 100vh; 
                background: #0a0e1a;
                font-family: sans-serif;
              }
              .container {
                max-width: 95%;
                max-height: 95vh;
                display: flex;
                flex-direction: column;
                align-items: center;
              }
              img { 
                max-width: 100%; 
                max-height: 85vh; 
                border-radius: 8px;
                box-shadow: 0 4px 24px rgba(0,0,0,0.5);
              }
              .info {
                color: rgba(255,255,255,0.6);
                margin-top: 12px;
                font-size: 14px;
              }
              .error {
                color: #ef4444;
                margin-top: 20px;
                display: none;
              }
            </style>
          </head>
          <body>
            <div class="container">
              <img src="${comprobante}" alt="Comprobante de pago" 
                   onerror="this.style.display='none'; document.querySelector('.error').style.display='block'" 
                   onload="document.querySelector('.loading').style.display='none'"/>
              <div class="loading" style="color:rgba(255,255,255,0.4);margin-top:20px;">
                ⏳ Cargando imagen...
              </div>
              <div class="info">Comprobante de pago</div>
              <div class="error">⚠️ No se pudo cargar la imagen</div>
            </div>
          </body>
        </html>
      `)
    }
  } else {
    // Si es un path relativo
    const fullUrl = comprobante.startsWith('/') 
      ? `https://financoop.onrender.com${comprobante}`
      : comprobante
    window.open(fullUrl, '_blank')
  }
}

onMounted(() => {
  cargarPagos()
  refreshInterval = setInterval(cargarPagos, 30000)
})

onUnmounted(() => {
  if (refreshInterval) {
    clearInterval(refreshInterval)
  }
})
</script>

<style scoped>
.gap-2 {
  gap: 8px;
}
</style>