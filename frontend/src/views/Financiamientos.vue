<template>
  <v-container fluid class="pa-0">
    <div class="background-gradient"></div>
    
    <v-row class="ma-0">
      <v-col cols="12" class="pa-4">
        <!-- HEADER PREMIUM -->
        <div class="header-premium d-flex align-center justify-space-between flex-wrap">
          <div class="d-flex align-center">
            <div class="icon-wrapper pulse-animation">
              <v-icon size="32" color="white">mdi-file-document-multiple</v-icon>
            </div>
            <div class="ml-3">
              <h1 class="text-h4 font-weight-bold text-white">Financiamientos</h1>
              <p class="text-subtitle-2 text-white" style="opacity: 0.7;">Panel de control y morosidad</p>
            </div>
          </div>
          <v-chip class="step-chip" color="transparent" size="large">
            <span class="text-white font-weight-bold">{{ stats.total }} Créditos</span>
          </v-chip>
        </div>

        <!-- KPIs PREMIUM -->
        <v-row class="mt-4">
          <v-col cols="12" sm="6" md="3">
            <v-card class="kpi-card glass-card rounded-xl" elevation="0">
              <v-card-text class="pa-4 text-center">
                <div class="kpi-icon-wrapper mb-2" style="background: rgba(79,172,254,0.15);">
                  <v-icon size="28" color="#4facfe">mdi-file-document</v-icon>
                </div>
                <div class="kpi-number text-primary">{{ stats.total }}</div>
                <div class="kpi-label">Total Financiamientos</div>
              </v-card-text>
            </v-card>
          </v-col>
          <v-col cols="12" sm="6" md="3">
            <v-card class="kpi-card glass-card rounded-xl" elevation="0">
              <v-card-text class="pa-4 text-center">
                <div class="kpi-icon-wrapper mb-2" style="background: rgba(76,175,80,0.15);">
                  <v-icon size="28" color="#4caf50">mdi-cash-check</v-icon>
                </div>
                <div class="kpi-number text-success">BS {{ formatearBS(stats.total_entrada) }}</div>
                <div class="kpi-label">Entrada Cobrada</div>
              </v-card-text>
            </v-card>
          </v-col>
          <v-col cols="12" sm="6" md="3">
            <v-card class="kpi-card glass-card rounded-xl" elevation="0">
              <v-card-text class="pa-4 text-center">
                <div class="kpi-icon-wrapper mb-2" style="background: rgba(255,213,79,0.15);">
                  <v-icon size="28" color="#ffd54f">mdi-cash-multiple</v-icon>
                </div>
                <div class="kpi-number text-warning">BS {{ formatearBS(stats.total_financiado) }}</div>
                <div class="kpi-label">Financiado</div>
              </v-card-text>
            </v-card>
          </v-col>
          <v-col cols="12" sm="6" md="3">
            <v-card class="kpi-card glass-card rounded-xl" elevation="0">
              <v-card-text class="pa-4 text-center">
                <div class="kpi-icon-wrapper mb-2" style="background: rgba(244,67,54,0.15);">
                  <v-icon size="28" color="#f44336">mdi-alert-circle</v-icon>
                </div>
                <div class="kpi-number text-error">BS {{ formatearBS(stats.total_pendiente) }}</div>
                <div class="kpi-label">Pendiente por Cobrar</div>
              </v-card-text>
            </v-card>
          </v-col>
        </v-row>

        <!-- GRÁFICA Y MOROSIDAD -->
        <v-row class="mt-4">
          <v-col cols="12" md="7">
            <v-card class="glass-card rounded-xl" elevation="0">
              <v-card-title class="text-h6 font-weight-bold text-white pa-4">
                <v-icon color="#4facfe" class="mr-2">mdi-chart-pie</v-icon>
                Distribución de Montos
              </v-card-title>
              <v-card-text class="pa-4 pt-0">
                <canvas ref="chartRef" style="max-height: 280px;"></canvas>
              </v-card-text>
            </v-card>
          </v-col>
          <v-col cols="12" md="5">
            <v-card class="glass-card rounded-xl" elevation="0">
              <v-card-title class="text-h6 font-weight-bold text-white pa-4">
                <v-icon color="#ffd54f" class="mr-2">mdi-alert-circle</v-icon>
                Niveles de Morosidad
              </v-card-title>
              <v-card-text class="pa-4 pt-0">
                <div v-for="nivel in nivelesMorosidad" :key="nivel.nombre" class="morosidad-item glass-effect mb-2 rounded-lg">
                  <div class="d-flex align-center pa-3">
                    <v-icon :color="nivel.color" size="28" class="mr-3">{{ nivel.icono }}</v-icon>
                    <div class="flex-grow-1">
                      <div class="d-flex align-center">
                        <strong class="text-white">{{ nivel.nombre }}</strong>
                        <v-chip :color="nivel.color" size="x-small" class="ml-2" variant="tonal">{{ nivel.cantidad }}</v-chip>
                      </div>
                      <div class="text-caption" style="color: rgba(255,255,255,0.3);">{{ nivel.descripcion }}</div>
                    </div>
                    <div class="text-right">
                      <div class="text-white font-weight-bold">BS {{ formatearBS(nivel.monto) }}</div>
                      <div class="text-caption" style="color: rgba(255,255,255,0.3);">{{ nivel.porcentaje }}%</div>
                    </div>
                  </div>
                </div>
                <div v-if="nivelesMorosidad.length === 0" class="empty-state glass-effect rounded-xl mt-2">
                  <v-icon size="32" color="rgba(255,255,255,0.1)">mdi-check-circle</v-icon>
                  <div class="text-caption" style="color: rgba(255,255,255,0.3);">Sin datos de morosidad</div>
                </div>
              </v-card-text>
            </v-card>
          </v-col>
        </v-row>

        <!-- FILTROS PREMIUM -->
        <v-row class="mt-4">
          <v-col cols="12">
            <v-card class="glass-card rounded-xl" elevation="0">
              <v-card-text class="pa-4">
                <v-row>
                  <v-col cols="12" md="3">
                    <v-text-field v-model="filtros.busqueda" label="Buscar (cédula, nombre, código)" prepend-inner-icon="mdi-magnify" @input="aplicarFiltros" variant="outlined" density="comfortable" dark class="custom-input" placeholder="Escribe para buscar..." />
                  </v-col>
                  <v-col cols="6" md="2">
                    <v-select v-model="filtros.estado" :items="['todos', 'activo', 'completado', 'mora']" label="Estado" @update:modelValue="aplicarFiltros" variant="outlined" density="comfortable" dark class="custom-input" />
                  </v-col>
                  <v-col cols="6" md="2">
                    <v-select v-model="filtros.nivel" :items="['todos', 'nuevo', 'bronce', 'plata', 'oro', 'platino']" label="Nivel Cliente" @update:modelValue="aplicarFiltros" variant="outlined" density="comfortable" dark class="custom-input" />
                  </v-col>
                  <v-col cols="6" md="2">
                    <v-select v-model="filtros.morosidad" :items="['todos', 'al_dia', 'leve', 'moderada', 'grave', 'critica']" label="Morosidad" @update:modelValue="aplicarFiltros" variant="outlined" density="comfortable" dark class="custom-input" />
                  </v-col>
                  <v-col cols="6" md="3">
                    <v-btn color="#4caf50" @click="exportarExcel" block rounded="pill" elevation="0" class="btn-export">
                      <v-icon start>mdi-file-excel</v-icon>Exportar Excel
                    </v-btn>
                  </v-col>
                </v-row>
              </v-card-text>
            </v-card>
          </v-col>
        </v-row>

        <!-- TABLA PREMIUM -->
        <v-row class="mt-4">
          <v-col cols="12">
            <v-card class="glass-card rounded-xl" elevation="0">
              <v-card-title class="text-h6 font-weight-bold text-white pa-4">
                <v-icon color="#4facfe" class="mr-2">mdi-format-list-bulleted</v-icon>
                Listado de Financiamientos
                <v-spacer></v-spacer>
                <v-chip color="#4facfe" variant="tonal" size="small">{{ financiamientosFiltrados.length }} registros</v-chip>
              </v-card-title>
              <v-card-text class="pa-4 pt-0">
                <div class="table-wrapper">
                  <v-data-table :items="financiamientosFiltrados" :headers="headers" :items-per-page="50" class="premium-table">
                    <template v-slot:item.cliente="{ item }">
                      <div class="d-flex align-center">
                        <v-avatar size="32" color="rgba(79,172,254,0.2)" class="mr-2">
                          <span class="text-caption" style="color: #4facfe;">{{ item.cliente_nombre?.charAt(0) }}</span>
                        </v-avatar>
                        <div>
                          <div class="text-white font-weight-bold">{{ item.cliente_nombre }}</div>
                          <div class="text-caption" style="color: rgba(255,255,255,0.3);">{{ item.cliente_cedula }}</div>
                        </div>
                      </div>
                    </template>
                    <template v-slot:item.montos="{ item }">
                      <div class="text-right">
                        <div class="text-white font-weight-bold">BS {{ formatearBS(item.monto_total_bs) }}</div>
                        <div class="text-caption" style="color: rgba(255,255,255,0.3);">${{ formatearUSD(item.monto_total_usd) }}</div>
                      </div>
                    </template>
                    <template v-slot:item.entrada="{ item }">
                      <div class="text-right">
                        <div class="text-success font-weight-bold">BS {{ formatearBS(item.monto_entrada_bs) }}</div>
                        <v-chip size="x-small" color="success" variant="tonal">Pagada</v-chip>
                      </div>
                    </template>
                    <template v-slot:item.pendiente="{ item }">
                      <div class="text-right">
                        <div :class="item.saldo_pendiente_bs > 0 ? 'text-error' : 'text-success'" class="font-weight-bold">
                          BS {{ formatearBS(item.saldo_pendiente_bs) }}
                        </div>
                      </div>
                    </template>
                    <template v-slot:item.progreso="{ item }">
                      <v-progress-linear :model-value="item.porcentaje_pagado" :color="item.porcentaje_pagado >= 100 ? 'success' : '#4facfe'" height="16" rounded>
                        <template v-slot:default><span class="text-caption font-weight-bold">{{ item.porcentaje_pagado }}%</span></template>
                      </v-progress-linear>
                    </template>
                    <template v-slot:item.morosidad="{ item }">
                      <v-chip :color="item.morosidad.color" size="x-small" variant="flat">
                        <v-icon start size="14">{{ item.morosidad.icono }}</v-icon>{{ item.morosidad.nombre }}
                      </v-chip>
                    </template>
                    <template v-slot:item.estado="{ item }">
                      <v-chip :color="colorEstado(item.estado)" size="x-small" variant="tonal">{{ item.estado }}</v-chip>
                    </template>
                    <template v-slot:item.acciones="{ item }">
                      <div class="d-flex gap-1">
                        <v-btn size="x-small" color="#4facfe" variant="tonal" :to="`/cuotas/${item.id}`" rounded="pill">
                          <v-icon start size="16">mdi-eye</v-icon>Cuotas
                        </v-btn>
                        <v-btn v-if="item.estado === 'activo'" size="x-small" color="#4caf50" variant="tonal" @click="abrirPagoEfectivo(item)" rounded="pill">
                          <v-icon start size="16">mdi-cash</v-icon>Pagar
                        </v-btn>
                        <v-btn v-if="esAdminCentral" size="x-small" color="error" variant="tonal" @click="confirmarEliminar(item)" rounded="pill">
                          <v-icon start size="16">mdi-delete</v-icon>
                        </v-btn>
                      </div>
                    </template>
                  </v-data-table>
                </div>
              </v-card-text>
            </v-card>
          </v-col>
        </v-row>
      </v-col>
    </v-row>

    <!-- DIALOG PAGO EFECTIVO -->
    <v-dialog v-model="dialogPago" max-width="400">
      <v-card class="glass-card">
        <v-card-title class="text-white pa-4" style="background: linear-gradient(135deg, #4caf50, #2e7d32);">
          <v-icon start>mdi-cash</v-icon>Pago en Efectivo
        </v-card-title>
        <v-card-text class="pa-4">
          <p class="text-white"><strong>Cliente:</strong> {{ financiamientoSeleccionado?.cliente_nombre }}</p>
          <p class="text-white"><strong>Código:</strong> {{ financiamientoSeleccionado?.codigo }}</p>
          <v-select v-model="cuotaSeleccionada" :items="cuotasPendientes" item-title="label" item-value="id" label="Seleccionar cuota" variant="outlined" dark class="custom-input mt-3" />
          <div v-if="cuotaSeleccionada" class="glass-effect pa-3 mt-3 rounded-lg text-center">
            <div class="text-h5 text-white font-weight-bold">BS {{ formatearBS(cuotaInfo?.monto_total_bs) }}</div>
            <div class="text-caption" style="color: rgba(255,255,255,0.3);">${{ formatearUSD(cuotaInfo?.monto_total_usd) }}</div>
          </div>
        </v-card-text>
        <v-card-actions class="pa-4">
          <v-btn @click="dialogPago = false" variant="text" color="grey">Cancelar</v-btn>
          <v-spacer></v-spacer>
          <v-btn color="#4caf50" rounded="pill" @click="confirmarPagoEfectivo" :disabled="!cuotaSeleccionada">Confirmar Pago</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>
  </v-container>
