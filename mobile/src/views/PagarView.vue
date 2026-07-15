<template>
  <div class="pagar-wrapper">
    <div class="bg-gradient"></div>

    <div class="page-content">
      <!-- Header -->
      <div class="d-flex align-center mb-4">
        <v-btn icon variant="text" size="small" class="back-btn" @click="volver">
          <v-icon>mdi-arrow-left</v-icon>
        </v-btn>
        <span class="header-title">Realizar Pago</span>
      </div>

      <!-- Sin cuota seleccionada -->
      <v-card v-if="!cuotaSeleccionada" class="empty-card glass-card" elevation="0">
        <v-card-text class="pa-4 text-center">
          <v-icon size="64" color="rgba(255,255,255,0.1)" class="mb-4">mdi-credit-card-off</v-icon>
          <h3 class="empty-title">No hay cuota seleccionada</h3>
          <p class="empty-text">Selecciona una cuota desde "Inicio" o "Cuotas"</p>
          <v-btn color="#4facfe" rounded="pill" @click="volver">
            <v-icon start>mdi-calendar-clock</v-icon>
            Ver mis Cuotas
          </v-btn>
        </v-card-text>
      </v-card>

      <!-- Pago -->
      <v-card v-else class="pago-card glass-card" elevation="0">
        <v-card-text class="pa-4">
          <div class="d-flex align-center mb-2">
            <v-icon color="#4caf50" size="32" class="mr-3">mdi-credit-card-check</v-icon>
            <div>
              <div class="pago-title">Pagar Cuota #{{ cuotaSeleccionada.cuota_numero || cuotaSeleccionada.numero }}</div>
              <div class="pago-subtitle">{{ cuotaSeleccionada.financiamiento_descripcion || 'Cuota pendiente' }}</div>
            </div>
          </div>

          <v-divider class="my-4" style="border-color: rgba(255,255,255,0.06);" />

          <div class="text-center mb-4">
            <div class="monto-label">Monto a Pagar</div>
            <div class="monto-value">BS {{ formatearBS(cuotaSeleccionada.monto_bs || cuotaSeleccionada.monto_total_bs) }}</div>
            <div class="monto-ref">Ref: ${{ formatearUSD(cuotaSeleccionada.monto_usd_ref || cuotaSeleccionada.monto_total_usd_ref) }}</div>
            <div class="monto-tasa">Tasa: {{ tasaActual }} Bs/$</div>
            <div v-if="(cuotaSeleccionada.monto_interes_bs || 0) > 0" class="monto-interes">+{{ formatearBS(cuotaSeleccionada.monto_interes_bs) }} Bs de mora</div>
          </div>

          <v-divider class="my-4" style="border-color: rgba(255,255,255,0.06);" />

          <div class="metodo-label">Método de pago</div>
          <v-card class="metodo-card" elevation="0">
            <v-list density="compact" class="bg-transparent">
              <v-list-item
                v-for="metodo in metodosPago"
                :key="metodo.value"
                :active="pagoForm.metodo === metodo.value"
                @click="pagoForm.metodo = metodo.value"
                class="py-2"
              >
                <template v-slot:prepend>
                  <v-icon :color="pagoForm.metodo === metodo.value ? '#4facfe' : 'rgba(255,255,255,0.3)'">
                    {{ metodoIcono(metodo.value) }}
                  </v-icon>
                </template>
                <v-list-item-title>{{ metodo.title }}</v-list-item-title>
                <template v-slot:append>
                  <v-icon v-if="pagoForm.metodo === metodo.value" color="#4facfe">mdi-check-circle</v-icon>
                </template>
              </v-list-item>
            </v-list>
          </v-card>

          <v-card v-if="datosBancariosMetodo" class="datos-banco" variant="outlined">
            <v-card-text class="pa-3">
              <div class="datos-title">Datos para transferir:</div>
              <div v-for="(dato, key) in datosBancariosMetodo" :key="key" class="dato-item">
                <span class="dato-label">{{ key }}:</span>
                <div class="d-flex align-center">
                  <span class="dato-value">{{ dato }}</span>
                  <v-btn icon size="x-small" variant="text" class="copy-btn" @click="copiarAlPortapapeles(dato)">
                    <v-icon size="14">mdi-content-copy</v-icon>
                  </v-btn>
                </div>
              </div>
            </v-card-text>
          </v-card>

          <v-text-field
            v-model="pagoForm.referencia"
            label="Número de Referencia *"
            placeholder="Últimos 4 dígitos del comprobante"
            prepend-inner-icon="mdi-numeric"
            variant="outlined"
            class="input-field"
            hide-details
          />

          <v-text-field
            v-model="pagoForm.banco_origen"
            label="Banco de Origen"
            placeholder="Ej: Banco de Venezuela"
            prepend-inner-icon="mdi-bank"
            variant="outlined"
            class="input-field"
            hide-details
          />

          <v-text-field
            v-model="pagoForm.telefono_pago"
            label="Teléfono desde donde pagaste"
            placeholder="Ej: 04121234567"
            prepend-inner-icon="mdi-phone"
            variant="outlined"
            class="input-field"
            hide-details
          />

          <v-file-input
            v-model="pagoForm.comprobante"
            label="Foto del Comprobante (opcional)"
            accept="image/*"
            capture="camera"
            prepend-icon="mdi-camera"
            variant="outlined"
            class="input-field"
            show-size
            chips
          />

          <v-alert v-if="error" type="error" variant="tonal" class="error-alert" density="compact">
            {{ error }}
          </v-alert>

          <v-btn
            color="success"
            block
            size="x-large"
            :loading="cargandoPago || cargandoUpload"
            :disabled="!pagoForm.referencia || !pagoForm.metodo || cargandoUpload"
            @click="handlePago"
            elevation="0"
            rounded="pill"
            class="pagar-btn"
          >
            <v-icon start>mdi-send</v-icon>
            {{ cargandoUpload ? 'Subiendo comprobante...' : 'Reportar Pago' }}
          </v-btn>

          <v-btn variant="text" block class="cancel-btn" @click="cancelarPago">
            Cancelar
          </v-btn>
        </v-card-text>
      </v-card>
    </div>
  </div>
