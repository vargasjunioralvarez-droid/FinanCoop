<template>
  <div class="cuotas-wrapper">
    <div class="bg-gradient"></div>

    <div class="page-content">
      <!-- Header -->
      <div class="header-section">
        <div class="d-flex align-center">
          <v-btn icon variant="text" size="small" class="back-btn" @click="$router.push('/inicio')">
            <v-icon>mdi-arrow-left</v-icon>
          </v-btn>
          <span class="header-title">Mis Cuotas</span>
          <v-spacer />
          <v-chip class="badge-chip" size="small" color="primary" variant="tonal">
            {{ cuotasPendientes.length }} pendientes
          </v-chip>
        </div>
      </div>

      <!-- Filtros -->
      <v-chip-group v-model="filtro" mandatory class="filter-group">
        <v-chip value="todas" size="small" variant="outlined" filter>Todas</v-chip>
        <v-chip value="pendientes" size="small" variant="outlined" filter>Pendientes</v-chip>
        <v-chip value="vencidas" size="small" variant="outlined" filter color="error">Vencidas</v-chip>
        <v-chip value="pagadas" size="small" variant="outlined" filter color="success">Pagadas</v-chip>
      </v-chip-group>

      <!-- Resumen de deuda -->
      <v-card class="summary-card glass-card" elevation="0">
        <v-card-text class="pa-4">
          <div class="d-flex justify-space-between align-center">
            <div>
              <div class="summary-label">Deuda pendiente</div>
              <div class="summary-value">BS {{ formatearBS(totalDeudaBs) }}</div>
              <div class="summary-sub">Ref: ${{ formatearUSD(totalDeudaUsd) }}</div>
            </div>
            <div class="summary-badge">
              <span class="badge-number">{{ cuotasPendientes.length }}</span>
              <span class="badge-label">cuotas</span>
            </div>
          </div>
        </v-card-text>
      </v-card>

      <!-- Lista de cuotas -->
      <div v-if="cuotasFiltradas.length === 0" class="empty-state">
        <v-icon size="56" color="rgba(255,255,255,0.2)">mdi-inbox-outline</v-icon>
        <div class="empty-text">No hay cuotas en esta categoría</div>
      </div>

      <v-card
        v-for="c in cuotasFiltradas"
        :key="c.cuota_id || c.id"
        class="cuota-item glass-card"
        :class="{ 'cuota-selectable': c.estado === 'pendiente' || c.estado === 'conciliando' }"
        elevation="0"
      >
        <v-card-text class="pa-3">
          <div class="d-flex align-center">
            <v-avatar :color="avatarColor(c)" size="42" class="mr-3">
              <v-icon color="white" size="20">{{ avatarIcon(c) }}</v-icon>
            </v-avatar>
            <div class="flex-grow-1">
              <div class="d-flex align-center mb-1">
                <span class="cuota-title">{{ c.financiamiento_descripcion || 'Sin descripción' }}</span>
                <v-chip size="x-small" :color="chipColor(c)" variant="tonal" class="ml-2">
                  {{ chipLabel(c) }}
                </v-chip>
              </div>
              <div class="cuota-meta">Cuota #{{ c.cuota_numero || c.numero }} — {{ formatearFecha(c.fecha_vencimiento) }}</div>
              <div v-if="c.dias_atraso > 0" class="cuota-mora">{{ c.dias_atraso }} días de mora</div>
            </div>
            <div class="text-right ml-2">
              <div class="cuota-monto">BS {{ formatearBS(c.monto_total_bs || c.monto_bs) }}</div>
              <div class="cuota-usd">${{ formatearUSD(c.monto_total_usd_ref || c.monto_usd_ref) }}</div>
              <div v-if="c.monto_interes_bs > 0" class="cuota-interes">+{{ formatearBS(c.monto_interes_bs) }} mora</div>

              <!-- ⚡ MENÚ DE OPCIONES DE PAGO -->
              <v-menu v-if="c.puede_pagar !== false && c.estado !== 'pagada'" location="bottom end">
                <template v-slot:activator="{ props }">
                  <v-btn
                    color="success"
                    size="small"
                    variant="flat"
                    v-bind="props"
                    @click.stop
                    class="mt-1"
                  >
                    <v-icon start size="16">mdi-cash-fast</v-icon>
                    Pagar
                    <v-icon end size="16">mdi-chevron-down</v-icon>
                  </v-btn>
                </template>
                <v-list density="compact" class="bg-surface" style="min-width: 240px;">
                  <!-- Pagar solo esta cuota -->
                  <v-list-item @click="seleccionarCuota(c, 'cuota')">
                    <template v-slot:prepend>
                      <v-icon color="primary" size="18">mdi-credit-card-outline</v-icon>
                    </template>
                    <v-list-item-title style="font-size: 13px;">Pagar cuota completa</v-list-item-title>
                    <v-list-item-subtitle style="font-size: 11px;">
                      BS {{ formatearBS(c.monto_total_bs || c.monto_bs) }}
                    </v-list-item-subtitle>
                  </v-list-item>

                  <v-divider class="my-1"></v-divider>

                  <!-- 💰 ABONAR - NUEVA OPCIÓN -->
                  <v-list-item @click="abrirDialogoAbono(c)">
                    <template v-slot:prepend>
                      <v-icon color="info" size="18">mdi-cash-plus</v-icon>
                    </template>
                    <v-list-item-title style="font-size: 13px;">Abonar</v-list-item-title>
                    <v-list-item-subtitle style="font-size: 11px;">
                      Paga una parte del monto
                    </v-list-item-subtitle>
                  </v-list-item>

                  <v-divider class="my-1"></v-divider>

                  <!-- Adelantar pagos -->
                  <v-list-item @click="seleccionarCuota(c, 'adelantar')">
                    <template v-slot:prepend>
                      <v-icon color="warning" size="18">mdi-fast-forward</v-icon>
                    </template>
                    <v-list-item-title style="font-size: 13px;">Adelantar pagos</v-list-item-title>
                    <v-list-item-subtitle style="font-size: 11px;">
                      Desde cuota #{{ c.cuota_numero || c.numero }} en adelante
                    </v-list-item-subtitle>
                  </v-list-item>

                  <v-divider class="my-1"></v-divider>

                  <!-- Liquidar deuda -->
                  <v-list-item @click="seleccionarCuota(c, 'liquidar')">
                    <template v-slot:prepend>
                      <v-icon color="success" size="18">mdi-rocket-launch</v-icon>
                    </template>
                    <v-list-item-title style="font-size: 13px;">Liquidar deuda</v-list-item-title>
                    <v-list-item-subtitle style="font-size: 11px;">
                      <span class="text-success">⭐ Ahorra 5% de intereses</span>
                    </v-list-item-subtitle>
                  </v-list-item>
                </v-list>
              </v-menu>
            </div>
          </div>
        </v-card-text>
      </v-card>

      <!-- Info -->
      <v-card class="info-card glass-card" elevation="0">
        <v-card-text class="pa-3 d-flex align-center">
          <v-icon size="18" color="info" class="mr-2">mdi-information-outline</v-icon>
          <div class="info-text">
            ✅ Los montos en Bs se actualizan automáticamente con el tipo de cambio.<br>
            💵 Tu deuda se mantiene en DÓLARES (USD) para protegerte de la devaluación.<br>
            💰 Puedes <strong>abonar</strong> cualquier monto y el resto se mantiene pendiente.
          </div>
        </v-card-text>
      </v-card>
    </div>

    <!-- 💰 DIÁLOGO DE ABONO -->
    <v-dialog v-model="dialogoAbono" max-width="400" persistent>
      <v-card class="glass-card" style="background: #1a1f3a !important;">
        <v-card-title class="pa-4 pb-2">
          <div class="d-flex align-center">
            <v-icon color="info" class="mr-2">mdi-cash-plus</v-icon>
            <span style="font-size: 16px; font-weight: 600;">Realizar Abono</span>
          </div>
        </v-card-title>

        <v-card-text class="pa-4 pt-2">
          <div v-if="cuotaAbono" class="mb-4">
            <div style="font-size: 12px; color: rgba(255,255,255,0.5); margin-bottom: 4px;">
              Cuota #{{ cuotaAbono.cuota_numero || cuotaAbono.numero }}
            </div>
            <div style="font-size: 14px; color: #fff; margin-bottom: 8px;">
              {{ cuotaAbono.financiamiento_descripcion || 'Sin descripción' }}
            </div>
            <div class="d-flex justify-space-between" style="font-size: 13px;">
              <span style="color: rgba(255,255,255,0.5);">Monto total:</span>
              <span style="color: #4facfe; font-weight: 600;">
                BS {{ formatearBS(cuotaAbono.monto_total_bs || cuotaAbono.monto_bs) }}
              </span>
            </div>
            <div class="d-flex justify-space-between" style="font-size: 13px;">
              <span style="color: rgba(255,255,255,0.5);">Mínimo a abonar:</span>
              <span style="color: #ffd54f; font-weight: 600;">
                BS {{ formatearBS((cuotaAbono.monto_total_bs || cuotaAbono.monto_bs || 0) * 0.1) }}
              </span>
            </div>
          </div>

          <v-text-field
            v-model="montoAbono"
            label="Monto a abonar (Bs) *"
            placeholder="Ej: 100000"
            prepend-inner-icon="mdi-cash"
            variant="outlined"
            type="number"
            class="input-field"
            hide-details
            autofocus
          />

          <v-alert v-if="errorAbono" type="error" variant="tonal" density="compact" class="mt-3" style="border-radius: 10px;">
            {{ errorAbono }}
          </v-alert>

          <div class="d-flex gap-2 mt-4">
            <v-btn variant="text" color="rgba(255,255,255,0.5)" @click="cerrarDialogoAbono" class="flex-grow-1">
              Cancelar
            </v-btn>
            <v-btn color="info" @click="confirmarAbono" class="flex-grow-1" :disabled="!montoAbono">
              <v-icon start>mdi-check</v-icon>
              Abonar
            </v-btn>
          </div>
        </v-card-text>
      </v-card>
    </v-dialog>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useFinanCash } from '@/composables/useFinanCash'