</template>

<script setup>
import { ref, computed, onMounted, nextTick } from 'vue'
import { api } from '@/config/api'
import Chart from 'chart.js/auto'

const financiamientos = ref([])
const financiamientosFiltrados = ref([])
const cuotasPendientes = ref([])
const cuotaSeleccionada = ref(null)
const cuotaInfo = ref(null)
const financiamientoSeleccionado = ref(null)
const dialogPago = ref(false)
const chartRef = ref(null)
let chartInstance = null

const filtros = ref({ busqueda: '', estado: 'todos', nivel: 'todos', morosidad: 'todos' })
const stats = ref({ total: 0, total_entrada: 0, total_financiado: 0, total_pendiente: 0 })

import { useAuthStore } from '@/stores/auth'
const auth = useAuthStore()
const esAdminCentral = computed(() => auth.esAdmin)

const headers = [
  { title: 'Código', key: 'codigo', width: '100px' },
  { title: 'Cliente', key: 'cliente', width: '200px' },
  { title: 'Fecha', key: 'fecha_primera_cuota', width: '120px' },
  { title: 'Montos', key: 'montos', align: 'end', width: '150px' },
  { title: 'Entrada', key: 'entrada', align: 'end', width: '120px' },
  { title: 'Pendiente', key: 'pendiente', align: 'end', width: '150px' },
  { title: 'Progreso', key: 'progreso', width: '150px' },
  { title: 'Morosidad', key: 'morosidad', width: '130px' },
  { title: 'Estado', key: 'estado', width: '100px' },
  { title: 'Acciones', key: 'acciones', width: '250px' }
]

