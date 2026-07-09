<template>
  <v-container class="pa-4 inicio-view">
    <!-- Toast de notificación -->
    <transition name="toast">
      <v-alert
        v-if="notificacionVisible"
        type="warning"
        variant="tonal"
        class="mb-3"
        closable
        @click:close="notificacionVisible = false"
      >
        <template v-slot:prepend>
          <v-icon color="warning">mdi-bell-alert</v-icon>
        </template>
        <div class="text-body-2 font-weight-medium">{{ notificacionTitulo }}</div>
        <div class="text-caption">{{ notificacionMensaje }}</div>
      </v-alert>
    </transition>

    <!-- Perfil con nivel y progreso -->
    <v-card class="profile-card mb-4" elevation="4" :style="{ borderLeft: '4px solid ' + colorNivel(usuario.nivel) }">
      <v-card-text class="pa-4">
        <div class="d-flex align-center">
          <v-avatar size="56" :color="colorNivel(usuario.nivel)" class="mr-4">
            <v-icon size="32" color="white">{{ iconoNivel(usuario.nivel) }}</v-icon>
          </v-avatar>
          <div class="flex-grow-1">
            <h2 class="text-h6 font-weight-bold">{{ datosCliente?.cliente?.nombre || usuario.nombre }}</h2>
            <div class="d-flex align-center mt-1">
              <v-chip :color="colorNivel(usuario.nivel)" size="small" variant="tonal" class="mr-2">
                <v-icon size="14" start>{{ iconoNivel(usuario.nivel) }}</v-icon>
                {{ usuario.nivel }}
              </v-chip>
              <span class="text-caption text-medium-emphasis">{{ usuario.score }} pts</span>
            </div>
            <div v-if="siguienteNivel" class="mt-2">
              <div class="d-flex justify-space-between text-caption mb-1">
                <span class="text-medium-emphasis">{{ Math.round(progresoNivel) }}% hacia {{ siguienteNivel.key }}</span>
                <span class="font-weight-medium">{{ usuario.score }}/{{ siguienteNivel.max_score }}</span>
              </div>
              <v-progress-linear
                :model-value="progresoNivel"
                :color="colorNivel(siguienteNivel.key)"
                height="4"
                rounded
              />
            </div>
          </div>
        </div>
      </v-card-text>
    </v-card>

    <!-- Tasa con variación -->
    <v-card class="mb-4 dolar-card" elevation="2">
      <v-card-text class="pa-3 d-flex align-center">
        <v-icon color="primary" size="24" class="mr-3">mdi-currency-usd</v-icon>
        <div class="flex-grow-1">
          <div class="text-caption text-medium-emphasis">Tipo de cambio</div>
          <div class="text-h6 font-weight-medium" style="font-variant-numeric: tabular-nums;">
            {{ formatearNumero(tasaActual) }} Bs/$
          </div>
        </div>
        <v-chip
          :color="variacionDolar >= 0 ? 'error' : 'success'"
          size="small"
          variant="tonal"
        >
          <v-icon size="14" start>{{ variacionDolar >= 0 ? 'mdi-arrow-up' : 'mdi-arrow-down' }}</v-icon>
          {{ Math.abs(variacionDolar).toFixed(2) }}%
        </v-chip>
      </v-card-text>
    </v-card>

    <!-- Línea de crédito - SIEMPRE EN USD -->
    <v-card class="mb-4 credit-card" elevation="2">
      <v-card-text class="pa-4">
        <div class="d-flex justify-space-between align-end mb-2">
          <div>
            <div class="text-caption text-medium-emphasis">Disponible</div>
            <div class="text-h4 font-weight-bold" style="font-variant-numeric: tabular-nums; color: rgb(var(--v-theme-success));">
              ${{ formatearNumero(lineaDisponible) }}
            </div>
          </div>
          <div class="text-right">
            <div class="text-caption text-medium-emphasis">Usado</div>
            <div class="text-h5 font-weight-medium" style="font-variant-numeric: tabular-nums; color: rgb(var(--v-theme-warning));">
              ${{ formatearNumero(lineaUsada) }}
            </div>
          </div>
        </div>
        <v-progress-linear
          :model-value="(lineaUsada / (lineaUsada + lineaDisponible || 1)) * 100"
          :color="colorNivel(usuario.nivel)"
          height="8"
          rounded
          class="mb-1"
        />
        <div class="d-flex justify-space-between text-caption text-medium-emphasis">
          <span>${{ formatearNumero(lineaUsada) }} usado</span>
          <span>Límite: ${{ nivelActual.monto_max_usd || 0 }}</span>
        </div>
      </v-card-text>
    </v-card>

    <!-- Deuda Total - EN BOLÍVARES CON REFERENCIA EN USD -->
    <v-card 
      v-if="totalDeudaBs > 0" 
      class="deuda-card mb-4"
      elevation="4"
    >
      <v-card-text class="pa-4">
        <div class="d-flex align-center mb-2">
          <v-icon color="warning" size="28" class="mr-3">mdi-alert-circle</v-icon>
          <div>
            <div class="text-caption text-medium-emphasis">Deuda Total</div>
            <div class="text-h4 font-weight-bold" style="font-variant-numeric: tabular-nums;">
              BS {{ formatearBS(totalDeudaBs) }}
            </div>
            <div class="text-caption text-medium-emphasis">
              <!-- ✅ LA DEUDA EN USD SIEMPRE ES LA MISMA, LOS BS SE ACTUALIZAN -->
              Ref: ${{ formatearUSD(totalDeudaUsd) }} @ {{ formatearNumero(tasaActual) }} Bs/$
            </div>
          </div>
        </div>
      </v-card-text>
    </v-card>

    <v-alert v-else type="success" class="mb-4" variant="tonal">
      ✅ No tienes deudas pendientes
    </v-alert>

    <!-- Mis Compras -->
    <div class="d-flex align-center mb-3">
      <h3 class="text-h6 font-weight-bold">Mis Compras</h3>
      <v-spacer />
      <v-chip size="small" variant="text" color="primary">
        {{ financiamientos.length }} activas
      </v-chip>
    </div>

    <v-slide-group show-arrows class="mb-4">
      <v-slide-group-item
        v-for="fin in financiamientos"
        :key="fin.codigo || fin.id"
      >
        <v-card 
          class="compra-card mx-2" 
          width="280" 
          elevation="4"
          @click="irACuotas(fin)"
        >
          <v-card-text class="pa-4">
            <div class="d-flex align-center mb-3">
              <v-avatar :color="fin.cuotas_atrasadas > 0 ? 'error' : 'success'" size="40" class="mr-3">
                <v-icon color="white">
                  {{ fin.cuotas_atrasadas > 0 ? 'mdi-alert' : 'mdi-shopping' }}
                </v-icon>
              </v-avatar>
              <div>
                <div class="text-subtitle-2 font-weight-bold">{{ fin.descripcion }}</div>
                <div class="text-caption text-medium-emphasis">{{ fin.codigo }}</div>
              </div>
            </div>

            <!-- ✅ EL MONTO EN BS SE ACTUALIZA CON LA TASA -->
            <div class="text-h5 font-weight-bold text-primary mb-1" style="font-variant-numeric: tabular-nums;">
              BS {{ formatearBS(fin.monto_total_bs) }}
            </div>
            <!-- ✅ LA REFERENCIA EN USD SIEMPRE ES LA MISMA -->
            <div class="text-caption text-medium-emphasis mb-1">
              Ref: ${{ formatearUSD(fin.monto_total_usd_ref) }}
            </div>

            <div class="d-flex justify-space-between text-caption mb-2">
              <span>Pagadas: {{ fin.cuotas_pagadas }}</span>
              <span>Pendientes: {{ fin.cuotas_pendientes }}</span>
            </div>

            <v-progress-linear
              :model-value="(fin.cuotas_pagadas / (fin.cuotas_total || 1)) * 100"
              color="success"
              height="6"
              rounded
            />

            <!-- Próxima cuota -->
            <v-card v-if="fin.proxima_cuota" class="mt-3 proxima-cuota" variant="outlined">
              <v-card-text class="pa-2">
                <div class="d-flex justify-space-between align-center">
                  <div>
                    <div class="text-caption text-medium-emphasis">Próxima cuota</div>
                    <div class="text-body-2 font-weight-medium">
                      #{{ fin.proxima_cuota.numero }} — {{ formatearFechaCorta(fin.proxima_cuota.fecha_vencimiento) }}
                    </div>
                  </div>
                  <div class="text-right">
                    <!-- ✅ MONTO EN BS ACTUALIZADO -->
                    <div class="text-body-2 font-weight-medium" style="font-variant-numeric: tabular-nums;">
                      BS {{ formatearBS(fin.proxima_cuota.monto_bs) }}
                    </div>
                    <!-- ✅ USD SIEMPRE IGUAL -->
                    <div class="text-caption text-medium-emphasis">
                      ${{ formatearUSD(fin.proxima_cuota.monto_usd_ref) }}
                    </div>
                  </div>
                </div>
              </v-card-text>
            </v-card>

            <v-btn
              v-if="fin.proxima_cuota && fin.proxima_cuota.puede_pagar !== false"
              color="success"
              block
              size="small"
              class="mt-3"
              rounded="pill"
              @click.stop="irAPagar(fin.proxima_cuota)"
            >
              <v-icon start size="16">mdi-credit-card</v-icon>
              Pagar Cuota {{ fin.proxima_cuota.numero }}
            </v-btn>
          </v-card-text>
        </v-card>
      </v-slide-group-item>
    </v-slide-group>

    <!-- Próximas cuotas -->
    <div v-if="cuotasProximas.length > 0" class="mb-4">
      <div class="text-subtitle-1 font-weight-medium mb-2 d-flex align-center">
        <v-icon size="18" class="mr-1">mdi-calendar-clock</v-icon>
        Próximas cuotas
      </div>
      <v-card
        v-for="cuota in cuotasProximas.slice(0, 3)"
        :key="cuota.cuota_id || cuota.id"
        class="mb-2 cuota-card"
        :class="{ 'cuota-urgente': esUrgente(cuota) }"
        elevation="1"
        @click="irAPagar(cuota)"
      >
        <v-card-text class="pa-3 d-flex align-center">
          <div class="cuota-indicator mr-3" :class="estadoCuota(cuota)"></div>
          <div class="flex-grow-1">
            <div class="text-body-2 font-weight-medium">
              Cuota {{ cuota.cuota_numero || cuota.numero }} — {{ cuota.financiamiento_descripcion }}
            </div>
            <div class="text-caption text-medium-emphasis">
              {{ formatearFecha(cuota.fecha_vencimiento) }}
              <span v-if="diasRestantes(cuota) !== null" :class="diasRestantes(cuota) <= 3 ? 'text-error font-weight-medium' : ''">
                {{ diasRestantesTexto(cuota) }}
              </span>
            </div>
          </div>
          <div class="text-right">
            <!-- ✅ MONTO EN BS ACTUALIZADO -->
            <div class="text-body-1 font-weight-medium" style="font-variant-numeric: tabular-nums;">
              BS {{ formatearBS(cuota.monto_total_bs || cuota.monto_bs) }}
            </div>
            <!-- ✅ USD SIEMPRE IGUAL -->
            <div class="text-caption text-medium-emphasis">
              ${{ formatearUSD(cuota.monto_total_usd_ref || cuota.monto_usd_ref) }}
            </div>
          </div>
          <v-icon size="18" class="ml-2 text-medium-emphasis">mdi-chevron-right</v-icon>
        </v-card-text>
      </v-card>
    </div>
  </v-container>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useFinanCash } from '@/composables/useFinanCash'