const router = useRouter()
const route = useRoute()

const { 
  todasCuotas, 
  tasaActual,
  cuotasPendientes,
  totalDeudaBs,
  totalDeudaUsd,
  formatearBS,
  formatearUSD,
  formatearFecha,
  setCuotaSeleccionada
} = useFinanCash()

const filtro = ref('todas')
const financiamientoId = route.query.financiamiento_id

// 💰 ESTADO DEL DIÁLOGO DE ABONO
const dialogoAbono = ref(false)
const cuotaAbono = ref(null)
const montoAbono = ref('')
const errorAbono = ref('')

const cuotasFiltradas = computed(() => {
  let lista = [...todasCuotas.value]

  if (financiamientoId) {
    lista = lista.filter(c => c.financiamiento_id === Number(financiamientoId))
  }

  lista = lista.sort((a, b) => {
    const orden = { vencida: 0, conciliando: 1, pendiente: 2, pagada: 3 }
    const ea = estadoCuota(a)
    const eb = estadoCuota(b)
    if (orden[ea] !== orden[eb]) return orden[ea] - orden[eb]
    return new Date(a.fecha_vencimiento) - new Date(b.fecha_vencimiento)
  })

  if (filtro.value === 'pendientes') {
    lista = lista.filter(c => c.estado === 'pendiente' && new Date(c.fecha_vencimiento) >= new Date())
  } else if (filtro.value === 'vencidas') {
    lista = lista.filter(c => c.estado === 'pendiente' && new Date(c.fecha_vencimiento) < new Date())
  } else if (filtro.value === 'pagadas') {
    lista = lista.filter(c => c.estado === 'pagada')
  }

  return lista
})

