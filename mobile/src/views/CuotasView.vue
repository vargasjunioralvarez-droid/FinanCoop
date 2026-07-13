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
        @click="seleccionarCuota(c)"
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
              <v-chip v-if="c.puede_pagar !== false && c.estado !== 'pagada'" color="success" size="x-small" class="mt-1" variant="flat">
                Pagar
              </v-chip>
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
            💵 Tu deuda se mantiene en DÓLARES (USD) para protegerte de la devaluación.
          </div>
        </v-card-text>
      </v-card>
    </div>
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
  formatearNumero,
  formatearFecha,
  setCuotaSeleccionada
} = useFinanCash()

const filtro = ref('todas')
const financiamientoId = route.query.financiamiento_id

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

function seleccionarCuota(c) {
  if (c.estado === 'pagada') return
  setCuotaSeleccionada(c)
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
</style>