const router = useRouter()

const { 
  usuario, 
  datosCliente,
  nivelActual,
  siguienteNivel,
  progresoNivel,
  lineaUsada,
  lineaDisponible,
  tasaActual,
  financiamientos,
  cuotasProximas,
  totalDeudaBs,
  totalDeudaUsd,
  historialDolar,
  notificaciones,
  formatearBS,
  formatearUSD,
  formatearNumero,
  formatearFecha,
  formatearFechaCorta,
  colorNivel,
  iconoNivel,
  setCuotaSeleccionada
} = useFinanCash()

const notificacionVisible = ref(false)
const notificacionTitulo = ref('')
const notificacionMensaje = ref('')

const variacionDolar = computed(() => {
  if (historialDolar.value.length < 2) return 0
  const ultimo = historialDolar.value[0]
  const anterior = historialDolar.value[1]
  if (!ultimo?.tasa || !anterior?.tasa) return 0
  return ((ultimo.tasa - anterior.tasa) / anterior.tasa) * 100
})

function irACuotas(fin) {
  console.log('📋 Ver cuotas de:', fin.codigo)
  router.push({
    path: '/cuotas',
    query: { financiamiento_id: fin.id }
  })
}

function irAPagar(cuota) {
  console.log('💰 Pagar cuota:', cuota)
  setCuotaSeleccionada(cuota)
  router.push('/pagar')
}

