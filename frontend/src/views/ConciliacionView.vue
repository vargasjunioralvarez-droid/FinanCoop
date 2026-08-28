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
        <v-spacer />
        <v-btn size="small" color="info" variant="tonal" @click="cargarPagos" :loading="cargando">
          <v-icon start size="18">mdi-refresh</v-icon>
        </v-btn>
      </div>

      <!-- Stats Compactas -->
      <div class="stats-row mb-3">
        <div class="stat-item"><span class="stat-num">{{ pagosPendientes.length }}</span><span class="stat-lbl">Pendientes</span></div>
        <div class="stat-item"><span class="stat-num" style="color:#ffd54f;">{{ abonosCount }}</span><span class="stat-lbl">Abonos</span></div>
        <div class="stat-item"><span class="stat-num" style="color:#4caf50;">{{ liquidacionesCount }}</span><span class="stat-lbl">Liquidac.</span></div>
        <div class="stat-item"><span class="stat-num" style="color:#ff9800;">{{ adelantosCount }}</span><span class="stat-lbl">Adelantos</span></div>
      </div>

      <!-- Filtros VISIBLES -->
      <div class="filtros-row mb-3">
        <v-btn :color="filtroModo==='todos'?'primary':'grey-darken-1'" :variant="filtroModo==='todos'?'flat':'tonal'" @click="filtroModo='todos'" size="x-small" class="filtro-btn">Todos</v-btn>
        <v-btn :color="filtroModo==='cuota'?'primary':'grey-darken-1'" :variant="filtroModo==='cuota'?'flat':'tonal'" @click="filtroModo='cuota'" size="x-small" class="filtro-btn">Cuotas</v-btn>
        <v-btn :color="filtroModo==='abono'?'info':'grey-darken-1'" :variant="filtroModo==='abono'?'flat':'tonal'" @click="filtroModo='abono'" size="x-small" class="filtro-btn">Abonos</v-btn>
        <v-btn :color="filtroModo==='adelantar'?'warning':'grey-darken-1'" :variant="filtroModo==='adelantar'?'flat':'tonal'" @click="filtroModo='adelantar'" size="x-small" class="filtro-btn">Adelantos</v-btn>
        <v-btn :color="filtroModo==='liquidar'?'success':'grey-darken-1'" :variant="filtroModo==='liquidar'?'flat':'tonal'" @click="filtroModo='liquidar'" size="x-small" class="filtro-btn">Liquidac.</v-btn>
      </div>

      <!-- Lista de pagos -->
      <v-alert v-if="pagosFiltrados.length === 0" type="success" variant="tonal" class="rounded-lg">✅ No hay pagos pendientes</v-alert>

      <div v-else class="pagos-list">
        <v-card v-for="pago in pagosFiltrados" :key="pago.id" class="pago-item glass-card mb-3" elevation="0">
          <v-card-text class="pa-3">

            <!-- FILA 1: Cliente + Modo + Monto -->
            <div class="d-flex align-center justify-space-between flex-wrap gap-2 mb-2">
              <div class="d-flex align-center gap-2">
                <div>
                  <div class="cliente-nombre">{{ pago.cliente_nombre }}</div>
                  <div class="cliente-cedula">{{ pago.cliente_cedula }}</div>
                </div>
                <v-chip :color="modoPagoColor(pago.modo_pago)" size="x-small" variant="flat" class="text-white">{{ modoPagoTexto(pago.modo_pago) }}</v-chip>
              </div>
              <div class="text-right">
                <div class="monto-valor">BS {{ formatearNumero(pago.monto_reportado_bs) }}</div>
                <div class="monto-usd">${{ formatearNumero(pago.monto_reportado_usd) }}</div>
              </div>
            </div>

            <!-- Alerta de abono -->
            <v-alert v-if="pago.modo_pago === 'abono'" type="warning" variant="tonal" density="compact" class="mb-2 abono-alert">
              <div class="d-flex justify-space-between"><span style="color:#ffd54f;">💰 Abono parcial</span><span style="color:#ffd54f;">Saldo: BS {{ formatearNumero((pago.monto_original_bs||0)-(pago.monto_reportado_bs||0)) }}</span></div>
            </v-alert>

            <!-- FILA 2: Detalles -->
            <div class="detalle-inline">
              <span>#{{ pago.cuota_numero }}</span><span>·</span>
              <v-chip :color="colorMetodo(pago.metodo)" size="x-small" variant="tonal" class="text-white">{{ formatoMetodo(pago.metodo) }}</v-chip><span>·</span>
              <span class="font-mono">{{ pago.referencia || 'N/A' }}</span><span>·</span>
              <span>{{ formatearFecha(pago.fecha_reporte) }}</span>
            </div>

            <!-- Comprobante miniatura -->
            <div v-if="pago.comprobante || pago.comprobante_url" class="comprobante-mini mt-2" @click="verComprobante(pago.comprobante || pago.comprobante_url)">
              <v-img :src="pago.comprobante || pago.comprobante_url" max-height="80" max-width="120" cover class="rounded-lg" />
              <span class="text-caption ml-2" style="color:#4facfe;">📸 Ver comprobante</span>
            </div>

            <!-- Botones -->
            <div class="d-flex gap-2 mt-3">
              <v-btn color="success" variant="flat" class="flex-grow-1" size="small" @click="abrirConciliar(pago,true)" :disabled="pago.es_pago_padre===false">
                <v-icon start size="18">mdi-check</v-icon>{{ pago.modo_pago==='abono'?'Aprobar Abono':'Aprobar' }}
              </v-btn>
              <v-btn color="error" variant="outlined" size="small" @click="abrirConciliar(pago,false)" :disabled="pago.es_pago_padre===false">
                <v-icon size="18">mdi-close</v-icon>
              </v-btn>
            </div>
          </v-card-text>
        </v-card>
      </div>
    </div>
  </div>

  <!-- Dialog Confirmar -->
  <v-dialog v-model="dialogConfirmar" max-width="500">
    <v-card class="dialog-card">
      <v-card-title :class="accionAprobar?'bg-success':'bg-error'" class="text-white dialog-title">
        <v-icon start class="mr-2">{{ accionAprobar?'mdi-check-circle':'mdi-close-circle' }}</v-icon>
        {{ accionAprobar?'Aprobar Pago':'Rechazar Pago' }}
      </v-card-title>
      <v-card-text class="pt-4">
        <p class="text-white"><strong>Cliente:</strong> {{ pagoSeleccionado?.cliente_nombre }}</p>
        <p class="text-white"><strong>Cédula:</strong> {{ pagoSeleccionado?.cliente_cedula }}</p>
        <p class="text-white"><strong>Cuota:</strong> #{{ pagoSeleccionado?.cuota_numero }}</p>
        <template v-if="pagoSeleccionado?.modo_pago==='abono'">
          <v-alert type="warning" variant="tonal" density="compact" class="mb-2">
            <div class="d-flex justify-space-between"><span style="color:#ffd54f;">Total cuota:</span><span style="color:#fff;">BS {{ formatearNumero(pagoSeleccionado?.monto_original_bs) }}</span></div>
            <div class="d-flex justify-space-between"><span style="color:#ffd54f;">Abonado:</span><span style="color:#4caf50;">BS {{ formatearNumero(pagoSeleccionado?.monto_reportado_bs) }}</span></div>
            <v-divider class="my-1" />
            <div class="d-flex justify-space-between"><span style="color:#ffd54f;">Saldo:</span><span style="color:#ffd54f;">BS {{ formatearNumero((pagoSeleccionado?.monto_original_bs||0)-(pagoSeleccionado?.monto_reportado_bs||0)) }}</span></div>
          </v-alert>
        </template>
        <template v-else>
          <p class="text-white"><strong>Monto:</strong> BS {{ formatearNumero(pagoSeleccionado?.monto_reportado_bs) }}</p>
        </template>
        <p class="text-white"><strong>Ref:</strong> {{ pagoSeleccionado?.referencia || 'N/A' }}</p>
        <p class="text-white"><strong>Método:</strong> {{ formatoMetodo(pagoSeleccionado?.metodo) }}</p>
        <p class="text-white"><strong>Banco:</strong> {{ pagoSeleccionado?.banco_origen || 'N/A' }}</p>
        <div v-if="pagoSeleccionado?.comprobante" class="mt-2">
          <v-img :src="pagoSeleccionado.comprobante" max-height="200" contain class="rounded-lg" @click="verComprobante(pagoSeleccionado.comprobante)" />
        </div>
        <v-text-field v-if="accionAprobar" v-model.number="montoConfirmado" label="Monto a confirmar (BS)" type="number" prefix="BS" variant="outlined" density="comfortable" class="mt-3" hide-details />
        <v-alert v-else type="warning" class="mt-3" variant="tonal">El pago será rechazado.</v-alert>
      </v-card-text>
      <v-card-actions class="pa-4">
        <v-btn variant="text" @click="dialogConfirmar=false" style="color:rgba(255,255,255,0.5);">Cancelar</v-btn>
        <v-spacer />
        <v-btn :color="accionAprobar?'success':'error'" @click="confirmarAccion" :loading="cargando" variant="flat">
          {{ accionAprobar?'Aprobar':'Rechazar' }}
        </v-btn>
      </v-card-actions>
    </v-card>
  </v-dialog>