function estadoCuota(c) {
  if (c.estado === 'pagada') return 'pagada'
  if (c.estado === 'conciliando') return 'conciliando'
  const hoy = new Date()
  const venc = new Date(c.fecha_vencimiento)
  if (venc < hoy) return 'vencida'
  const dias = Math.floor((venc - hoy) / (1000 * 60 * 60 * 24))
  if (dias <= 3) return 'urgente'
  return 'pendiente'
}

function avatarColor(c) {
  const est = estadoCuota(c)
  return { 
    pagada: 'success', 
    vencida: 'error', 
    urgente: 'warning',
    pendiente: 'warning',
    conciliando: 'info'
  }[est]
}

function avatarIcon(c) {
  const est = estadoCuota(c)
  return { 
    pagada: 'mdi-check', 
    vencida: 'mdi-alert', 
    urgente: 'mdi-clock-alert',
    pendiente: 'mdi-clock',
    conciliando: 'mdi-sync'
  }[est]
}

function chipColor(c) {
  const est = estadoCuota(c)
  return { 
    pagada: 'success', 
    vencida: 'error', 
    urgente: 'warning',
    pendiente: 'primary',
    conciliando: 'info'
  }[est]
}

function chipLabel(c) {
  const est = estadoCuota(c)
  return { 
    pagada: 'Pagada', 
    vencida: 'Vencida', 
    urgente: 'Próxima',
    pendiente: 'Pendiente',
    conciliando: 'Conciliando'
  }[est]
}