function esUrgente(cuota) {
  const hoy = new Date()
  const venc = new Date(cuota.fecha_vencimiento)
  const dias = Math.floor((venc - hoy) / (1000 * 60 * 60 * 24))
  return dias >= 0 && dias <= 3
}

function estadoCuota(cuota) {
  if (cuota.estado === 'pagada') return 'pagada'
  const hoy = new Date()
  const venc = new Date(cuota.fecha_vencimiento)
  if (venc < hoy) return 'vencida'
  const dias = Math.floor((venc - hoy) / (1000 * 60 * 60 * 24))
  if (dias <= 3) return 'urgente'
  return 'pendiente'
}

function diasRestantes(cuota) {
  if (cuota.estado === 'pagada') return null
  const hoy = new Date()
  const venc = new Date(cuota.fecha_vencimiento)
  return Math.floor((venc - hoy) / (1000 * 60 * 60 * 24))
}

function diasRestantesTexto(cuota) {
  const dias = diasRestantes(cuota)
  if (dias === null) return ''
  if (dias < 0) return ` (${Math.abs(dias)} días vencida)`
  if (dias === 0) return ' (vence hoy)'
  if (dias === 1) return ' (mañana)'
  return ` (${dias} días)`
}

onMounted(() => {
  const notif = notificaciones.value.find(n => n.tipo === 'recordatorio' && !n.leida)
  if (notif) {
    notificacionTitulo.value = notif.titulo
    notificacionMensaje.value = notif.mensaje
    notificacionVisible.value = true
    setTimeout(() => { notificacionVisible.value = false }, 5000)
  }
})
</script>