</template>

<script setup>
import { ref, onMounted, onUnmounted, computed } from 'vue'
import { api } from '@/config/api'

const pagosPendientes = ref([])
const dialogConfirmar = ref(false)
const pagoSeleccionado = ref(null)
const accionAprobar = ref(true)
const montoConfirmado = ref(0)
const cargando = ref(false)
const filtroModo = ref('todos')
let refreshInterval = null

const pagosFiltrados = computed(() => filtroModo.value==='todos' ? pagosPendientes.value : pagosPendientes.value.filter(p => (p.modo_pago||'cuota')===filtroModo.value))
const abonosCount = computed(() => pagosPendientes.value.filter(p => p.modo_pago==='abono').length)
const liquidacionesCount = computed(() => pagosPendientes.value.filter(p => p.modo_pago==='liquidar').length)
const adelantosCount = computed(() => pagosPendientes.value.filter(p => p.modo_pago==='adelantar').length)

const modoPagoColor = m => ({cuota:'primary',adelantar:'warning',liquidar:'success',abono:'info'}[m]||'primary')
const modoPagoIcono = m => ({cuota:'mdi-credit-card-outline',adelantar:'mdi-fast-forward',liquidar:'mdi-rocket-launch',abono:'mdi-cash-plus'}[m]||'mdi-cash')
const modoPagoTexto = m => ({cuota:'Cuota',adelantar:'Adelanto',liquidar:'Liquidación',abono:'Abono'}[m]||'Pago')
const colorMetodo = m => ({pago_movil:'purple',transferencia:'blue',zelle:'green',binance:'amber',efectivo:'grey'}[m]||'grey')
const formatoMetodo = m => ({pago_movil:'Pago Móvil',transferencia:'Transferencia',zelle:'Zelle',binance:'Binance',efectivo:'Efectivo'}[m]||m)
const formatearFecha = f => f ? new Date(f).toLocaleString('es-VE',{day:'2-digit',month:'2-digit',hour:'2-digit',minute:'2-digit'}):''
const formatearNumero = n => n ? Number(n).toLocaleString('es-VE',{minimumFractionDigits:2,maximumFractionDigits:2}):'0,00'