// 💰 ABRIR DIÁLOGO DE ABONO
function abrirDialogoAbono(c) {
  if (c.estado === 'pagada') return
  cuotaAbono.value = c
  montoAbono.value = ''
  errorAbono.value = ''
  dialogoAbono.value = true
}

// 💰 CERRAR DIÁLOGO DE ABONO
function cerrarDialogoAbono() {
  dialogoAbono.value = false
  cuotaAbono.value = null
  montoAbono.value = ''
  errorAbono.value = ''
}

// 💰 CONFIRMAR ABONO
function confirmarAbono() {
  if (!cuotaAbono.value || !montoAbono.value) return

  const monto = parseFloat(montoAbono.value)
  const montoTotal = cuotaAbono.value.monto_total_bs || cuotaAbono.value.monto_bs || 0
  const montoMinimo = montoTotal * 0.1 // 10% mínimo

  // Validaciones
  if (isNaN(monto) || monto <= 0) {
    errorAbono.value = 'Ingresa un monto válido'
    return
  }

  if (monto < montoMinimo) {
    errorAbono.value = `El abono mínimo es BS ${formatearBS(montoMinimo)} (10% del total)`
    return
  }

  if (monto >= montoTotal) {
    errorAbono.value = 'El monto es igual o mayor al total. Usa "Pagar cuota completa"'
    return
  }

  // Ir a pagar con modo abono
  setCuotaSeleccionada({
    ...cuotaAbono.value,
    modo_pago: 'abono',
    monto_bs: Math.round(monto * 100) / 100,
    monto_original: montoTotal,
    cuotas_incluidas: [cuotaAbono.value.cuota_id || cuotaAbono.value.id]
  })

  dialogoAbono.value = false
  router.push('/pagar')
}

