<template>
  <v-container fluid class="pa-0">
    <div class="background-gradient"></div>
    
    <v-row class="ma-0">
      <v-col cols="12" class="pa-4">
        <!-- HEADER PREMIUM -->
        <div class="header-premium d-flex align-center justify-space-between flex-wrap">
          <div class="d-flex align-center">
            <div class="icon-wrapper pulse-animation">
              <v-icon size="32" color="white">mdi-cart-check</v-icon>
            </div>
            <div class="ml-3">
              <h1 class="text-h4 font-weight-bold text-white">Mis Ventas del Día</h1>
              <p class="text-subtitle-2 text-white" style="opacity: 0.7;">{{ fechaHoy }} | 🏪 {{ tiendaNombre || 'Cargando...' }}</p>
            </div>
          </div>
          <div class="d-flex align-center" style="gap: 8px;">
            <v-btn v-if="ventasHoy.length > 0" color="#4facfe" size="small" rounded="pill" @click="imprimirReporte" elevation="0">
              <v-icon start>mdi-printer</v-icon>Imprimir
            </v-btn>
            <v-chip class="step-chip" color="transparent" size="large">
              <span class="text-white font-weight-bold">{{ ventasHoy.length }} Ventas Hoy</span>
            </v-chip>
          </div>
        </div>

        <!-- KPIs PREMIUM -->
        <v-row class="mt-4">
          <v-col cols="12" sm="3">
            <v-card class="kpi-card glass-card rounded-xl" elevation="0">
              <v-card-text class="pa-4 text-center">
                <div class="kpi-icon-wrapper mb-2" style="background: rgba(76,175,80,0.15);">
                  <v-icon size="28" color="#4caf50">mdi-shopping</v-icon>
                </div>
                <div class="kpi-number text-success">{{ ventasHoy.length }}</div>
                <div class="kpi-label">Ventas Hoy</div>
              </v-card-text>
            </v-card>
          </v-col>
          <v-col cols="12" sm="3">
            <v-card class="kpi-card glass-card rounded-xl" elevation="0">
              <v-card-text class="pa-4 text-center">
                <div class="kpi-icon-wrapper mb-2" style="background: rgba(79,172,254,0.15);">
                  <v-icon size="28" color="#4facfe">mdi-cash-multiple</v-icon>
                </div>
                <div class="kpi-number text-primary">BS {{ formatearBS(totalHoy) }}</div>
                <div class="kpi-label">Total Financiado</div>
              </v-card-text>
            </v-card>
          </v-col>
          <v-col cols="12" sm="3">
            <v-card class="kpi-card glass-card rounded-xl" elevation="0">
              <v-card-text class="pa-4 text-center">
                <div class="kpi-icon-wrapper mb-2" style="background: rgba(255,213,79,0.15);">
                  <v-icon size="28" color="#ffd54f">mdi-cash-check</v-icon>
                </div>
                <div class="kpi-number text-warning">BS {{ formatearBS(totalEntrada) }}</div>
                <div class="kpi-label">Entradas Cobradas</div>
              </v-card-text>
            </v-card>
          </v-col>
          <v-col cols="12" sm="3">
            <v-card class="kpi-card glass-card rounded-xl" elevation="0">
              <v-card-text class="pa-4 text-center">
                <div class="kpi-icon-wrapper mb-2" style="background: rgba(244,67,54,0.15);">
                  <v-icon size="28" color="#f44336">mdi-clock-outline</v-icon>
                </div>
                <div class="kpi-number text-error">BS {{ formatearBS(totalPendiente) }}</div>
                <div class="kpi-label">Pendiente por Cobrar</div>
              </v-card-text>
            </v-card>
          </v-col>
        </v-row>

        <!-- TABLA DE VENTAS -->
        <v-row class="mt-4">
          <v-col cols="12">
            <v-card id="reporte-ventas" class="glass-card rounded-xl" elevation="0">
              <v-card-title class="text-h6 font-weight-bold text-white pa-4">
                <v-icon color="#4facfe" class="mr-2">mdi-clipboard-text</v-icon>
                Ventas de Hoy
                <v-spacer></v-spacer>
                <v-chip v-if="ventasHoy.length > 0" color="#4facfe" variant="tonal" size="small">{{ ventasHoy.length }} registros</v-chip>
              </v-card-title>
              
              <v-card-text class="pa-4 pt-0">
                <div class="table-wrapper">
                  <v-table class="premium-table">
                    <thead>
                      <tr>
                        <th>Código</th>
                        <th>Cliente</th>
                        <th class="text-right">Monto</th>
                        <th class="text-right">Entrada</th>
                        <th class="text-right">Pendiente</th>
                        <th class="text-center">Cuotas</th>
                        <th class="text-right">Hora</th>
                      </tr>
                    </thead>
                    <tbody>
                      <tr v-for="v in ventasHoy" :key="v.id" class="fade-in">
                        <td>
                          <v-chip size="x-small" color="#4facfe" variant="tonal">{{ v.codigo }}</v-chip>
                        </td>
                        <td>
                          <div class="d-flex align-center">
                            <v-avatar size="28" color="rgba(79,172,254,0.2)" class="mr-2">
                              <span class="text-caption" style="color: #4facfe;">{{ (v.cliente_nombre || '?').charAt(0) }}</span>
                            </v-avatar>
                            <span class="text-white">{{ v.cliente_nombre }}</span>
                          </div>
                        </td>
                        <td class="text-right">
                          <span class="text-white font-weight-bold">BS {{ formatearBS(v.monto_total_bs) }}</span>
                        </td>
                        <td class="text-right">
                          <span class="text-success font-weight-bold">BS {{ formatearBS(v.monto_entrada_bs) }}</span>
                        </td>
                        <td class="text-right">
                          <span class="text-error font-weight-bold">BS {{ formatearBS((v.monto_total_bs || 0) - (v.monto_entrada_bs || 0)) }}</span>
                        </td>
                        <td class="text-center">
                          <v-chip size="x-small" color="rgba(255,255,255,0.1)" variant="flat">{{ v.cuotas_aprobadas }}</v-chip>
                        </td>
                        <td class="text-right">
                          <span style="color: rgba(255,255,255,0.4); font-size: 0.8rem;">{{ formatearHora(v.creado_en) }}</span>
                        </td>
                      </tr>
                    </tbody>
                  </v-table>
                </div>

                <div v-if="ventasHoy.length === 0" class="empty-state glass-effect mt-2 rounded-xl">
                  <v-icon size="48" color="rgba(255,255,255,0.1)">mdi-cart-off</v-icon>
                  <div class="text-body-1 mt-2" style="color: rgba(255,255,255,0.4);">No hay ventas registradas hoy</div>
                  <div class="text-caption" style="color: rgba(255,255,255,0.2);">Las ventas que realices aparecerán aquí</div>
                </div>
              </v-card-text>
            </v-card>
          </v-col>
        </v-row>
      </v-col>
    </v-row>
  </v-container>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { api } from '@/config/api'