const colorEstado = (estado) => ({ activo: 'primary', completado: 'success', cancelado: 'grey', mora: 'error' })[estado] || 'grey'
const formatearBS = (m) => m ? Number(m).toLocaleString('es-VE', { minimumFractionDigits: 2, maximumFractionDigits: 2 }) : '0,00'
const formatearUSD = (m) => m ? Number(m).toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 }) : '0.00'
const formatearFecha = (f) => f ? new Date(f).toLocaleDateString('es-VE', { day: '2-digit', month: '2-digit', year: 'numeric' }) : ''

const calcularMorosidad = (fin) => {
  if (fin.estado === 'completado') return { nombre: 'Al Día', color: 'success', icono: 'mdi-check-circle', descripcion: 'Completado' }
  const atrasadas = fin.cuotas?.filter(c => c.estado === 'pendiente' && new Date(c.fecha_vencimiento) < new Date()).length || 0
  if (atrasadas === 0) return { nombre: 'Al Día', color: 'success', icono: 'mdi-check-circle', descripcion: 'Sin atrasos' }
  if (atrasadas === 1) return { nombre: 'Leve', color: 'warning', icono: 'mdi-alert', descripcion: '1 cuota atrasada' }
  if (atrasadas === 2) return { nombre: 'Moderada', color: 'orange', icono: 'mdi-alert', descripcion: '2 cuotas atrasadas' }
  if (atrasadas <= 4) return { nombre: 'Grave', color: 'error', icono: 'mdi-alert-circle', descripcion: `${atrasadas} cuotas atrasadas` }
  return { nombre: 'Crítica', color: 'red-darken-4', icono: 'mdi-alert-octagon', descripcion: `${atrasadas} cuotas atrasadas` }
}