// ⚡ SELECCIONAR CUOTA CON MODO DE PAGO
function seleccionarCuota(c, modo = 'cuota') {
  if (c.estado === 'pagada') return

  let montoPago = c.monto_total_bs || c.monto_bs || 0
  let cuotasIncluidas = [c.cuota_id || c.id]
  let montoOriginal = montoPago

  if (modo === 'adelantar') {
    const cuotasFuturas = todasCuotas.value.filter(
      x => x.financiamiento_id === c.financiamiento_id 
        && x.estado === 'pendiente'
        && (x.cuota_numero || x.numero) >= (c.cuota_numero || c.numero)
    )
    montoPago = cuotasFuturas.reduce((sum, x) => sum + (x.monto_total_bs || x.monto_bs || 0), 0)
    cuotasIncluidas = cuotasFuturas.map(x => x.cuota_id || x.id)
  }

  if (modo === 'liquidar') {
    const todasPendientes = todasCuotas.value.filter(
      x => x.financiamiento_id === c.financiamiento_id 
        && x.estado === 'pendiente'
    )
    montoOriginal = todasPendientes.reduce((sum, x) => sum + (x.monto_total_bs || x.monto_bs || 0), 0)
    montoPago = montoOriginal * 0.95
    cuotasIncluidas = todasPendientes.map(x => x.cuota_id || x.id)
  }

  setCuotaSeleccionada({
    ...c,
    modo_pago: modo,
    monto_bs: Math.round(montoPago * 100) / 100,
    monto_original: modo === 'liquidar' ? montoOriginal : null,
    cuotas_incluidas: cuotasIncluidas
  })

  router.push('/pagar')
}
</script>

<style scoped>
.cuotas-wrapper {
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

.header-section {
  margin-bottom: 16px;
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

.badge-chip {
  background: rgba(79, 172, 254, 0.15) !important;
  color: #4facfe !important;
}

.filter-group {
  display: flex;
  gap: 6px;
  margin-bottom: 16px;
}

.filter-group :deep(.v-chip) {
  background: rgba(255,255,255,0.04) !important;
  color: rgba(255,255,255,0.5) !important;
  border-color: rgba(255,255,255,0.06) !important;
}

.filter-group :deep(.v-chip--selected) {
  background: rgba(79, 172, 254, 0.15) !important;
  color: #4facfe !important;
  border-color: rgba(79, 172, 254, 0.3) !important;
}

.glass-card {
  background: rgba(255,255,255,0.04) !important;
  backdrop-filter: blur(12px) !important;
  -webkit-backdrop-filter: blur(12px) !important;
  border: 1px solid rgba(255,255,255,0.06);
  border-radius: 16px !important;
}

.summary-card {
  margin-bottom: 16px;
}

.summary-label {
  font-size: 11px;
  color: rgba(255,255,255,0.4);
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.summary-value {
  font-size: 24px;
  font-weight: 700;
  color: #ffd54f;
}

.summary-sub {
  font-size: 11px;
  color: rgba(255,255,255,0.3);
}

.summary-badge {
  text-align: center;
}

.badge-number {
  font-size: 28px;
  font-weight: 700;
  color: #ffffff;
  display: block;
}

.badge-label {
  font-size: 10px;
  color: rgba(255,255,255,0.3);
  text-transform: uppercase;
}

.cuota-item {
  margin-bottom: 10px;
  transition: all 0.3s ease;
  cursor: default;
}

.cuota-item.cuota-selectable {
  cursor: pointer;
}

.cuota-item.cuota-selectable:hover {
  transform: translateX(4px);
  background: rgba(255,255,255,0.06) !important;
}

.cuota-title {
  font-size: 13px;
  font-weight: 500;
  color: #ffffff;
}

.cuota-meta {
  font-size: 11px;
  color: rgba(255,255,255,0.4);
}

.cuota-mora {
  font-size: 11px;
  color: #f87171;
}

.cuota-monto {
  font-size: 15px;
  font-weight: 700;
  color: #ffffff;
}

.cuota-usd {
  font-size: 11px;
  color: rgba(255,255,255,0.3);
}

.cuota-interes {
  font-size: 10px;
  color: #f87171;
}

.empty-state {
  text-align: center;
  padding: 48px 0;
}

.empty-text {
  font-size: 14px;
  color: rgba(255,255,255,0.3);
  margin-top: 12px;
}

.info-card {
  margin-top: 16px;
}

.info-text {
  font-size: 11px;
  color: rgba(255,255,255,0.3);
  line-height: 1.5;
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
</style>