const ventasHoy = ref([])
const tiendaNombre = ref('')

const fechaHoy = new Date().toLocaleDateString('es-VE', { weekday: 'long', day: 'numeric', month: 'long' })
const totalHoy = computed(() => ventasHoy.value.reduce((s, v) => s + (v.monto_total_bs || 0), 0))
const totalEntrada = computed(() => ventasHoy.value.reduce((s, v) => s + (v.monto_entrada_bs || 0), 0))
const totalPendiente = computed(() => ventasHoy.value.reduce((s, v) => s + ((v.monto_total_bs || 0) - (v.monto_entrada_bs || 0)), 0))

const formatearBS = (m) => m ? Number(m).toLocaleString('es-VE', { minimumFractionDigits: 2 }) : '0,00'
const formatearHora = (f) => f ? new Date(f).toLocaleTimeString('es-VE', { hour: '2-digit', minute: '2-digit' }) : ''

const cargarVentas = async () => {
  try {
    const data = await api.get('/financiamientos')
    const hoy = new Date().toDateString()
    ventasHoy.value = data.filter(f => new Date(f.creado_en).toDateString() === hoy)
  } catch (e) {}
}

const cargarUsuario = async () => {
  try {
    const data = await api.get('/auth/verificar')
    tiendaNombre.value = data.tienda_nombre || ''
  } catch (e) {}
}