const cargarPagos = async () => {
  cargando.value=true
  try { const d = await api.get('/pagos/pendientes'); pagosPendientes.value = Array.isArray(d)?d:[] }
  catch(e) { pagosPendientes.value=[] }
  finally { cargando.value=false }
}

const abrirConciliar = (pago, aprobar) => {
  pagoSeleccionado.value=pago; accionAprobar.value=aprobar; montoConfirmado.value=pago.monto_reportado_bs||0; dialogConfirmar.value=true
}

import { ref, onMounted, onUnmounted, computed } from 'vue'
import { api } from '@/config/api'
import { useAuthStore } from '@/stores/auth'  // ✅ NUEVO

const auth = useAuthStore()  // ✅ NUEVO

// ... resto del código ...

const confirmarAccion = async () => {
  if(!pagoSeleccionado.value) return
  cargando.value=true
  try {
    await api.post('/pagos/conciliar',{
      pago_id:Number(pagoSeleccionado.value.id||pagoSeleccionado.value.pago_id),
      monto_confirmado_bs:accionAprobar.value?Number(montoConfirmado.value):0,
      estado:accionAprobar.value?'conciliado':'rechazado',
      conciliado_por: auth.username || 'admin'  // ✅ USA EL USERNAME REAL
    })
    dialogConfirmar.value=false; await cargarPagos()
  } catch(e) { alert('Error: '+(e.response?.data?.detail||e.message)) }
  finally { cargando.value=false }
}

