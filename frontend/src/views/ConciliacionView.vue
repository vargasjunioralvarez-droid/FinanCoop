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
          >
            <template v-slot:item.fecha_reporte="{ item }">
              {{ formatearFecha(item.fecha_reporte) }}
            </template>
            
            <template v-slot:item.monto_reportado="{ item }">
              <strong>${{ item.monto_reportado }}</strong>
            </template>
            
            <template v-slot:item.metodo="{ item }">
              <v-chip :color="colorMetodo(item.metodo)" size="small">
                {{ item.metodo }}
              </v-chip>
            </template>
            
            <template v-slot:item.comprobante="{ item }">
              <v-btn 
                v-if="item.comprobante" 
                size="small" 
                color="info"
                @click="verComprobante(item.comprobante)"
              >
                📷 Ver
              </v-btn>
              <span v-else class="text-grey">Sin foto</span>
            </template>
            
            <template v-slot:item.acciones="{ item }">
              <div class="d-flex gap-2">
                <v-btn 
                  color="success" 
                  size="small" 
                  @click="abrirConciliar(item, true)"
                >
                  ✅ Aprobar
                </v-btn>
                <v-btn 
                  color="error" 
                  size="small" 
                  @click="abrirConciliar(item, false)"
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
  <v-dialog v-model="dialogConfirmar" max-width="400">
    <v-card>
      <v-card-title :class="accionAprobar ? 'bg-success' : 'bg-error'">
        {{ accionAprobar ? '✅ Aprobar Pago' : '❌ Rechazar Pago' }}
      </v-card-title>
      <v-card-text class="pt-4">
        <p>Cliente: <strong>{{ pagoSeleccionado?.cliente }}</strong></p>
        <p>Cuota: #{{ pagoSeleccionado?.cuota_numero }}</p>
        <p>Monto reportado: <strong>${{ pagoSeleccionado?.monto_reportado }}</strong></p>
        <p>Referencia: {{ pagoSeleccionado?.referencia }}</p>
        <p>Método: {{ pagoSeleccionado?.metodo }}</p>
        
        <v-text-field
          v-if="accionAprobar"
          v-model="montoConfirmado"
          label="Monto a confirmar"
          type="number"
          prefix="$"
        ></v-text-field>
        
        <v-alert v-if="!accionAprobar" type="warning" class="mt-3">
          El pago será rechazado y la cuota volverá a estado pendiente.
        </v-alert>
      </v-card-text>
      <v-card-actions>
        <v-btn @click="dialogConfirmar = false">Cancelar</v-btn>
        <v-btn 
          :color="accionAprobar ? 'success' : 'error'" 
          @click="confirmarAccion"
        >
          {{ accionAprobar ? 'Aprobar' : 'Rechazar' }}
        </v-btn>
      </v-card-actions>
    </v-card>
  </v-dialog>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import axios from 'axios'

const API_URL = 'http://localhost:8000'

const pagosPendientes = ref([])
const dialogConfirmar = ref(false)
const pagoSeleccionado = ref(null)
const accionAprobar = ref(true)
const montoConfirmado = ref(0)

const headers = [
  { title: 'Fecha', key: 'fecha_reporte' },
  { title: 'Cliente', key: 'cliente' },
  { title: 'Cédula', key: 'cedula' },
  { title: 'Cuota', key: 'cuota_numero' },
  { title: 'Monto', key: 'monto_reportado' },
  { title: 'Método', key: 'metodo' },
  { title: 'Referencia', key: 'referencia' },
  { title: 'Banco', key: 'banco_origen' },
  { title: 'Teléfono', key: 'telefono_pago' },
  { title: 'Comprobante', key: 'comprobante' },
  { title: 'Acciones', key: 'acciones' }
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

const formatearFecha = (fechaStr) => {
  if (!fechaStr) return ''
  const fecha = new Date(fechaStr)
  return fecha.toLocaleString('es-ES')
}

const cargarPagos = async () => {
  try {
    const res = await axios.get(`${API_URL}/pagos/pendientes`)
    pagosPendientes.value = res.data
  } catch (e) {
    console.error('Error cargando pagos:', e)
  }
}

const abrirConciliar = (pago, aprobar) => {
  pagoSeleccionado.value = pago
  accionAprobar.value = aprobar
  montoConfirmado.value = pago.monto_reportado
  dialogConfirmar.value = true
}

const confirmarAccion = async () => {
  try {
    const res = await axios.post(`${API_URL}/pagos/conciliar`, {
      pago_id: pagoSeleccionado.value.pago_id,
      monto_confirmado: accionAprobar.value ? parseFloat(montoConfirmado.value) : 0,
      estado: accionAprobar.value ? 'conciliado' : 'rechazado',
      conciliado_por: 'admin'
    })
    
    alert(res.data.mensaje)
    dialogConfirmar.value = false
    await cargarPagos()
    
  } catch (e) {
    alert('Error en conciliación')
    console.error(e)
  }
}

const verComprobante = (comprobante) => {
  if (comprobante.startsWith('data:image')) {
    // Es base64, mostrar en nueva ventana
    const win = window.open()
    win.document.write(`<img src="${comprobante}" style="max-width:100%">`)
  } else {
    window.open(comprobante, '_blank')
  }
}

onMounted(() => {
  cargarPagos()
  // Actualizar cada 30 segundos
  setInterval(cargarPagos, 30000)
})
</script>