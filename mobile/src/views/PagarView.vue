<template>
  <v-container class="pa-4 pagar-view">
    <div class="d-flex align-center mb-4">
      <v-btn icon variant="text" size="small" @click="volver">
        <v-icon>mdi-arrow-left</v-icon>
      </v-btn>
      <span class="text-h6 font-weight-medium ml-2">Realizar Pago</span>
    </div>

    <v-card v-if="!cuotaSeleccionada" class="pa-4 text-center" elevation="4">
      <v-icon size="64" color="medium-emphasis" class="mb-4">mdi-credit-card-off</v-icon>
      <h3 class="text-h6 mb-2">No hay cuota seleccionada</h3>
      <p class="text-body-2 text-medium-emphasis mb-4">Selecciona una cuota desde "Inicio" o "Cuotas"</p>
      <v-btn color="primary" rounded="pill" @click="volver">
        <v-icon start>mdi-calendar-clock</v-icon>
        Ver mis Cuotas
      </v-btn>
    </v-card>

    <v-card v-else class="pa-4" elevation="4">
      <v-card-title class="px-0 pt-0">
        <div class="d-flex align-center">
          <v-icon color="success" size="32" class="mr-3">mdi-credit-card-check</v-icon>
          <div>
            <div class="text-h6 font-weight-bold">Pagar Cuota #{{ cuotaSeleccionada.cuota_numero || cuotaSeleccionada.numero }}</div>
            <div class="text-caption text-medium-emphasis">{{ cuotaSeleccionada.financiamiento_descripcion || 'Cuota pendiente' }}</div>
          </div>
        </div>
      </v-card-title>

      <v-divider class="my-4"></v-divider>

      <div class="text-center mb-4">
        <div class="text-caption text-medium-emphasis">Monto a Pagar</div>
        <!-- ✅ MONTO EN BS ACTUALIZADO -->
        <div class="text-h3 font-weight-bold text-primary" style="font-variant-numeric: tabular-nums;">
          BS {{ formatearBS(cuotaSeleccionada.monto_bs || cuotaSeleccionada.monto_total_bs) }}
        </div>
        <!-- ✅ USD SIEMPRE IGUAL -->
        <div class="text-caption text-medium-emphasis mt-1">
          Ref: ${{ formatearUSD(cuotaSeleccionada.monto_usd_ref || cuotaSeleccionada.monto_total_usd_ref) }}
        </div>
        <div class="text-caption text-medium-emphasis">Tasa: {{ tasaActual }} Bs/$</div>
        <div v-if="(cuotaSeleccionada.monto_interes_bs || 0) > 0" class="text-caption text-error mt-1">
          +{{ formatearBS(cuotaSeleccionada.monto_interes_bs) }} Bs de mora
        </div>
      </div>

      <v-divider class="my-4"></v-divider>

      <div class="text-subtitle-2 font-weight-medium mb-2">Método de pago</div>
      <v-card class="mb-4" elevation="1">
        <v-list density="compact">
          <v-list-item
            v-for="metodo in metodosPago"
            :key="metodo.value"
            :active="pagoForm.metodo === metodo.value"
            @click="pagoForm.metodo = metodo.value"
            class="py-2"
          >
            <template v-slot:prepend>
              <v-icon :color="pagoForm.metodo === metodo.value ? 'primary' : 'medium-emphasis'">
                {{ metodoIcono(metodo.value) }}
              </v-icon>
            </template>
            <v-list-item-title>{{ metodo.title }}</v-list-item-title>
            <template v-slot:append>
              <v-icon v-if="pagoForm.metodo === metodo.value" color="primary">mdi-check-circle</v-icon>
            </template>
          </v-list-item>
        </v-list>
      </v-card>

      <v-card v-if="datosBancariosMetodo" class="mb-4 datos-banco" variant="outlined">
        <v-card-text class="pa-3">
          <div class="text-caption text-medium-emphasis mb-2 font-weight-medium">Datos para transferir:</div>
          <div v-for="(dato, key) in datosBancariosMetodo" :key="key" class="d-flex justify-space-between py-1">
            <span class="text-caption text-medium-emphasis">{{ key }}:</span>
            <div class="d-flex align-center">
              <span class="text-body-2 font-weight-medium">{{ dato }}</span>
              <v-btn icon size="x-small" variant="text" class="ml-1" @click="copiarAlPortapapeles(dato)">
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
        class="mb-3"
        hide-details
        :rules="[v => !!v || 'Requerido']"
      ></v-text-field>

      <v-text-field
        v-model="pagoForm.banco_origen"
        label="Banco de Origen (desde donde pagaste)"
        placeholder="Ej: Banco de Venezuela"
        prepend-inner-icon="mdi-bank"
        variant="outlined"
        class="mb-3"
        hide-details
      ></v-text-field>

      <v-text-field
        v-model="pagoForm.telefono_pago"
        label="Teléfono desde donde pagaste"
        placeholder="Ej: 04121234567"
        prepend-inner-icon="mdi-phone"
        variant="outlined"
        class="mb-3"
        hide-details
      ></v-text-field>

      <v-file-input
        v-model="pagoForm.comprobante"
        label="Foto del Comprobante (opcional)"
        accept="image/*"
        capture="camera"
        prepend-icon="mdi-camera"
        variant="outlined"
        class="mb-4"
        show-size
        chips
      ></v-file-input>

      <v-alert v-if="error" type="error" variant="tonal" class="mb-3" density="compact">
        {{ error }}
      </v-alert>

      <v-btn 
        color="success" 
        block 
        size="x-large"
        :loading="cargandoPago"
        :disabled="!pagoForm.referencia || !pagoForm.metodo"
        @click="handlePago"
        elevation="4"
        rounded="pill"
      >
        <v-icon start>mdi-send</v-icon>
        Reportar Pago
      </v-btn>

      <v-btn variant="text" block class="mt-2" @click="cancelarPago">
        Cancelar
      </v-btn>
    </v-card>
  </v-container>
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
  error,
  formatearBS, 
  formatearUSD,
  reportarPago,
  copiarAlPortapapeles,
  setCuotaSeleccionada
} = useFinanCash()

onMounted(() => {
  console.log('📋 PagarView montado')
  console.log('📋 Cuota seleccionada:', cuotaSeleccionada.value)
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
  console.log('🔄 Iniciando pago...')
  console.log('📋 Cuota seleccionada:', cuotaSeleccionada.value)
  console.log('📋 Formulario:', pagoForm.value)
  
  const success = await reportarPago()
  console.log('✅ Resultado:', success)
  
  if (success) {
    console.log('✅ Pago exitoso, redirigiendo...')
    router.push('/')
  }
}

const volver = () => {
  router.push('/cuotas')
}

const cancelarPago = () => {
  setCuotaSeleccionada(null)
  router.push('/cuotas')
}
</script>

<style scoped>
.pagar-view { padding-bottom: 80px; }
.datos-banco {
  border-style: dashed;
  border-radius: 12px;
}
</style>