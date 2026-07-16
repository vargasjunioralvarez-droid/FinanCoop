<template>
  <div class="conciliacion-wrapper">
    <div class="bg-gradient"></div>

    <div class="page-content">
      <!-- Header -->
      <div class="d-flex align-center mb-4">
        <v-btn icon variant="text" size="small" class="back-btn" @click="$router.push('/admin')">
          <v-icon>mdi-arrow-left</v-icon>
        </v-btn>
        <span class="header-title">💰 Conciliación de Pagos</span>
      </div>

      <!-- Stats Cards -->
      <v-row class="mb-4">
        <v-col cols="6" md="3">
          <v-card class="stat-card glass-card" elevation="0">
            <v-card-text class="pa-3 text-center">
              <div class="stat-value">{{ pagosPendientes.length }}</div>
              <div class="stat-label">Pendientes</div>
            </v-card-text>
          </v-card>
        </v-col>
        <v-col cols="6" md="3">
          <v-card class="stat-card glass-card" elevation="0">
            <v-card-text class="pa-3 text-center">
              <div class="stat-value" style="color: #ffd54f;">{{ abonosCount }}</div>
              <div class="stat-label">Abonos</div>
            </v-card-text>
          </v-card>
        </v-col>
        <v-col cols="6" md="3">
          <v-card class="stat-card glass-card" elevation="0">
            <v-card-text class="pa-3 text-center">
              <div class="stat-value" style="color: #4caf50;">{{ liquidacionesCount }}</div>
              <div class="stat-label">Liquidaciones</div>
            </v-card-text>
          </v-card>
        </v-col>
        <v-col cols="6" md="3">
          <v-card class="stat-card glass-card" elevation="0">
            <v-card-text class="pa-3 text-center">
              <div class="stat-value" style="color: #ff9800;">{{ adelantosCount }}</div>
              <div class="stat-label">Adelantos</div>
            </v-card-text>
          </v-card>
        </v-col>
      </v-row>

      <!-- Filtros -->
      <v-card class="glass-card mb-4" elevation="0">
        <v-card-text class="pa-3">
          <div class="d-flex align-center gap-2 flex-wrap">
            <v-chip
              :color="filtroModo === 'todos' ? 'primary' : undefined"
              :variant="filtroModo === 'todos' ? 'flat' : 'outlined'"
              @click="filtroModo = 'todos'"
              size="small"
            >
              Todos
            </v-chip>
            <v-chip
              :color="filtroModo === 'cuota' ? 'primary' : undefined"
              :variant="filtroModo === 'cuota' ? 'flat' : 'outlined'"
              @click="filtroModo = 'cuota'"
              size="small"
            >
              <v-icon start size="14">mdi-credit-card-outline</v-icon>
              Cuotas
            </v-chip>
            <v-chip
              :color="filtroModo === 'abono' ? 'info' : undefined"
              :variant="filtroModo === 'abono' ? 'flat' : 'outlined'"
              @click="filtroModo = 'abono'"
              size="small"
            >
              <v-icon start size="14">mdi-cash-plus</v-icon>
              Abonos
            </v-chip>
            <v-chip
              :color="filtroModo === 'adelantar' ? 'warning' : undefined"
              :variant="filtroModo === 'adelantar' ? 'flat' : 'outlined'"
              @click="filtroModo = 'adelantar'"
              size="small"
            >
              <v-icon start size="14">mdi-fast-forward</v-icon>
              Adelantos
            </v-chip>
            <v-chip
              :color="filtroModo === 'liquidar' ? 'success' : undefined"
              :variant="filtroModo === 'liquidar' ? 'flat' : 'outlined'"
              @click="filtroModo = 'liquidar'"
              size="small"
            >
              <v-icon start size="14">mdi-rocket-launch</v-icon>
              Liquidaciones
            </v-chip>
            <v-spacer></v-spacer>
            <v-btn
              size="small"
              color="info"
              variant="tonal"
              @click="cargarPagos"
              :loading="cargando"
            >
              <v-icon start>mdi-refresh</v-icon>
              Actualizar
            </v-btn>
          </div>
        </v-card-text>
      </v-card>

      <!-- Pagos Pendientes -->
      <v-card class="glass-card" elevation="0">
        <v-card-title class="pa-4 pb-2">
          <div class="d-flex align-center">
            <span class="section-title">Pagos Pendientes</span>
            <v-spacer></v-spacer>
            <v-chip color="warning" size="small" variant="flat">
              {{ pagosFiltrados.length }} pendientes
            </v-chip>
          </div>
        </v-card-title>

        <v-card-text class="pa-4 pt-2">
          <v-alert
            v-if="pagosFiltrados.length === 0"
            type="success"
            variant="tonal"
            class="mb-0"
            style="border-radius: 12px;"
          >
            <div class="d-flex align-center">
              <v-icon size="32" class="mr-3">mdi-check-circle</v-icon>
              <div>
                <div class="font-weight-bold">¡Todo al día!</div>
                <div class="text-caption">No hay pagos pendientes de conciliación</div>
              </div>
            </div>
          </v-alert>

          <!-- Lista de pagos como cards (más visual para móvil) -->
          <div v-else class="pagos-list">
            <v-card
              v-for="pago in pagosFiltrados"
              :key="pago.id"
              class="pago-item glass-card mb-3"
              elevation="0"
            >
              <v-card-text class="pa-4">
                <!-- Header: Cliente + Modo de pago -->
                <div class="d-flex justify-space-between align-start mb-3">
                  <div>
                    <div class="cliente-nombre">{{ pago.cliente_nombre }}</div>
                    <div class="cliente-cedula">{{ pago.cliente_cedula }}</div>
                  </div>
                  <v-chip
                    :color="modoPagoColor(pago.modo_pago)"
                    size="small"
                    variant="flat"
                    class="modo-chip"
                  >
                    <v-icon start size="14">{{ modoPagoIcono(pago.modo_pago) }}</v-icon>
                    {{ modoPagoTexto(pago.modo_pago) }}
                  </v-chip>
                </div>

                <!-- 🚨 ALERTA DE ABONO -->
                <v-alert
                  v-if="pago.modo_pago === 'abono'"
                  type="warning"
                  variant="tonal"
                  density="compact"
                  class="mb-3 abono-alert"
                >
                  <div class="d-flex justify-space-between align-center">
                    <span class="abono-text">
                      💰 <strong>Abono parcial</strong>
                    </span>
                    <span class="saldo-text">
                      Saldo: <strong>BS {{ formatearNumero((pago.monto_original_bs || 0) - (pago.monto_reportado_bs || 0)) }}</strong>
                    </span>
                  </div>
                </v-alert>

                <!-- Info de cuotas incluidas (adelantar/liquidar) -->
                <v-alert
                  v-if="pago.cuotas_incluidas && pago.cuotas_incluidas.length > 1"
                  type="info"
                  variant="tonal"
                  density="compact"
                  class="mb-3 cuotas-alert"
                >
                  <div class="cuotas-text">
                    📋 Este pago incluye <strong>{{ pago.cuotas_incluidas.length }} cuotas</strong>
                    <span v-if="pago.es_pago_padre === false" class="text-caption ml-1">(pago hijo)</span>
                  </div>
                </v-alert>

                <!-- Montos -->
                <div class="montos-section mb-3">
                  <!-- NORMAL: pago completo -->
                  <template v-if="pago.modo_pago !== 'abono'">
                    <div class="d-flex justify-space-between mb-1">
                      <span class="monto-label">Monto reportado:</span>
                      <span class="monto-valor">
                        BS {{ formatearNumero(pago.monto_reportado_bs) }}
                      </span>
                    </div>
                    <div class="d-flex justify-space-between">
                      <span class="monto-label">Referencia USD:</span>
                      <span class="monto-usd">
                        ${{ formatearNumero(pago.monto_reportado_usd) }}
                      </span>
                    </div>
                  </template>

                  <!-- ABONO: desglose completo -->
                  <template v-else>
                    <div class="d-flex justify-space-between mb-1">
                      <span class="monto-label">Monto total cuota:</span>
                      <span class="monto-original">
                        BS {{ formatearNumero(pago.monto_original_bs) }}
                      </span>
                    </div>
                    <div class="d-flex justify-space-between mb-1">
                      <span class="monto-label">Monto abonado:</span>
                      <span class="monto-abonado">
                        BS {{ formatearNumero(pago.monto_reportado_bs) }}
                      </span>
                    </div>
                    <v-divider class="my-2" style="border-color: rgba(255,255,255,0.1);" />
                    <div class="d-flex justify-space-between">
                      <span class="monto-label">Saldo pendiente:</span>
                      <span class="monto-saldo">
                        BS {{ formatearNumero((pago.monto_original_bs || 0) - (pago.monto_reportado_bs || 0)) }}
                      </span>
                    </div>
                  </template>
                </div>

                <!-- Detalles del pago -->
                <div class="detalles-section mb-3">
                  <div class="detalle-row">
                    <span class="detalle-label">Cuota:</span>
                    <span class="detalle-valor">#{{ pago.cuota_numero }}</span>
                  </div>
                  <div class="detalle-row">
                    <span class="detalle-label">Método:</span>
                    <v-chip :color="colorMetodo(pago.metodo)" size="x-small" variant="tonal">
                      {{ formatoMetodo(pago.metodo) }}
                    </v-chip>
                  </div>
                  <div class="detalle-row">
                    <span class="detalle-label">Referencia:</span>
                    <span class="detalle-valor font-mono">{{ pago.referencia || 'N/A' }}</span>
                  </div>
                  <div class="detalle-row">
                    <span class="detalle-label">Banco origen:</span>
                    <span class="detalle-valor">{{ pago.banco_origen || 'N/A' }}</span>
                  </div>
                  <div class="detalle-row">
                    <span class="detalle-label">Teléfono:</span>
                    <span class="detalle-valor">{{ pago.telefono_pago || 'N/A' }}</span>
                  </div>
                  <div class="detalle-row">
                    <span class="detalle-label">Fecha:</span>
                    <span class="detalle-valor">{{ formatearFecha(pago.fecha_reporte) }}</span>
                  </div>
                </div>

                <!-- Comprobante -->
                <div v-if="pago.comprobante || pago.comprobante_url" class="comprobante-section mb-3">
                  <v-img
                    :src="pago.comprobante || pago.comprobante_url"
                    max-height="180"
                    class="rounded-lg comprobante-img"
                    cover
                    @click="verComprobante(pago.comprobante || pago.comprobante_url)"
                  >
                    <template v-slot:placeholder>
                      <v-row class="fill-height ma-0" align="center" justify="center">
                        <v-progress-circular indeterminate color="grey-lighten-5" size="32" />
                      </v-row>
                    </template>
                  </v-img>
                  <div class="comprobante-hint text-caption text-center mt-1">
                    Toca para ampliar
                  </div>
                </div>
                <div v-else class="sin-comprobante mb-3 text-center">
                  <v-icon size="32" color="rgba(255,255,255,0.1)">mdi-image-off</v-icon>
                  <div class="text-caption mt-1" style="color: rgba(255,255,255,0.3);">Sin comprobante</div>
                </div>

                <!-- Botones de acción -->
                <div class="d-flex gap-2">
                  <v-btn
                    color="success"
                    variant="flat"
                    class="flex-grow-1 action-btn"
                    @click="abrirConciliar(pago, true)"
                    :disabled="pago.es_pago_padre === false"
                  >
                    <v-icon start>mdi-check</v-icon>
                    {{ pago.modo_pago === 'abono' ? 'Aprobar Abono' : 'Aprobar' }}
                  </v-btn>
                  <v-btn
                    color="error"
                    variant="outlined"
                    class="action-btn-reject"
                    @click="abrirConciliar(pago, false)"
                    :disabled="pago.es_pago_padre === false"
                  >
                    <v-icon>mdi-close</v-icon>
                  </v-btn>
                </div>
                <div
                  v-if="pago.es_pago_padre === false"
                  class="text-caption text-center mt-2"
                  style="color: rgba(255,255,255,0.3);"
                >
                  Este pago se concilia con el pago padre
                </div>
              </v-card-text>
            </v-card>
          </div>
        </v-card-text>
      </v-card>
    </div>
  </div>

  <!-- Dialog Confirmar -->
  <v-dialog v-model="dialogConfirmar" max-width="500">
    <v-card class="dialog-card">
      <v-card-title :class="accionAprobar ? 'bg-success' : 'bg-error'" class="text-white dialog-title">
        <v-icon start class="mr-2">
          {{ accionAprobar ? 'mdi-check-circle' : 'mdi-close-circle' }}
        </v-icon>
        {{ accionAprobar ? 'Aprobar Pago' : 'Rechazar Pago' }}
      </v-card-title>
      <v-card-text class="pt-4">
        <div class="mb-3">
          <div class="text-subtitle-2 font-weight-bold mb-2">Detalles del pago:</div>
          <v-divider class="mb-3"></v-divider>

          <!-- Badge modo de pago en el modal -->
          <div class="d-flex justify-space-between align-center mb-2">
            <span class="text-caption" style="color: rgba(255,255,255,0.5);">Modo:</span>
            <v-chip
              :color="modoPagoColor(pagoSeleccionado?.modo_pago)"
              size="small"
              variant="flat"
            >
              <v-icon start size="14">{{ modoPagoIcono(pagoSeleccionado?.modo_pago) }}</v-icon>
              {{ modoPagoTexto(pagoSeleccionado?.modo_pago) }}
            </v-chip>
          </div>

          <p><strong>Cliente:</strong> {{ pagoSeleccionado?.cliente_nombre }}</p>
          <p><strong>Cédula:</strong> {{ pagoSeleccionado?.cliente_cedula }}</p>
          <p><strong>Cuota:</strong> #{{ pagoSeleccionado?.cuota_numero }}</p>

          <!-- Montos específicos según modo -->
          <template v-if="pagoSeleccionado?.modo_pago === 'abono'">
            <v-alert type="warning" variant="tonal" class="mt-3 mb-3" density="compact">
              <div class="font-weight-bold mb-1">💰 Abono parcial</div>
              <div class="d-flex justify-space-between">
                <span>Monto total cuota:</span>
                <span>BS {{ formatearNumero(pagoSeleccionado?.monto_original_bs) }}</span>
              </div>
              <div class="d-flex justify-space-between">
                <span>Monto abonado:</span>
                <span class="font-weight-bold" style="color: #4caf50;">
                  BS {{ formatearNumero(pagoSeleccionado?.monto_reportado_bs) }}
                </span>
              </div>
              <v-divider class="my-2"></v-divider>
              <div class="d-flex justify-space-between">
                <span>Saldo pendiente:</span>
                <span class="font-weight-bold" style="color: #ffd54f;">
                  BS {{ formatearNumero((pagoSeleccionado?.monto_original_bs || 0) - (pagoSeleccionado?.monto_reportado_bs || 0)) }}
                </span>
              </div>
            </v-alert>
            <p class="text-caption" style="color: rgba(255,255,255,0.5);">
              Al aprobar, el abono se registrará pero la cuota seguirá pendiente hasta completar el pago.
            </p>
          </template>

          <template v-else>
            <p><strong>Monto reportado:</strong> BS {{ formatearNumero(pagoSeleccionado?.monto_reportado_bs) }}</p>
            <p><strong>Referencia USD:</strong> ${{ formatearNumero(pagoSeleccionado?.monto_reportado_usd) }}</p>
          </template>

          <p><strong>Referencia:</strong> {{ pagoSeleccionado?.referencia || 'N/A' }}</p>
          <p><strong>Método:</strong> {{ formatoMetodo(pagoSeleccionado?.metodo) }}</p>
          <p><strong>Banco Origen:</strong> {{ pagoSeleccionado?.banco_origen || 'N/A' }}</p>
          <p><strong>Teléfono:</strong> {{ pagoSeleccionado?.telefono_pago || 'N/A' }}</p>

          <!-- Cuotas incluidas -->
          <div v-if="pagoSeleccionado?.cuotas_incluidas && pagoSeleccionado.cuotas_incluidas.length > 1" class="mt-2">
            <p class="text-caption font-weight-bold" style="color: rgba(255,255,255,0.5);">Cuotas incluidas:</p>
            <div class="d-flex flex-wrap gap-1 mt-1">
              <v-chip
                v-for="cid in pagoSeleccionado.cuotas_incluidas"
                :key="cid"
                size="x-small"
                color="primary"
                variant="tonal"
              >
                #{{ cid }}
              </v-chip>
            </div>
          </div>

          <!-- Comprobante en el diálogo -->
          <div v-if="pagoSeleccionado?.comprobante || pagoSeleccionado?.comprobante_url" class="mt-3">
            <div class="text-subtitle-2 font-weight-bold mb-2">Comprobante:</div>
            <v-img
              :src="pagoSeleccionado.comprobante || pagoSeleccionado.comprobante_url"
              max-height="200"
              contain
              class="rounded-lg comprobante-dialog"
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
          class="mt-3"
        ></v-text-field>

        <v-alert v-if="!accionAprobar" type="warning" class="mt-3" border="start" variant="tonal">
          El pago será rechazado y la cuota volverá a estado pendiente.
        </v-alert>
      </v-card-text>
      <v-card-actions class="pa-4">
        <v-btn variant="text" @click="dialogConfirmar = false" class="cancel-btn">
          Cancelar
        </v-btn>
        <v-spacer></v-spacer>
        <v-btn
          :color="accionAprobar ? 'success' : 'error'"
          @click="confirmarAccion"
          :loading="cargando"
          size="large"
          :disabled="accionAprobar && (!montoConfirmado || montoConfirmado <= 0)"
          variant="flat"
        >
          <v-icon start>
            {{ accionAprobar ? 'mdi-check' : 'mdi-close' }}
          </v-icon>
          {{ accionAprobar ? 'Aprobar' : 'Rechazar' }}
        </v-btn>
      </v-card-actions>
    </v-card>
  </v-dialog>