const imprimirReporte = () => {
  const ventana = window.open('', '_blank', 'width=900,height=700')
  if (!ventana) { alert('Permite las ventanas emergentes para imprimir'); return }
  
  let filas = ''
  ventasHoy.value.forEach(v => {
    filas += `<tr>
      <td>${v.codigo || '-'}</td>
      <td>${v.cliente_nombre || '-'}</td>
      <td style="text-align:right;">BS ${formatearBS(v.monto_total_bs)}</td>
      <td style="text-align:right;">BS ${formatearBS(v.monto_entrada_bs)}</td>
      <td style="text-align:right; color:#f44336; font-weight:bold;">BS ${formatearBS((v.monto_total_bs || 0) - (v.monto_entrada_bs || 0))}</td>
      <td style="text-align:center;">${v.cuotas_aprobadas || 0}</td>
      <td style="text-align:right;">${formatearHora(v.creado_en)}</td>
    </tr>`
  })
  
  ventana.document.write(`
    <html>
      <head>
        <title>Reporte de Ventas - ${fechaHoy}</title>
        <style>
          body { font-family: Arial, sans-serif; margin: 20px; color: #333; }
          .header { text-align: center; margin-bottom: 20px; }
          .header h1 { margin: 0; font-size: 22px; }
          .header p { margin: 2px 0; font-size: 14px; color: #666; }
          .resumen { display: flex; justify-content: space-around; margin-bottom: 20px; flex-wrap: wrap; gap: 10px; }
          .resumen div { text-align: center; padding: 10px 20px; background: #f5f5f5; border-radius: 8px; }
          .resumen strong { font-size: 20px; }
          table { width: 100%; border-collapse: collapse; margin-top: 10px; }
          th { background: #1a237e; color: white; padding: 10px; font-size: 12px; text-transform: uppercase; }
          td { padding: 8px; border-bottom: 1px solid #eee; font-size: 13px; }
          tr:hover { background: #f9f9f9; }
          .footer { text-align: center; margin-top: 30px; font-size: 11px; color: #999; }
          @media print { body { margin: 0; } .no-print { display: none; } }
        </style>
      </head>
      <body>
        <div class="header">
          <h1>🏪 FinanCoop - Reporte de Ventas</h1>
          <p>${fechaHoy} | Tienda: ${tiendaNombre.value || 'Todas'}</p>
          <p>Generado: ${new Date().toLocaleString('es-VE')}</p>
        </div>
        <div class="resumen">
          <div><div style="color:#4caf50;">Total Ventas</div><strong>${ventasHoy.value.length}</strong></div>
          <div><div style="color:#4facfe;">Total Financiado</div><strong>BS ${formatearBS(totalHoy.value)}</strong></div>
          <div><div style="color:#ffd54f;">Entradas Cobradas</div><strong>BS ${formatearBS(totalEntrada.value)}</strong></div>
          <div><div style="color:#f44336;">Pendiente</div><strong>BS ${formatearBS(totalPendiente.value)}</strong></div>
        </div>
        <table>
          <thead><tr><th>Código</th><th>Cliente</th><th>Monto</th><th>Entrada</th><th>Pendiente</th><th>Cuotas</th><th>Hora</th></tr></thead>
          <tbody>${filas}</tbody>
        </table>
        <div class="footer"><p>FinanCoop © ${new Date().getFullYear()} - Sistema de Financiamiento</p></div>
        <div class="no-print" style="text-align:center; margin-top:20px;">
          <button onclick="window.print()" style="padding:10px 30px; font-size:16px; background:#4facfe; color:white; border:none; border-radius:25px; cursor:pointer;">🖨️ Imprimir Reporte</button>
        </div>
      </body>
    </html>
  `)
  ventana.document.close()
}

