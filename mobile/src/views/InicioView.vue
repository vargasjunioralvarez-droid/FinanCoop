<template>
  <div class="inicio-wrapper">
    <div class="bg-gradient"></div>

    <div class="page-content">
      <!-- Perfil -->
      <v-card class="profile-card glass-card" elevation="0">
        <v-card-text class="pa-4">
          <div class="d-flex align-center">
            <v-avatar size="56" :color="colorNivel(usuario.nivel)" class="mr-4">
              <v-icon size="32" color="white">{{ iconoNivel(usuario.nivel) }}</v-icon>
            </v-avatar>
            <div class="flex-grow-1">
              <h2 class="profile-name">{{ datosCliente?.cliente?.nombre || usuario.nombre }}</h2>
              <div class="d-flex align-center mt-1">
                <v-chip :color="colorNivel(usuario.nivel)" size="small" variant="tonal" class="mr-2">
                  <v-icon size="14" start>{{ iconoNivel(usuario.nivel) }}</v-icon>
                  {{ usuario.nivel }}
                </v-chip>
                <span class="profile-score">{{ usuario.score }} pts</span>
              </div>
              <div v-if="siguienteNivel" class="mt-2">
                <div class="d-flex justify-space-between progress-labels">
                  <span>{{ Math.round(progresoNivel) }}% hacia {{ siguienteNivel.key }}</span>
                  <span>{{ usuario.score }}/{{ siguienteNivel.max_score }}</span>
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

      <!-- Tasa -->
      <v-card class="dolar-card glass-card" elevation="0">
        <v-card-text class="pa-3 d-flex align-center">
          <v-icon color="#4facfe" size="24" class="mr-3">mdi-currency-usd</v-icon>
          <div class="flex-grow-1">
            <div class="dolar-label">Tipo de cambio</div>
            <div class="dolar-value">{{ formatearNumero(tasaActual) }} Bs/$</div>
          </div>
          <v-chip :color="variacionDolar >= 0 ? 'error' : 'success'" size="small" variant="tonal">
            <v-icon size="14" start>{{ variacionDolar >= 0 ? 'mdi-arrow-up' : 'mdi-arrow-down' }}</v-icon>
            {{ Math.abs(variacionDolar).toFixed(2) }}%
          </v-chip>
        </v-card-text>
      </v-card>

      <!-- Línea de crédito -->
      <v-card class="credit-card glass-card" elevation="0">
        <v-card-text class="pa-4">
          <div class="d-flex justify-space-between align-end mb-2">
            <div>
              <div class="credit-label">Disponible</div>
              <div class="credit-available">${{ formatearNumero(lineaDisponible) }}</div>
            </div>
            <div class="text-right">
              <div class="credit-label">Usado</div>
              <div class="credit-used">${{ formatearNumero(lineaUsada) }}</div>
            </div>
          </div>
          <v-progress-linear
            :model-value="(lineaUsada / (lineaUsada + lineaDisponible || 1)) * 100"
            :color="colorNivel(usuario.nivel)"
            height="8"
            rounded
            class="mb-1"
          />
          <div class="d-flex justify-space-between credit-footer">
            <span>${{ formatearNumero(lineaUsada) }} usado</span>
            <span>Límite: ${{ nivelActual.monto_max_usd || 0 }}</span>
          </div>
        </v-card-text>
      </v-card>

      <!-- Deuda -->
      <v-card v-if="totalDeudaBs > 0" class="deuda-card glass-card" elevation="0">
        <v-card-text class="pa-4">
          <div class="d-flex align-center">
            <v-icon color="#ffd54f" size="28" class="mr-3">mdi-alert-circle</v-icon>
            <div>
              <div class="deuda-label">Deuda Total</div>
              <div class="deuda-value">BS {{ formatearBS(totalDeudaBs) }}</div>
              <div class="deuda-ref">Ref: ${{ formatearUSD(totalDeudaUsd) }}</div>
            </div>
          </div>
        </v-card-text>
      </v-card>

      <v-alert v-else type="success" class="success-alert" variant="tonal" rounded="lg">
        ✅ No tienes deudas pendientes
      </v-alert>

      <!-- Mis Compras -->
      <div class="section-header">
        <h3>Mis Compras</h3>
        <v-chip size="small" variant="text" color="#4facfe">
          {{ financiamientos.length }} activas
        </v-chip>
      </div>

      <v-slide-group show-arrows class="slide-group">
        <v-slide-group-item v-for="fin in financiamientos" :key="fin.codigo || fin.id">
          <v-card class="compra-card glass-card" width="280" elevation="0" @click="irACuotas(fin)">
            <v-card-text class="pa-4">
              <div class="d-flex align-center mb-3">
                <v-avatar :color="fin.cuotas_atrasadas > 0 ? 'error' : 'success'" size="40" class="mr-3">
                  <v-icon color="white">{{ fin.cuotas_atrasadas > 0 ? 'mdi-alert' : 'mdi-shopping' }}</v-icon>
                </v-avatar>
                <div>
                  <div class="compra-title">{{ fin.descripcion }}</div>
                  <div class="compra-code">{{ fin.codigo }}</div>
                </div>
              </div>
              <div class="compra-monto">BS {{ formatearBS(fin.monto_total_bs) }}</div>
              <div class="compra-ref">Ref: ${{ formatearUSD(fin.monto_total_usd_ref) }}</div>

              <!-- 📸 FOTO DE FACTURA -->
              <div class="factura-section mt-2" @click.stop>
                <div v-if="fin.url_factura" class="d-flex align-center">
                  <v-icon size="14" color="success" class="mr-1">mdi-check-circle</v-icon>
                  <v-btn variant="text" size="x-small" color="info" density="compact" @click.stop="verFactura(fin)">
                    📸 Ver factura
                  </v-btn>
                </div>
                <div v-else class="d-flex align-center">
                  <v-btn variant="tonal" size="x-small" color="warning" density="compact" @click.stop="abrirCamaraFactura(fin)">
                    <v-icon size="14" class="mr-1">mdi-camera</v-icon> Subir factura
                  </v-btn>
                </div>
              </div>

              <div class="d-flex justify-space-between compra-progress-text">
                <span>Pagadas: {{ fin.cuotas_pagadas }}</span>
                <span>Pendientes: {{ fin.cuotas_pendientes }}</span>
              </div>
              <v-progress-linear :model-value="(fin.cuotas_pagadas / (fin.cuotas_total || 1)) * 100" color="success" height="6" rounded />

              <v-card v-if="fin.proxima_cuota" class="proxima-card" variant="outlined">
                <v-card-text class="pa-2">
                  <div class="d-flex justify-space-between align-center">
                    <div>
                      <div class="proxima-label">Próxima cuota</div>
                      <div class="proxima-info">#{{ fin.proxima_cuota.numero }} — {{ formatearFechaCorta(fin.proxima_cuota.fecha_vencimiento) }}</div>
                    </div>
                    <div class="text-right">
                      <div class="proxima-monto">BS {{ formatearBS(fin.proxima_cuota.monto_bs) }}</div>
                      <div class="proxima-usd">${{ formatearUSD(fin.proxima_cuota.monto_usd_ref) }}</div>
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
      <div v-if="cuotasProximas.length > 0" class="mt-4">
        <div class="section-header">
          <h3>Próximas cuotas</h3>
        </div>
        <v-card
          v-for="cuota in cuotasProximas.slice(0, 3)"
          :key="cuota.cuota_id || cuota.id"
          class="cuota-preview glass-card"
          :class="{ 'cuota-urgente': esUrgente(cuota) }"
          elevation="0"
          @click="irAPagar(cuota)"
        >
          <v-card-text class="pa-3 d-flex align-center">
            <div class="cuota-indicator" :class="estadoCuota(cuota)"></div>
            <div class="flex-grow-1">
              <div class="cuota-preview-title">Cuota {{ cuota.cuota_numero || cuota.numero }} — {{ cuota.financiamiento_descripcion }}</div>
              <div class="cuota-preview-date">{{ formatearFecha(cuota.fecha_vencimiento) }}</div>
            </div>
            <div class="text-right">
              <div class="cuota-preview-monto">BS {{ formatearBS(cuota.monto_total_bs || cuota.monto_bs) }}</div>
              <div class="cuota-preview-usd">${{ formatearUSD(cuota.monto_total_usd_ref || cuota.monto_usd_ref) }}</div>
            </div>
            <v-icon size="18" class="ml-2" color="rgba(255,255,255,0.2)">mdi-chevron-right</v-icon>
          </v-card-text>
        </v-card>
      </div>
    </div>

    <!-- DIÁLOGO VER FACTURA -->
    <v-dialog v-model="dialogoFactura" max-width="500">
      <v-card class="glass-card">
        <v-card-title class="d-flex align-center text-white">
          📸 Factura
          <v-spacer></v-spacer>
          <v-btn icon="mdi-close" variant="text" @click="dialogoFactura = false" color="white" />
        </v-card-title>
        <v-card-text class="text-center pa-4">
          <v-img v-if="facturaUrl" :src="facturaUrl" max-height="60vh" contain class="rounded-lg" />
        </v-card-text>
      </v-card>
    </v-dialog>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onActivated } from 'vue'