<style scoped>
.inicio-view { padding-bottom: 80px; }
.profile-card {
  border-radius: 16px;
  transition: transform 0.2s ease, box-shadow 0.2s ease;
}
.profile-card:hover { transform: translateY(-2px); }
.dolar-card {
  border-radius: 12px;
  transition: all 0.2s ease;
}
.dolar-card:hover { background: rgba(var(--v-theme-primary), 0.03); }
.credit-card {
  border-radius: 16px;
  border-left: 4px solid v-bind('colorNivel(usuario.nivel)');
}
.deuda-card {
  border-radius: 16px;
  border-left: 4px solid rgb(var(--v-theme-warning));
}
.compra-card {
  border-radius: 16px;
  transition: all 0.2s ease;
  cursor: pointer;
}
.compra-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 8px 24px rgba(0,0,0,0.12) !important;
}
.proxima-cuota {
  border-radius: 8px;
  background: rgba(var(--v-theme-primary), 0.03);
}
.cuota-card {
  cursor: pointer;
  transition: all 0.2s ease;
  border-left: 3px solid transparent;
  border-radius: 12px;
}
.cuota-card:hover {
  transform: translateX(4px);
  box-shadow: 0 2px 8px rgba(0,0,0,0.08) !important;
}
.cuota-card.cuota-urgente { border-left-color: rgb(var(--v-theme-warning)); }
.cuota-indicator {
  width: 10px;
  height: 10px;
  border-radius: 50%;
  flex-shrink: 0;
}
.cuota-indicator.pendiente { background: rgb(var(--v-theme-primary)); }
.cuota-indicator.urgente { background: rgb(var(--v-theme-warning)); animation: pulse 2s infinite; }
.cuota-indicator.vencida { background: rgb(var(--v-theme-error)); }
.cuota-indicator.pagada { background: rgb(var(--v-theme-success)); }
@keyframes pulse {
  0%, 100% { opacity: 1; transform: scale(1); box-shadow: 0 0 0 0 rgba(var(--v-theme-warning), 0.4); }
  50% { opacity: 0.7; transform: scale(1.2); box-shadow: 0 0 0 6px rgba(var(--v-theme-warning), 0); }
}
.toast-enter-active,
.toast-leave-active {
  transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
}
.toast-enter-from { transform: translateY(-20px); opacity: 0; }
.toast-leave-to { transform: translateY(-20px); opacity: 0; }
</style>