onMounted(() => { cargarVentas(); cargarUsuario() })
</script>

<style scoped>
.background-gradient { position: fixed; top: 0; left: 0; right: 0; bottom: 0; background: radial-gradient(ellipse at 20% 50%, rgba(79,172,254,0.12), transparent 70%), radial-gradient(ellipse at 80% 50%, rgba(99,102,241,0.08), transparent 70%), #0a0e1a; z-index: 0; }
.header-premium { position: relative; z-index: 1; padding: 16px 24px; background: rgba(255,255,255,0.05); backdrop-filter: blur(20px); border-radius: 20px; border: 1px solid rgba(255,255,255,0.06); }
.icon-wrapper { width: 48px; height: 48px; background: linear-gradient(135deg, #4facfe, #6366f1); border-radius: 14px; display: flex; align-items: center; justify-content: center; }
.pulse-animation { animation: pulse 2s infinite; }
@keyframes pulse { 0%, 100% { transform: scale(1); } 50% { transform: scale(1.05); } }
.step-chip { background: rgba(255,255,255,0.08) !important; padding: 8px 16px !important; border-radius: 50px !important; }
.glass-effect { background: rgba(255,255,255,0.05) !important; backdrop-filter: blur(16px) !important; border: 1px solid rgba(255,255,255,0.08) !important; border-radius: 12px !important; }
.glass-card { background: rgba(255,255,255,0.03) !important; backdrop-filter: blur(24px) !important; border: 1px solid rgba(255,255,255,0.06) !important; border-radius: 24px !important; }
.kpi-card { transition: transform 0.3s ease; }
.kpi-card:hover { transform: translateY(-4px); }
.kpi-icon-wrapper { width: 56px; height: 56px; border-radius: 50%; display: flex; align-items: center; justify-content: center; margin: 0 auto; }
.kpi-number { font-size: 1.8rem; font-weight: 800; }
.kpi-label { font-size: 0.7rem; color: rgba(255,255,255,0.4); text-transform: uppercase; letter-spacing: 0.5px; margin-top: 2px; }
.text-success { color: #4caf50 !important; }
.text-primary { color: #4facfe !important; }
.text-warning { color: #ffd54f !important; }
.text-error { color: #f44336 !important; }
.table-wrapper { overflow-x: auto; }
.premium-table { background: transparent !important; }
.premium-table :deep(th) { color: rgba(255,255,255,0.7) !important; font-weight: 700 !important; font-size: 0.75rem !important; text-transform: uppercase; padding: 12px 8px !important; border-bottom: 1px solid rgba(255,255,255,0.06) !important; }
.premium-table :deep(td) { color: rgba(255,255,255,0.9) !important; padding: 10px 8px !important; border-bottom: 1px solid rgba(255,255,255,0.03) !important; }
.premium-table :deep(tr:hover) { background: rgba(255,255,255,0.02) !important; }
.empty-state { padding: 40px; text-align: center; border: 1px dashed rgba(255,255,255,0.08); }
.fade-in { animation: fadeIn 0.4s ease; }
@keyframes fadeIn { from { opacity: 0; transform: translateY(10px); } to { opacity: 1; transform: translateY(0); } }
@media (max-width: 600px) { .header-premium { flex-direction: column; gap: 12px; align-items: stretch !important; } .kpi-number { font-size: 1.3rem; } }
</style>