const cargarDatos = async () => {
  try {
    const response = await api.get('/financiamientos')
    const financiamientosData = response.financiamientos || response.data || response || []

    const datos = await Promise.all(financiamientosData.map(async (fin) => {
      const cuotasResponse = await api.get(`/financiamientos/${fin.id}/cuotas`)
      const cuotas = Array.isArray(cuotasResponse) ? cuotasResponse : cuotasResponse.data || []
      const pagadas = cuotas.filter(c => c.estado === 'pagada').length
      const pendientes = cuotas.filter(c => c.estado === 'pendiente')
      const atrasadas = cuotas.filter(c => c.estado === 'pendiente' && new Date(c.fecha_vencimiento) < new Date())
      const saldoPendienteBS = pendientes.reduce((s, c) => s + (c.monto_total_bs || 0), 0)
      const saldoPendienteUSD = pendientes.reduce((s, c) => s + (c.monto_total_usd || 0), 0)
      const porcentajePagado = fin.cuotas_solicitadas > 0 ? Math.round((pagadas / fin.cuotas_solicitadas) * 100) : 0
      return { 
        ...fin, 
        cliente_nombre: fin.cliente_nombre || 'Desconocido',
        cliente_cedula: fin.cliente_cedula || '', 
        cliente_nivel: fin.cliente_nivel || 'nuevo', 
        cuotas, 
        saldo_pendiente_bs: saldoPendienteBS, 
        saldo_pendiente_usd: saldoPendienteUSD, 
        porcentaje_pagado: porcentajePagado, 
        morosidad: calcularMorosidad({ ...fin, cuotas }), 
        cuotas_atrasadas: atrasadas.length, 
        fecha_primera_cuota: fin.fecha_primera_cuota 
      }
    }))
    
    financiamientos.value = datos; aplicarFiltros(); calcularStats(); calcularNivelesMorosidad()
    await nextTick(); crearGrafica()
  } catch (e) { console.error('Error cargando datos:', e) }
}