const verComprobante = url => {
  if(!url) return
  if(url.startsWith('http')||url.startsWith('data:')){
    const w=window.open('','_blank')
    if(w) w.document.write(`<html><body style="margin:0;background:#0a0e1a;display:flex;justify-content:center;align-items:center;min-height:100vh;"><img src="${url}" style="max-width:95%;max-height:95vh;border-radius:8px;"></body></html>`)
  } else {
    window.open(url.startsWith('/')?`https://financoop-agd5.onrender.com${url}`:url,'_blank')
  }
}

onMounted(()=>{ cargarPagos(); refreshInterval=setInterval(cargarPagos,30000) })
onUnmounted(()=>{ if(refreshInterval) clearInterval(refreshInterval) })
</script>

<style scoped>
.conciliacion-wrapper{min-height:100vh;background:#0a0e1a;position:relative}
.bg-gradient{position:fixed;top:0;left:0;right:0;bottom:0;background:radial-gradient(ellipse at 20% 50%,rgba(79,172,254,0.08),transparent 70%),radial-gradient(ellipse at 80% 50%,rgba(99,102,241,0.08),transparent 70%);z-index:0}
.page-content{position:relative;z-index:1;padding:16px 16px 80px}
.back-btn{color:rgba(255,255,255,0.6)!important}
.header-title{font-size:20px;font-weight:700;color:#fff;margin-left:8px}
.glass-card{background:rgba(255,255,255,0.04)!important;backdrop-filter:blur(12px)!important;border:1px solid rgba(255,255,255,0.06);border-radius:16px!important}
.stats-row{display:flex;gap:8px}
.stat-item{flex:1;text-align:center;background:rgba(255,255,255,0.04);border-radius:12px;padding:8px 4px;border:1px solid rgba(255,255,255,0.06)}
.stat-num{font-size:18px;font-weight:700;color:#4facfe;display:block}
.stat-lbl{font-size:10px;color:rgba(255,255,255,0.4);text-transform:uppercase;letter-spacing:.5px}

/* Filtros visibles */
.filtros-row{display:flex;gap:6px;flex-wrap:wrap}
.filtro-btn{min-width:auto!important;padding:0 10px!important;height:28px!important;font-size:11px!important;font-weight:600!important;letter-spacing:0!important;text-transform:none!important}
.filtro-btn :deep(.v-btn__content){color:white!important}

.pago-item{transition:transform .15s ease}
.pago-item:hover{transform:translateY(-1px)}
.cliente-nombre{font-size:14px;font-weight:600;color:#fff}
.cliente-cedula{font-size:11px;color:rgba(255,255,255,0.4)}
.monto-valor{font-size:14px;font-weight:700;color:#4facfe}
.monto-usd{font-size:10px;color:rgba(255,255,255,0.5)}
.abono-alert{border-radius:10px!important;background:rgba(255,193,7,0.1)!important;border:1px solid rgba(255,193,7,0.2)!important;font-size:11px}
.detalle-inline{display:flex;align-items:center;gap:6px;flex-wrap:wrap;font-size:11px;color:rgba(255,255,255,0.5)}
.font-mono{font-family:monospace;font-size:11px}
.comprobante-mini{display:flex;align-items:center;cursor:pointer;font-size:12px}
.gap-2{gap:8px}
.text-white{color:#fff!important}

.dialog-card{background:#1a1f2e!important;border:1px solid rgba(255,255,255,0.08);border-radius:16px!important}
.dialog-title{font-size:16px;font-weight:600;padding:16px 20px}
@media(min-width:768px){.page-content{padding:24px 24px 80px;max-width:900px;margin:0 auto}}
</style>