import { useRouter } from 'vue-router'
import { useFinanCash } from '@/composables/useFinanCash'
import { buildApiUrl } from '@/config'

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
  cargarDatos,
  formatearBS,
  formatearUSD,
  formatearNumero,
  formatearFecha,
  formatearFechaCorta,
  colorNivel,
  iconoNivel,
  setCuotaSeleccionada
} = useFinanCash()

// 📸 ESTADOS DE FACTURA
const dialogoFactura = ref(false)
const facturaUrl = ref('')

const variacionDolar = computed(() => {
  if (historialDolar.value.length < 2) return 0
  const ultimo = historialDolar.value[0]
  const anterior = historialDolar.value[1]
  if (!ultimo?.tasa || !anterior?.tasa) return 0
  return ((ultimo.tasa - anterior.tasa) / anterior.tasa) * 100
})

function irACuotas(fin) {
  router.push({ path: '/cuotas', query: { financiamiento_id: fin.id } })
}

function irAPagar(cuota) {
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

// 📸 FUNCIONES DE FACTURA
function abrirCamaraFactura(fin) {
  const input = document.createElement('input')
  input.type = 'file'
  input.accept = 'image/*'
  input.capture = 'environment'
  input.onchange = (e) => {
    const file = e.target.files[0]
    if (file) subirFactura(file, fin)
  }
  input.click()
}

async function subirFactura(file, fin) {
  try {
    const formData = new FormData()
    formData.append('file', file)
    
    const token = localStorage.getItem('financoop_token')
    const response = await fetch(buildApiUrl(`/upload/factura/${fin.id}`), {
      method: 'POST',
      headers: { 'Authorization': `Bearer ${token}` },
      body: formData
    })
    
    if (response.ok) {
      const data = await response.json()
      fin.url_factura = data.url
    } else {
      alert('Error al subir la factura')
    }
  } catch (e) {
    console.error('Error:', e)
  }
}

function verFactura(fin) {
  if (fin.url_factura) {
    facturaUrl.value = fin.url_factura
    dialogoFactura.value = true
  }
}

// ✅ FORZAR RECARGA CUANDO LA VISTA SE MONTA
onMounted(async () => {
  console.log('📱 InicioView montada, forzando carga de datos...')
  await cargarDatos()
  console.log('✅ Datos recargados en InicioView')
})

// ✅ RECARGAR CUANDO EL USUARIO VUELVE A LA VISTA
onActivated(async () => {
  console.log('🔄 InicioView activada, recargando datos...')
  await cargarDatos()
  console.log('✅ Datos recargados en InicioView (activada)')
})
</script>

<style scoped>
.inicio-wrapper { min-height: 100vh; background: #0a0e1a; position: relative; }
.bg-gradient { position: fixed; top: 0; left: 0; right: 0; bottom: 0; background: radial-gradient(ellipse at 20% 50%, rgba(79, 172, 254, 0.08), transparent 70%), radial-gradient(ellipse at 80% 50%, rgba(99, 102, 241, 0.08), transparent 70%); z-index: 0; }
.page-content { position: relative; z-index: 1; padding: 16px 16px 80px; }
.glass-card { background: rgba(255,255,255,0.04) !important; backdrop-filter: blur(12px) !important; -webkit-backdrop-filter: blur(12px) !important; border: 1px solid rgba(255,255,255,0.06); border-radius: 16px !important; }
.profile-card { margin-bottom: 12px; }
.profile-name { font-size: 18px; font-weight: 700; color: #ffffff; }
.profile-score { font-size: 12px; color: rgba(255,255,255,0.4); }
.progress-labels { font-size: 11px; color: rgba(255,255,255,0.4); }
.dolar-card { margin-bottom: 12px; }
.dolar-label { font-size: 11px; color: rgba(255,255,255,0.4); }
.dolar-value { font-size: 18px; font-weight: 700; color: #ffffff; }
.credit-card { margin-bottom: 12px; }
.credit-label { font-size: 11px; color: rgba(255,255,255,0.4); }
.credit-available { font-size: 24px; font-weight: 700; color: #4caf50; }
.credit-used { font-size: 18px; font-weight: 600; color: #ffd54f; }
.credit-footer { font-size: 11px; color: rgba(255,255,255,0.3); }
.deuda-card { margin-bottom: 12px; }
.deuda-label { font-size: 11px; color: rgba(255,255,255,0.4); }
.deuda-value { font-size: 22px; font-weight: 700; color: #ffd54f; }
.deuda-ref { font-size: 11px; color: rgba(255,255,255,0.3); }
.success-alert { background: rgba(76, 175, 80, 0.1) !important; color: #81c784 !important; border: 1px solid rgba(76, 175, 80, 0.15); border-radius: 12px !important; margin-bottom: 12px; }
.section-header { display: flex; align-items: center; justify-content: space-between; margin: 16px 0 12px; }
.section-header h3 { font-size: 16px; font-weight: 700; color: #ffffff; }
.slide-group { margin-bottom: 8px; }
.compra-card { transition: all 0.3s ease; cursor: pointer; }
.compra-card:hover { transform: translateY(-4px); background: rgba(255,255,255,0.06) !important; }
.compra-title { font-size: 13px; font-weight: 600; color: #ffffff; }
.compra-code { font-size: 11px; color: rgba(255,255,255,0.3); }
.compra-monto { font-size: 18px; font-weight: 700; color: #4facfe; }
.compra-ref { font-size: 11px; color: rgba(255,255,255,0.3); }
.compra-progress-text { font-size: 11px; color: rgba(255,255,255,0.4); }
.factura-section { padding: 4px 0; border-top: 1px solid rgba(255,255,255,0.04); border-bottom: 1px solid rgba(255,255,255,0.04); margin: 4px 0; }
.proxima-card { background: rgba(255,255,255,0.02) !important; border-color: rgba(255,255,255,0.06) !important; border-radius: 8px; margin-top: 8px; }
.proxima-label { font-size: 10px; color: rgba(255,255,255,0.3); }
.proxima-info { font-size: 12px; color: #ffffff; }
.proxima-monto { font-size: 13px; font-weight: 600; color: #ffffff; }
.proxima-usd { font-size: 10px; color: rgba(255,255,255,0.3); }
.cuota-preview { margin-bottom: 8px; transition: all 0.3s ease; cursor: pointer; }
.cuota-preview:hover { transform: translateX(4px); background: rgba(255,255,255,0.06) !important; }
.cuota-preview.cuota-urgente { border-left: 3px solid #ffd54f; }
.cuota-preview-title { font-size: 13px; font-weight: 500; color: #ffffff; }
.cuota-preview-date { font-size: 11px; color: rgba(255,255,255,0.4); }
.cuota-preview-monto { font-size: 14px; font-weight: 600; color: #ffffff; }
.cuota-preview-usd { font-size: 10px; color: rgba(255,255,255,0.3); }
.cuota-indicator { width: 8px; height: 8px; border-radius: 50%; margin-right: 12px; flex-shrink: 0; }
.cuota-indicator.pendiente { background: #4facfe; }
.cuota-indicator.urgente { background: #ffd54f; }
.cuota-indicator.vencida { background: #f87171; }
.cuota-indicator.pagada { background: #4caf50; }
</style>