</template>

<script setup>
import { computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useFinanCash } from '@/composables/useFinanCash'

const router = useRouter()

const { 
  cuotaSeleccionada, 
  tasaActual,
  datosPago, 
  pagoForm, 
  metodosPago, 
  cargandoPago,
  cargandoUpload,
  error,
  formatearBS, 
  formatearUSD,
  reportarPago,
  copiarAlPortapapeles,
  setCuotaSeleccionada,
  subirComprobante
} = useFinanCash()

onMounted(() => {
  console.log('📋 PagarView montado')
  console.log('📋 cuotaSeleccionada:', cuotaSeleccionada.value)
})

const datosBancariosMetodo = computed(() => {
  if (!datosPago.value || !pagoForm.value.metodo) return null
  const config = datosPago.value
  switch (pagoForm.value.metodo) {
    case 'pago_movil':
      return config.pago_movil ? {
        'Banco': config.pago_movil.banco,
        'Teléfono': config.pago_movil.telefono,
        'Cédula': config.pago_movil.cedula
      } : null
    case 'transferencia':
      return config.transferencia ? {
        'Banco': config.transferencia.banco,
        'Cuenta': config.transferencia.cuenta
      } : null
    case 'zelle':
      return config.zelle ? { 'Email': config.zelle } : null
    case 'binance':
      return config.binance ? { 'ID': config.binance } : null
    default:
      return null
  }
})

function metodoIcono(metodo) {
  const iconos = {
    pago_movil: 'mdi-cellphone',
    transferencia: 'mdi-bank-transfer',
    zelle: 'mdi-currency-usd',
    binance: 'mdi-bitcoin'
  }
  return iconos[metodo] || 'mdi-cash'
}

const handlePago = async () => {
  try {
    console.log('📝 Iniciando proceso de pago')
    console.log('📋 Cuota seleccionada (completa):', JSON.stringify(cuotaSeleccionada.value, null, 2))
    
    // ✅ OBTENER EL ID DE LA CUOTA CORRECTAMENTE
    const cuotaId = cuotaSeleccionada.value?.cuota_id || cuotaSeleccionada.value?.id
    
    if (!cuotaId) {
      console.error('❌ No se encontró cuota_id en:', cuotaSeleccionada.value)
      alert('Error: No se pudo identificar la cuota. Intenta de nuevo.')
      return
    }
    
    console.log(`✅ Cuota ID: ${cuotaId}`)
    console.log('📋 Método:', pagoForm.value.metodo)
    console.log('📋 Referencia:', pagoForm.value.referencia)
    console.log('📸 Comprobante file:', pagoForm.value.comprobante)
    
    let comprobanteUrl = null
    
    if (pagoForm.value.comprobante && pagoForm.value.comprobante instanceof File) {
      console.log('📸 Subiendo comprobante a Cloudflare...')
      comprobanteUrl = await subirComprobante(pagoForm.value.comprobante)
      if (!comprobanteUrl) {
        alert('No se pudo subir el comprobante. Intenta de nuevo.')
        return
      }
      console.log('✅ Comprobante subido URL:', comprobanteUrl)
    } else {
      console.log('⚠️ No hay comprobante para subir')
    }
    
    // ✅ PAYLOAD CON CUOTA_ID INCLUIDO
    const payload = {
      cuota_id: Number(cuotaId),
      monto_bs: Number(cuotaSeleccionada.value?.monto_bs || cuotaSeleccionada.value?.monto_total_bs || 0),
      metodo: String(pagoForm.value.metodo),
      referencia: String(pagoForm.value.referencia).trim(),
      banco_origen: String(pagoForm.value.banco_origen || '').trim(),
      telefono_pago: String(pagoForm.value.telefono_pago || '').trim(),
      cedula_pago: String(pagoForm.value.cedula_pago || '').trim(),
      comprobante: String(comprobanteUrl || '')
    }
    
    console.log('📤 Enviando pago al backend:', JSON.stringify(payload, null, 2))
    
    const success = await reportarPago(payload)
    if (success) {
      console.log('✅ Pago reportado exitosamente')
      router.push('/inicio')
    }
  } catch (e) {
    console.error('❌ Error en pago:', e)
    const errorMsg = e.response?.data?.detail || e.message || 'Error al procesar el pago'
    alert('Error al procesar el pago: ' + (typeof errorMsg === 'object' ? JSON.stringify(errorMsg) : errorMsg))
  }
}

