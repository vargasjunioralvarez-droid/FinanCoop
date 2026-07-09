<template>
  <v-container class="pa-4 cuotas-view">
    <div class="d-flex align-center mb-3">
      <v-btn icon variant="text" size="small" @click="$router.push('/')">
        <v-icon>mdi-arrow-left</v-icon>
      </v-btn>
      <span class="text-h6 font-weight-medium ml-2">Mis Cuotas</span>
      <v-spacer />
      <v-chip size="small" color="primary" variant="tonal">
        {{ cuotasPendientes.length }} pendientes
      </v-chip>
    </div>

    <v-chip-group v-model="filtro" mandatory class="mb-3">
      <v-chip value="todas" size="small" variant="outlined" filter>Todas</v-chip>
      <v-chip value="pendientes" size="small" variant="outlined" filter>Pendientes</v-chip>
      <v-chip value="vencidas" size="small" variant="outlined" filter color="error">Vencidas</v-chip>
      <v-chip value="pagadas" size="small" variant="outlined" filter color="success">Pagadas</v-chip>
    </v-chip-group>

    <v-card class="mb-3 resumen-card" elevation="2">
      <v-card-text class="pa-4">
        <div class="d-flex justify-space-between align-center">
          <div>
            <div class="text-caption text-medium-emphasis">Deuda pendiente</div>
            <div class="text-h4 font-weight-bold" style="font-variant-numeric: tabular-nums; color: rgb(var(--v-theme-warning));">
              BS {{ formatearBS(totalDeudaBs) }}
            </div>
            <div class="text-caption text-medium-emphasis">
              Ref: ${{ formatearUSD(totalDeudaUsd) }} @ {{ formatearNumero(tasaActual) }} Bs/$
            </div>
          </div>
          <div class="text-right">
            <div class="text-caption text-medium-emphasis">Cuotas</div>
            <div class="text-h5 font-weight-medium">{{ cuotasPendientes.length }}</div>
          </div>
        </div>
      </v-card-text>
    </v-card>

    <div v-if="cuotasFiltradas.length === 0" class="text-center py-8">
      <v-icon size="48" color="medium-emphasis" class="mb-2">mdi-inbox-outline</v-icon>
      <div class="text-body-1 text-medium-emphasis">No hay cuotas {{ filtro !== 'todas' ? 'en esta categoría' : '' }}</div>
    </div>

    <v-card
      v-for="c in cuotasFiltradas"
      :key="c.cuota_id || c.id"
      class="mb-2 cuota-item"
      :class="{ 'cuota-seleccionable': c.estado === 'pendiente' || c.estado === 'conciliando' }"
      elevation="1"
      @click="seleccionarCuota(c)"
    >
      <v-card-text class="pa-3">
        <div class="d-flex align-center">
          <v-avatar :color="avatarColor(c)" size="40" class="mr-3">
            <v-icon color="white" size="20">{{ avatarIcon(c) }}</v-icon>
          </v-avatar>
          <div class="flex-grow-1">
            <div class="d-flex align-center mb-1">
              <span class="text-body-2 font-weight-medium">{{ c.financiamiento_descripcion || 'Sin descripción' }}</span>
              <v-chip size="x-small" :color="chipColor(c)" variant="tonal" class="ml-2">
                {{ chipLabel(c) }}
              </v-chip>
            </div>
            <div class="text-caption text-medium-emphasis">
              Cuota #{{ c.cuota_numero || c.numero }} — {{ formatearFecha(c.fecha_vencimiento) }}
            </div>
            <div v-if="c.dias_atraso > 0" class="text-caption text-error">
              {{ c.dias_atraso }} días de mora
            </div>
          </div>
          <div class="text-right ml-2">
            <!-- ✅ MONTO EN BS ACTUALIZADO -->
            <div class="text-h6 font-weight-bold" style="font-variant-numeric: tabular-nums;">
              BS {{ formatearBS(c.monto_total_bs || c.monto_bs) }}
            </div>
            <!-- ✅ USD SIEMPRE IGUAL -->
            <div class="text-caption text-medium-emphasis">
              ${{ formatearUSD(c.monto_total_usd_ref || c.monto_usd_ref) }}
            </div>
            <div v-if="c.monto_interes_bs > 0" class="text-caption text-error">
              +{{ formatearBS(c.monto_interes_bs) }} mora
            </div>
            <v-chip v-if="c.puede_pagar !== false && c.estado !== 'pagada'" color="success" size="small" class="mt-1" variant="flat">
              Pagar
            </v-chip>
          </div>
        </div>
      </v-card-text>
    </v-card>

    <v-card class="mt-3 info-card" variant="outlined">
      <v-card-text class="pa-3 d-flex align-center">
        <v-icon size="18" color="info" class="mr-2">mdi-information-outline</v-icon>
        <div class="text-caption text-medium-emphasis">
          ✅ Los montos en Bs se actualizan automáticamente con el tipo de cambio.<br>
          💵 Tu deuda se mantiene en DÓLARES (USD) para protegerte de la devaluación.
        </div>
      </v-card-text>
    </v-card>
  </v-container>
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
  
  // Filtrar por financiamiento si viene en query
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
  if (c.estado === 'pagada') {
    console.log('❌ Esta cuota ya está pagada')
    return
  }
  console.log('✅ Seleccionando cuota:', c)
  setCuotaSeleccionada(c)
  router.push('/pagar')
}
</script>

<style scoped>
.cuotas-view { padding-bottom: 80px; }
.resumen-card {
  border-left: 4px solid rgb(var(--v-theme-warning));
  border-radius: 12px;
}
.cuota-item {
  transition: all 0.2s ease;
  border-left: 3px solid transparent;
  border-radius: 12px;
}
.cuota-item.cuota-seleccionable { cursor: pointer; }
.cuota-item.cuota-seleccionable:hover {
  transform: translateX(4px);
  box-shadow: 0 2px 8px rgba(0,0,0,0.08) !important;
}
.info-card {
  border-style: dashed;
  opacity: 0.8;
  border-radius: 12px;
}
</style>