const aplicarFiltros = () => {
  let r = [...financiamientos.value]
  if (filtros.value.busqueda) { const q = filtros.value.busqueda.toLowerCase(); r = r.filter(f => f.codigo?.toLowerCase().includes(q) || f.cliente_nombre?.toLowerCase().includes(q) || f.cliente_cedula?.includes(q)) }
  if (filtros.value.estado !== 'todos') r = r.filter(f => f.estado === filtros.value.estado)
  if (filtros.value.nivel !== 'todos') r = r.filter(f => f.cliente_nivel === filtros.value.nivel)
  if (filtros.value.morosidad !== 'todos') r = r.filter(f => f.morosidad.nombre.toLowerCase().replace(' ', '_') === filtros.value.morosidad)
  financiamientosFiltrados.value = r
}

const calcularStats = () => {
  const activos = financiamientos.value.filter(f => f.estado === 'activo')
  stats.value = { total: financiamientos.value.length, total_entrada: financiamientos.value.reduce((s, f) => s + (f.monto_entrada_bs || 0), 0), total_financiado: activos.reduce((s, f) => s + (f.saldo_pendiente_bs || 0), 0), total_pendiente: activos.reduce((s, f) => s + (f.saldo_pendiente_bs || 0), 0) }
}

const nivelesMorosidad = ref([])
const calcularNivelesMorosidad = () => {
  const niveles = [
    { nombre: 'Al Día', color: 'success', icono: 'mdi-check-circle', descripcion: 'Sin atrasos' },
    { nombre: 'Leve', color: 'warning', icono: 'mdi-alert', descripcion: '1 cuota atrasada' },
    { nombre: 'Moderada', color: 'orange', icono: 'mdi-alert', descripcion: '2 cuotas atrasadas' },
    { nombre: 'Grave', color: 'error', icono: 'mdi-alert-circle', descripcion: '3-4 cuotas atrasadas' },
    { nombre: 'Crítica', color: 'red-darken-4', icono: 'mdi-alert-octagon', descripcion: '5+ cuotas atrasadas' }
  ]
  const activos = financiamientos.value.filter(f => f.estado === 'activo')
  const total = activos.reduce((s, f) => s + f.saldo_pendiente_bs, 0)
  nivelesMorosidad.value = niveles.map(n => {
    const filtrados = activos.filter(f => f.morosidad.nombre === n.nombre)
    const monto = filtrados.reduce((s, f) => s + f.saldo_pendiente_bs, 0)
    return { ...n, cantidad: filtrados.length, monto, porcentaje: total > 0 ? ((monto / total) * 100).toFixed(1) : 0 }
  })
}