</template>

<script setup>
import { ref, onMounted, onUnmounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import { api } from '@/config/api'

const router = useRouter()

const pagosPendientes = ref([])
const dialogConfirmar = ref(false)
const pagoSeleccionado = ref(null)
const accionAprobar = ref(true)
const montoConfirmado = ref(0)
const cargando = ref(false)
const filtroModo = ref('todos')
let refreshInterval = null

// ========== COMPUTED ==========

const pagosFiltrados = computed(() => {
  if (filtroModo.value === 'todos') return pagosPendientes.value
  return pagosPendientes.value.filter(p => (p.modo_pago || 'cuota') === filtroModo.value)
})

const abonosCount = computed(() =>
  pagosPendientes.value.filter(p => p.modo_pago === 'abono').length
)

const liquidacionesCount = computed(() =>
  pagosPendientes.value.filter(p => p.modo_pago === 'liquidar').length
)

const adelantosCount = computed(() =>
  pagosPendientes.value.filter(p => p.modo_pago === 'adelantar').length
)

// ========== HELPERS MODO DE PAGO ==========

const modoPagoColor = (modo) => {
  const colores = { cuota: 'primary', adelantar: 'warning', liquidar: 'success', abono: 'info' }
  return colores[modo] || 'primary'
}

const modoPagoIcono = (modo) => {
  const iconos = {
    cuota: 'mdi-credit-card-outline',
    adelantar: 'mdi-fast-forward',
    liquidar: 'mdi-rocket-launch',
    abono: 'mdi-cash-plus'
  }
  return iconos[modo] || 'mdi-cash'
}

const modoPagoTexto = (modo) => {
  const textos = {
    cuota: 'Pago de cuota',
    adelantar: 'Adelanto',
    liquidar: 'Liquidación',
    abono: 'Abono parcial'
  }
  return textos[modo] || 'Pago'
}

// ========== HELPERS MÉTODO DE PAGO ==========

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

// ========== FORMATO ==========

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

// ========== API ==========

const cargarPagos = async () => {
  cargando.value = true
  try {
    const data = await api.get('/pagos/pendientes')
    pagosPendientes.value = Array.isArray(data) ? data : []
    console.log('📋 Pagos cargados:', pagosPendientes.value.length)

    // Debug: mostrar abonos
    const abonos = pagosPendientes.value.filter(p => p.modo_pago === 'abono')
    console.log('💰 Abonos encontrados:', abonos.length)
    abonos.forEach((a, i) => {
      console.log(`  Abono ${i + 1}:`, {
        id: a.id,
        monto_original: a.monto_original_bs,
        monto_reportado: a.monto_reportado_bs,
        saldo: (a.monto_original_bs || 0) - (a.monto_reportado_bs || 0)
      })
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
    const fullUrl = comprobante.startsWith('/')
      ? `https://financoop.onrender.com${comprobante}`
      : comprobante
    window.open(fullUrl, '_blank')
  }
}

// ========== LIFECYCLE ==========

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
.conciliacion-wrapper {
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
  color: rgba(255, 255, 255, 0.6) !important;
}

.header-title {
  font-size: 20px;
  font-weight: 700;
  color: #ffffff;
  margin-left: 8px;
}

.glass-card {
  background: rgba(255, 255, 255, 0.04) !important;
  backdrop-filter: blur(12px) !important;
  -webkit-backdrop-filter: blur(12px) !important;
  border: 1px solid rgba(255, 255, 255, 0.06);
  border-radius: 16px !important;
}

.section-title {
  font-size: 16px;
  font-weight: 600;
  color: #ffffff;
}

/* Stats */
.stat-card {
  border-radius: 12px !important;
}

.stat-value {
  font-size: 24px;
  font-weight: 700;
  color: #4facfe;
}

.stat-label {
  font-size: 11px;
  color: rgba(255, 255, 255, 0.4);
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

/* Filtros */
.gap-2 {
  gap: 8px;
}

/* Pagos list */
.pagos-list {
  display: flex;
  flex-direction: column;
}

.pago-item {
  transition: transform 0.2s ease, box-shadow 0.2s ease;
}

.pago-item:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3) !important;
}

.cliente-nombre {
  font-size: 15px;
  font-weight: 600;
  color: #ffffff;
}

.cliente-cedula {
  font-size: 12px;
  color: rgba(255, 255, 255, 0.4);
}

.modo-chip {
  font-weight: 500;
}

/* Abono alert */
.abono-alert {
  border-radius: 10px !important;
  background: rgba(255, 193, 7, 0.1) !important;
  border: 1px solid rgba(255, 193, 7, 0.2) !important;
}

.abono-text {
  font-size: 13px;
  color: #ffd54f;
}

.saldo-text {
  font-size: 13px;
  color: #ffd54f;
}

/* Cuotas alert */
.cuotas-alert {
  border-radius: 10px !important;
}

.cuotas-text {
  font-size: 12px;
  color: rgba(255, 255, 255, 0.8);
}

/* Montos */
.montos-section {
  background: rgba(255, 255, 255, 0.02);
  border-radius: 10px;
  padding: 12px;
}

.monto-label {
  font-size: 12px;
  color: rgba(255, 255, 255, 0.4);
}

.monto-valor {
  font-size: 14px;
  font-weight: 700;
  color: #4facfe;
}

.monto-usd {
  font-size: 12px;
  color: rgba(255, 255, 255, 0.5);
}

.monto-original {
  font-size: 13px;
  color: rgba(255, 255, 255, 0.4);
  text-decoration: line-through;
}

.monto-abonado {
  font-size: 14px;
  font-weight: 600;
  color: #4caf50;
}

.monto-saldo {
  font-size: 14px;
  font-weight: 700;
  color: #ffd54f;
}

/* Detalles */
.detalles-section {
  background: rgba(255, 255, 255, 0.02);
  border-radius: 10px;
  padding: 10px 12px;
}

.detalle-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 3px 0;
}

.detalle-label {
  font-size: 12px;
  color: rgba(255, 255, 255, 0.4);
}

.detalle-valor {
  font-size: 13px;
  color: rgba(255, 255, 255, 0.85);
}

.font-mono {
  font-family: 'Courier New', monospace;
  font-size: 12px;
}

/* Comprobante */
.comprobante-section {
  border-radius: 10px;
  overflow: hidden;
}

.comprobante-img {
  cursor: pointer;
  border: 1px solid rgba(255, 255, 255, 0.06);
  transition: opacity 0.2s;
}

.comprobante-img:hover {
  opacity: 0.9;
}

.comprobante-hint {
  color: rgba(255, 255, 255, 0.3);
}

.sin-comprobante {
  padding: 16px;
  background: rgba(255, 255, 255, 0.02);
  border-radius: 10px;
}

/* Botones */
.action-btn {
  font-weight: 600;
  height: 44px;
}

.action-btn-reject {
  min-width: 44px;
  height: 44px;
}

/* Dialog */
.dialog-card {
  background: #1a1f2e !important;
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 16px !important;
}

.dialog-title {
  font-size: 16px;
  font-weight: 600;
  padding: 16px 20px;
}

.comprobante-dialog {
  cursor: pointer;
  border: 1px solid rgba(255, 255, 255, 0.1);
}

.cancel-btn {
  color: rgba(255, 255, 255, 0.5) !important;
}

/* Responsive */
@media (min-width: 768px) {
  .page-content {
    padding: 24px 24px 80px;
    max-width: 900px;
    margin: 0 auto;
  }
}
</style>