const volver = () => router.push('/cuotas')
const cancelarPago = () => {
  setCuotaSeleccionada(null)
  router.push('/cuotas')
}
</script>

<style scoped>
.pagar-wrapper {
  min-height: 100vh;
  background: #0a0e1a;
  position: relative;
}

.bg-gradient {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: radial-gradient(ellipse at 20% 50%, rgba(79, 172, 254, 0.08), transparent 70%),
              radial-gradient(ellipse at 80% 50%, rgba(99, 102, 241, 0.08), transparent 70%);
  z-index: 0;
}

.page-content {
  position: relative;
  z-index: 1;
  padding: 16px 16px 80px;
}

.back-btn {
  color: rgba(255,255,255,0.6) !important;
}

.header-title {
  font-size: 20px;
  font-weight: 700;
  color: #ffffff;
  margin-left: 8px;
}

.glass-card {
  background: rgba(255,255,255,0.04) !important;
  backdrop-filter: blur(12px) !important;
  -webkit-backdrop-filter: blur(12px) !important;
  border: 1px solid rgba(255,255,255,0.06);
  border-radius: 16px !important;
}

.empty-card {
  padding: 24px 0;
}

.empty-title {
  font-size: 18px;
  font-weight: 600;
  color: #ffffff;
  margin-bottom: 8px;
}

.empty-text {
  font-size: 14px;
  color: rgba(255,255,255,0.4);
  margin-bottom: 16px;
}

.pago-title {
  font-size: 16px;
  font-weight: 600;
  color: #ffffff;
}

.pago-subtitle {
  font-size: 12px;
  color: rgba(255,255,255,0.4);
}

.monto-label {
  font-size: 12px;
  color: rgba(255,255,255,0.4);
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.monto-value {
  font-size: 32px;
  font-weight: 700;
  color: #4facfe;
}

.monto-ref {
  font-size: 12px;
  color: rgba(255,255,255,0.3);
}

.monto-tasa {
  font-size: 12px;
  color: rgba(255,255,255,0.3);
}

.monto-interes {
  font-size: 12px;
  color: #f87171;
}

.metodo-label {
  font-size: 13px;
  font-weight: 600;
  color: #ffffff;
  margin-bottom: 8px;
}

.metodo-card {
  background: rgba(255,255,255,0.02) !important;
  border-radius: 12px !important;
  margin-bottom: 12px;
}

.metodo-card :deep(.v-list-item) {
  color: rgba(255,255,255,0.7);
}

.metodo-card :deep(.v-list-item--active) {
  color: #ffffff;
}

.datos-banco {
  background: rgba(255,255,255,0.02) !important;
  border-color: rgba(255,255,255,0.06) !important;
  border-radius: 12px;
  margin-bottom: 12px;
}

.datos-title {
  font-size: 11px;
  font-weight: 600;
  color: rgba(255,255,255,0.4);
  text-transform: uppercase;
  letter-spacing: 0.5px;
  margin-bottom: 6px;
}

.dato-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 4px 0;
}

.dato-label {
  font-size: 12px;
  color: rgba(255,255,255,0.4);
}

.dato-value {
  font-size: 13px;
  font-weight: 500;
  color: #ffffff;
}

.copy-btn {
  color: rgba(255,255,255,0.3) !important;
}

.copy-btn:hover {
  color: rgba(255,255,255,0.6) !important;
}

.input-field {
  margin-bottom: 12px;
}

.input-field :deep(.v-field) {
  background: rgba(255,255,255,0.04) !important;
  border-radius: 12px !important;
}

.input-field :deep(.v-field__input) {
  color: #ffffff !important;
}

.input-field :deep(.v-field__input::placeholder) {
  color: rgba(255,255,255,0.2) !important;
}

.input-field :deep(.v-icon) {
  color: rgba(255,255,255,0.3) !important;
}

.input-field :deep(.v-field--focused) {
  box-shadow: 0 0 0 2px rgba(79, 172, 254, 0.15);
}

.error-alert {
  background: rgba(239, 68, 68, 0.1) !important;
  color: #f87171 !important;
  border: 1px solid rgba(239, 68, 68, 0.15);
  border-radius: 12px !important;
  margin-bottom: 12px;
}

.pagar-btn {
  background: linear-gradient(135deg, #4caf50, #388e3c) !important;
  font-weight: 700;
  height: 52px;
}

.cancel-btn {
  color: rgba(255,255,255,0.3) !important;
  margin-top: 8px;
}
</style>