const crearGrafica = () => {
  if (chartInstance) chartInstance.destroy()
  const ctx = chartRef.value?.getContext('2d')
  if (!ctx) return
  chartInstance = new Chart(ctx, { type: 'doughnut', data: { labels: ['Entrada Cobrada', 'Financiado Pendiente'], datasets: [{ data: [stats.value.total_entrada, stats.value.total_pendiente], backgroundColor: ['#4CAF50', '#FF9800'], borderWidth: 0 }] }, options: { responsive: true, maintainAspectRatio: false, plugins: { legend: { position: 'bottom', labels: { color: 'rgba(255,255,255,0.7)' } } } } })
}

const abrirPagoEfectivo = async (fin) => {
  financiamientoSeleccionado.value = fin; cuotaSeleccionada.value = null; cuotaInfo.value = null
  try {
    const cuotasResponse = await api.get(`/financiamientos/${fin.id}/cuotas`)
    const cuotas = Array.isArray(cuotasResponse) ? cuotasResponse : cuotasResponse.data || []
    cuotasPendientes.value = cuotas.filter(c => c.estado === 'pendiente').map(c => ({ id: c.id, label: `Cuota #${c.numero} - BS ${formatearBS(c.monto_total_bs)}`, monto_total_bs: c.monto_total_bs, monto_total_usd: c.monto_total_usd }))
    dialogPago.value = true
  } catch (e) {}
}

const confirmarPagoEfectivo = async () => {
  try { 
    await api.post(`/pagos/cuotas/${cuotaSeleccionada.value}/pagar-efectivo`)  // ✅ CORRECTO
    alert('✅ Pago registrado')
    dialogPago.value = false
    await cargarDatos() 
  } catch (e) { 
    alert('Error registrando pago: ' + (e.response?.data?.detail || e.message)) 
  }
}

const confirmarEliminar = (item) => {
  if (!confirm(`¿Eliminar el financiamiento ${item.codigo} de ${item.cliente_nombre}?`)) return
  eliminarFinanciamiento(item.id)
}

const eliminarFinanciamiento = async (id) => {
  try {
    await api.delete(`/financiamientos/${id}`)
    alert('✅ Financiamiento eliminado')
    await cargarDatos()
  } catch (e) {
    alert('❌ Error: ' + (e.response?.data?.detail || e.message))
  }
}

const exportarExcel = () => {
  const datos = financiamientosFiltrados.value.map(f => ({ Codigo: f.codigo, Cliente: f.cliente_nombre, Cedula: f.cliente_cedula, Fecha: formatearFecha(f.fecha_primera_cuota), Total_BS: f.monto_total_bs, Entrada_BS: f.monto_entrada_bs, Pendiente_BS: f.saldo_pendiente_bs, Estado: f.estado, Morosidad: f.morosidad.nombre, Progreso: f.porcentaje_pagado + '%' }))
  const h = Object.keys(datos[0] || {})
  const csv = [h.join(','), ...datos.map(r => h.map(k => `"${r[k]}"`).join(','))].join('\n')
  const blob = new Blob([csv], { type: 'text/csv' }); const a = document.createElement('a'); a.href = URL.createObjectURL(blob); a.download = `financiamientos_${new Date().toISOString().split('T')[0]}.csv`; a.click()
}

onMounted(() => { cargarDatos() })
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
.kpi-number { font-size: 2rem; font-weight: 800; }
.kpi-label { font-size: 0.75rem; color: rgba(255,255,255,0.4); text-transform: uppercase; letter-spacing: 0.5px; margin-top: 2px; }
.text-success { color: #4caf50 !important; }
.text-primary { color: #4facfe !important; }
.text-warning { color: #ffd54f !important; }
.text-error { color: #f44336 !important; }
.morosidad-item { transition: transform 0.2s ease; }
.morosidad-item:hover { transform: translateX(4px); }
.table-wrapper { overflow-x: auto; }
.premium-table { background: transparent !important; }
.premium-table :deep(th) { color: rgba(255,255,255,0.7) !important; font-weight: 700 !important; font-size: 0.75rem !important; text-transform: uppercase; padding: 12px 8px !important; border-bottom: 1px solid rgba(255,255,255,0.06) !important; }
.premium-table :deep(td) { color: rgba(255,255,255,0.9) !important; padding: 10px 8px !important; border-bottom: 1px solid rgba(255,255,255,0.03) !important; }
.premium-table :deep(tr:hover) { background: rgba(255,255,255,0.02) !important; }
.custom-input :deep(.v-field) { background: rgba(255,255,255,0.05) !important; border-radius: 12px !important; border: 1px solid rgba(255,255,255,0.08) !important; }
.custom-input :deep(.v-field--focused) { border-color: #4facfe !important; }
.custom-input :deep(.v-label) { color: rgba(255,255,255,0.5) !important; }
.custom-input :deep(.v-field__input) { color: white !important; }
.custom-input :deep(.v-field__input::placeholder) { color: rgba(255,255,255,0.5) !important; font-weight: 500 !important; }
.btn-export { background: linear-gradient(135deg, #4caf50, #2e7d32) !important; color: white !important; font-weight: 700 !important; transition: all 0.3s ease !important; }
.btn-export:hover { transform: translateY(-2px); box-shadow: 0 8px 32px rgba(76,175,80,0.3) !important; }
.empty-state { padding: 24px; text-align: center; border: 1px dashed rgba(255,255,255,0.08); }
.gap-1 { gap: 4px; }
@media (max-width: 600px) { .header-premium { flex-direction: column; gap: 12px; align-items: stretch !important; } .kpi-number { font-size: 1.5rem; } }
</style>