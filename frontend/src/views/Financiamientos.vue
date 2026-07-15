<template>
  <v-row>
    <v-col cols="12">
      <h1 class="text-h4 mb-2">📋 Financiamientos</h1>
      <p class="text-body-2 text-grey mb-4">Panel de control y morosidad</p>
    </v-col>
    
    <!-- RESUMEN GENERAL -->
    <v-col cols="12" md="3">
      <v-card color="primary" dark>
        <v-card-text class="text-center">
          <div class="text-h3">{{ stats.total }}</div>
          <div class="text-subtitle-1">Total Financiamientos</div>
        </v-card-text>
      </v-card>
    </v-col>
    
    <v-col cols="12" md="3">
      <v-card color="success" dark>
        <v-card-text class="text-center">
          <div class="text-h3">BS {{ formatearBS(stats.total_entrada) }}</div>
          <div class="text-subtitle-1">Entrada Cobrada</div>
        </v-card-text>
      </v-card>
    </v-col>
    
    <v-col cols="12" md="3">
      <v-card color="warning" dark>
        <v-card-text class="text-center">
          <div class="text-h3">BS {{ formatearBS(stats.total_financiado) }}</div>
          <div class="text-subtitle-1">Financiado</div>
        </v-card-text>
      </v-card>
    </v-col>
    
    <v-col cols="12" md="3">
      <v-card color="error" dark>
        <v-card-text class="text-center">
          <div class="text-h3">BS {{ formatearBS(stats.total_pendiente) }}</div>
          <div class="text-subtitle-1">Pendiente por Cobrar</div>
        </v-card-text>
      </v-card>
    </v-col>
    
    <!-- GRÁFICA -->
    <v-col cols="12" md="6">
      <v-card>
        <v-card-title>📊 Distribución de Montos</v-card-title>
        <v-card-text>
          <canvas ref="chartRef" style="max-height: 300px;"></canvas>
        </v-card-text>
      </v-card>
    </v-col>
    
    <!-- NIVELES DE MOROSIDAD -->
    <v-col cols="12" md="6">
      <v-card>
        <v-card-title>⚠️ Niveles de Morosidad</v-card-title>
        <v-card-text>
          <v-list>
            <v-list-item v-for="nivel in nivelesMorosidad" :key="nivel.nombre">
              <template v-slot:prepend>
                <v-icon :color="nivel.color" size="32">{{ nivel.icono }}</v-icon>
              </template>
              <v-list-item-title>
                <strong>{{ nivel.nombre }}</strong>
                <v-chip :color="nivel.color" size="small" class="ml-2">{{ nivel.cantidad }}</v-chip>
              </v-list-item-title>
              <v-list-item-subtitle>
                {{ nivel.descripcion }}
              </v-list-item-subtitle>
              <template v-slot:append>
                <div class="text-right">
                  <div class="text-h6">BS {{ formatearBS(nivel.monto) }}</div>
                  <div class="text-caption">{{ nivel.porcentaje }}% del total</div>
                </div>
              </template>
            </v-list-item>
          </v-list>
        </v-card-text>
      </v-card>
    </v-col>
    
    <!-- FILTROS -->
    <v-col cols="12">
      <v-card class="mb-4">
        <v-card-text>
          <v-row>
            <v-col cols="12" md="3">
              <v-text-field
                v-model="filtros.busqueda"
                label="Buscar (cédula, nombre, código)"
                prepend-inner-icon="mdi-magnify"
                @input="aplicarFiltros"
              ></v-text-field>
            </v-col>
            <v-col cols="12" md="2">
              <v-select
                v-model="filtros.estado"
                :items="['todos', 'activo', 'completado', 'mora']"
                label="Estado"
                @update:modelValue="aplicarFiltros"
              ></v-select>
            </v-col>
            <v-col cols="12" md="2">
              <v-select
                v-model="filtros.nivel"
                :items="['todos', 'nuevo', 'bronce', 'plata', 'oro', 'platino']"
                label="Nivel Cliente"
                @update:modelValue="aplicarFiltros"
              ></v-select>
            </v-col>
            <v-col cols="12" md="2">
              <v-select
                v-model="filtros.morosidad"
                :items="['todos', 'al_dia', 'leve', 'moderada', 'grave', 'critica']"
                label="Morosidad"
                @update:modelValue="aplicarFiltros"
              ></v-select>
            </v-col>
            <v-col cols="12" md="3">
              <v-btn color="primary" @click="exportarExcel" block>
                📥 Exportar Excel
              </v-btn>
            </v-col>
          </v-row>
        </v-card-text>
      </v-card>
    </v-col>
    
    <!-- TABLA DE FINANCIAMIENTOS -->
    <v-col cols="12">
      <v-card>
        <v-card-title>
          Listado de Financiamientos
          <v-spacer></v-spacer>
          <v-chip color="primary">{{ financiamientosFiltrados.length }} registros</v-chip>
        </v-card-title>
        
        <v-data-table
          :items="financiamientosFiltrados"
          :headers="headers"
          :items-per-page="50"
          class="elevation-1"
        >
          <!-- Cliente -->
          <template v-slot:item.cliente="{ item }">
            <div class="d-flex align-center">
              <v-avatar color="primary" size="32" class="mr-2">
                <span class="text-white">{{ item.cliente_nombre?.charAt(0) }}</span>
              </v-avatar>
              <div>
                <div class="font-weight-bold">{{ item.cliente_nombre }}</div>
                <div class="text-caption">{{ item.cliente_cedula }}</div>
              </div>
            </div>
          </template>
          
          <!-- Montos -->
          <template v-slot:item.montos="{ item }">
            <div class="text-right">
              <div>BS {{ formatearBS(item.monto_total_bs) }}</div>
              <div class="text-caption text-grey">Ref: ${{ formatearUSD(item.monto_total_usd) }}</div>
            </div>
          </template>
          
          <!-- Entrada -->
          <template v-slot:item.entrada="{ item }">
            <div class="text-right">
              <div>BS {{ formatearBS(item.monto_entrada_bs) }}</div>
              <v-chip size="x-small" color="success">Pagada</v-chip>
            </div>
          </template>
          
          <!-- Pendiente -->
          <template v-slot:item.pendiente="{ item }">
            <div class="text-right">
              <div class="font-weight-bold" :class="item.saldo_pendiente_bs > 0 ? 'text-error' : 'text-success'">
                BS {{ formatearBS(item.saldo_pendiente_bs) }}
              </div>
              <div class="text-caption text-grey">Ref: ${{ formatearUSD(item.saldo_pendiente_usd) }}</div>
            </div>
          </template>
          
          <!-- Progreso -->
          <template v-slot:item.progreso="{ item }">
            <div class="d-flex align-center">
              <v-progress-linear
                :model-value="item.porcentaje_pagado"
                :color="item.porcentaje_pagado >= 100 ? 'success' : 'primary'"
                height="20"
                rounded
              >
                <template v-slot:default>
                  <span class="text-white text-caption">{{ item.porcentaje_pagado }}%</span>
                </template>
              </v-progress-linear>
            </div>
          </template>
          
          <!-- Morosidad -->
          <template v-slot:item.morosidad="{ item }">
            <v-chip
              :color="item.morosidad.color"
              :text-color="item.morosidad.textColor"
              size="small"
            >
              <v-icon start size="14">{{ item.morosidad.icono }}</v-icon>
              {{ item.morosidad.nombre }}
            </v-chip>
          </template>
          
          <!-- Estado -->
          <template v-slot:item.estado="{ item }">
            <v-chip :color="colorEstado(item.estado)" size="small">
              {{ item.estado }}
            </v-chip>
          </template>
          
          <!-- Acciones -->
          <template v-slot:item.acciones="{ item }">
            <div class="d-flex gap-2">
              <v-btn
                size="small"
                color="info"
                :to="`/cuotas/${item.id}`"
              >
                Ver Cuotas
              </v-btn>
              <v-btn
                v-if="item.estado === 'activo'"
                size="small"
                color="success"
                @click="abrirPagoEfectivo(item)"
              >
                Pagar Efectivo
              </v-btn>
            </div>
          </template>
        </v-data-table>
      </v-card>
    </v-col>
  </v-row>
  
  <!-- DIALOG: Pago en Efectivo -->
  <v-dialog v-model="dialogPago" max-width="400">
    <v-card>
      <v-card-title>💵 Pago en Efectivo</v-card-title>
      <v-card-text>
        <p><strong>Cliente:</strong> {{ financiamientoSeleccionado?.cliente_nombre }}</p>
        <p><strong>Código:</strong> {{ financiamientoSeleccionado?.codigo }}</p>
        
        <v-select
          v-model="cuotaSeleccionada"
          :items="cuotasPendientes"
          item-title="label"
          item-value="id"
          label="Seleccionar cuota"
          class="mt-3"
        ></v-select>
        
        <div v-if="cuotaSeleccionada" class="text-center pa-3 bg-grey-lighten-4 rounded">
          <div class="text-h5">BS {{ formatearBS(cuotaInfo?.monto_total_bs) }}</div>
          <div class="text-caption">Ref: ${{ formatearUSD(cuotaInfo?.monto_total_usd) }}</div>
        </div>
      </v-card-text>
      <v-card-actions>
        <v-btn @click="dialogPago = false">Cancelar</v-btn>
        <v-btn color="success" @click="confirmarPagoEfectivo" :disabled="!cuotaSeleccionada">
          Confirmar Pago
        </v-btn>
      </v-card-actions>
    </v-card>
  </v-dialog>
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

const filtros = ref({
  busqueda: '',
  estado: 'todos',
  nivel: 'todos',
  morosidad: 'todos'
})

const stats = ref({
  total: 0,
  total_entrada: 0,
  total_financiado: 0,
  total_pendiente: 0
})

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
  { title: 'Acciones', key: 'acciones', width: '200px' }
]

const colorEstado = (estado) => {
  const colores = { activo: 'primary', completado: 'success', cancelado: 'grey', mora: 'error' }
  return colores[estado] || 'grey'
}

const formatearBS = (monto) => {
  if (!monto) return '0,00'
  return monto.toLocaleString('es-VE', { minimumFractionDigits: 2, maximumFractionDigits: 2 })
}

const formatearUSD = (monto) => {
  if (!monto) return '0.00'
  return monto.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })
}

const formatearFecha = (fechaStr) => {
  if (!fechaStr) return ''
  const fecha = new Date(fechaStr)
  return fecha.toLocaleDateString('es-VE', { day: '2-digit', month: '2-digit', year: 'numeric' })
}

const calcularMorosidad = (fin) => {
  if (fin.estado === 'completado') {
    return { nombre: 'Al Día', color: 'success', textColor: 'white', icono: 'mdi-check-circle', descripcion: 'Financiamiento completado' }
  }
  
  const cuotasAtrasadas = fin.cuotas?.filter(c => c.estado === 'pendiente' && new Date(c.fecha_vencimiento) < new Date()).length || 0
  
  if (cuotasAtrasadas === 0) {
    return { nombre: 'Al Día', color: 'success', textColor: 'white', icono: 'mdi-check-circle', descripcion: 'Sin atrasos' }
  } else if (cuotasAtrasadas === 1) {
    return { nombre: 'Leve', color: 'warning', textColor: 'black', icono: 'mdi-alert', descripcion: '1 cuota atrasada' }
  } else if (cuotasAtrasadas === 2) {
    return { nombre: 'Moderada', color: 'orange', textColor: 'white', icono: 'mdi-alert', descripcion: '2 cuotas atrasadas' }
  } else if (cuotasAtrasadas <= 4) {
    return { nombre: 'Grave', color: 'error', textColor: 'white', icono: 'mdi-alert-circle', descripcion: `${cuotasAtrasadas} cuotas atrasadas` }
  } else {
    return { nombre: 'Crítica', color: 'red-darken-4', textColor: 'white', icono: 'mdi-alert-octagon', descripcion: `${cuotasAtrasadas} cuotas atrasadas` }
  }
}

const cargarDatos = async () => {
  try {
    const response = await api.get('/financiamientos')
    const financiamientosData = Array.isArray(response) ? response : response.data || []
    
    const clientesResponse = await api.get('/clientes')
    const clientesData = Array.isArray(clientesResponse) ? clientesResponse : clientesResponse.data || []
    
    const datos = await Promise.all(financiamientosData.map(async (fin) => {
      const cliente = clientesData.find(c => c.id === fin.cliente_id)
      const cuotasResponse = await api.get(`/financiamientos/${fin.id}/cuotas`)
      const cuotas = Array.isArray(cuotasResponse) ? cuotasResponse : cuotasResponse.data || []
      
      const pagadas = cuotas.filter(c => c.estado === 'pagada').length
      const pendientes = cuotas.filter(c => c.estado === 'pendiente')
      const atrasadas = cuotas.filter(c => c.estado === 'pendiente' && new Date(c.fecha_vencimiento) < new Date())
      
      const saldoPendienteBS = pendientes.reduce((sum, c) => sum + (c.monto_total_bs || 0), 0)
      const saldoPendienteUSD = pendientes.reduce((sum, c) => sum + (c.monto_total_usd || 0), 0)
      
      const porcentajePagado = fin.cuotas_solicitadas > 0 ? Math.round((pagadas / fin.cuotas_solicitadas) * 100) : 0
      
      const morosidad = calcularMorosidad({ ...fin, cuotas })
      
      return {
        ...fin,
        cliente_nombre: cliente?.nombre || 'Desconocido',
        cliente_cedula: cliente?.cedula || '',
        cliente_nivel: cliente?.nivel || 'nuevo',
        cuotas: cuotas,
        saldo_pendiente_bs: saldoPendienteBS,
        saldo_pendiente_usd: saldoPendienteUSD,
        porcentaje_pagado: porcentajePagado,
        morosidad: morosidad,
        cuotas_atrasadas: atrasadas.length,
        fecha_primera_cuota: fin.fecha_primera_cuota
      }
    }))
    
    financiamientos.value = datos
    aplicarFiltros()
    calcularStats()
    calcularNivelesMorosidad()
    
    await nextTick()
    crearGrafica()
    
  } catch (e) {
    console.error('Error cargando datos:', e)
    alert('Error al cargar los datos')
  }
}

const aplicarFiltros = () => {
  let resultado = [...financiamientos.value]
  
  if (filtros.value.busqueda) {
    const busqueda = filtros.value.busqueda.toLowerCase()
    resultado = resultado.filter(f => 
      f.codigo?.toLowerCase().includes(busqueda) ||
      f.cliente_nombre?.toLowerCase().includes(busqueda) ||
      f.cliente_cedula?.includes(busqueda)
    )
  }
  
  if (filtros.value.estado !== 'todos') {
    resultado = resultado.filter(f => f.estado === filtros.value.estado)
  }
  
  if (filtros.value.nivel !== 'todos') {
    resultado = resultado.filter(f => f.cliente_nivel === filtros.value.nivel)
  }
  
  if (filtros.value.morosidad !== 'todos') {
    resultado = resultado.filter(f => f.morosidad.nombre.toLowerCase().replace(' ', '_') === filtros.value.morosidad)
  }
  
  financiamientosFiltrados.value = resultado
}

const calcularStats = () => {
  const activos = financiamientos.value.filter(f => f.estado === 'activo')
  
  stats.value = {
    total: financiamientos.value.length,
    total_entrada: financiamientos.value.reduce((sum, f) => sum + (f.monto_entrada_bs || 0), 0),
    total_financiado: activos.reduce((sum, f) => sum + (f.saldo_pendiente_bs || 0), 0),
    total_pendiente: activos.reduce((sum, f) => sum + (f.saldo_pendiente_bs || 0), 0)
  }
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
  const totalPendiente = activos.reduce((sum, f) => sum + f.saldo_pendiente_bs, 0)
  
  nivelesMorosidad.value = niveles.map(n => {
    const filtrados = activos.filter(f => f.morosidad.nombre === n.nombre)
    const monto = filtrados.reduce((sum, f) => sum + f.saldo_pendiente_bs, 0)
    return {
      ...n,
      cantidad: filtrados.length,
      monto: monto,
      porcentaje: totalPendiente > 0 ? ((monto / totalPendiente) * 100).toFixed(1) : 0
    }
  })
}

const crearGrafica = () => {
  if (chartInstance) {
    chartInstance.destroy()
  }
  
  const ctx = chartRef.value?.getContext('2d')
  if (!ctx) return
  
  chartInstance = new Chart(ctx, {
    type: 'doughnut',
    data: {
      labels: ['Entrada Cobrada', 'Financiado Pendiente'],
      datasets: [{
        data: [stats.value.total_entrada, stats.value.total_pendiente],
        backgroundColor: ['#4CAF50', '#FF9800'],
        borderWidth: 0
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: {
          position: 'bottom'
        },
        tooltip: {
          callbacks: {
            label: function(context) {
              return 'BS ' + formatearBS(context.raw)
            }
          }
        }
      }
    }
  })
}

const abrirPagoEfectivo = async (fin) => {
  financiamientoSeleccionado.value = fin
  cuotaSeleccionada.value = null
  cuotaInfo.value = null
  
  try {
    const cuotasResponse = await api.get(`/financiamientos/${fin.id}/cuotas`)
    const cuotas = Array.isArray(cuotasResponse) ? cuotasResponse : cuotasResponse.data || []
    const pendientes = cuotas.filter(c => c.estado === 'pendiente')
    
    cuotasPendientes.value = pendientes.map(c => ({
      id: c.id,
      label: `Cuota #${c.numero} - BS ${formatearBS(c.monto_total_bs)} (vence ${formatearFecha(c.fecha_vencimiento)})`,
      monto_total_bs: c.monto_total_bs,
      monto_total_usd: c.monto_total_usd
    }))
    
    dialogPago.value = true
  } catch (e) {
    alert('Error cargando cuotas')
  }
}

const confirmarPagoEfectivo = async () => {
  try {
    await api.post(`/cuotas/${cuotaSeleccionada.value}/pagar-efectivo`)
    alert('✅ Pago registrado')
    dialogPago.value = false
    await cargarDatos()
  } catch (e) {
    alert('Error registrando pago')
  }
}

const exportarExcel = () => {
  const datos = financiamientosFiltrados.value.map(f => ({
    Codigo: f.codigo,
    Cliente: f.cliente_nombre,
    Cedula: f.cliente_cedula,
    Fecha: formatearFecha(f.fecha_primera_cuota),
    Total_BS: f.monto_total_bs,
    Entrada_BS: f.monto_entrada_bs,
    Pendiente_BS: f.saldo_pendiente_bs,
    Estado: f.estado,
    Morosidad: f.morosidad.nombre,
    Progreso: f.porcentaje_pagado + '%'
  }))
  
  const headers = Object.keys(datos[0] || {})
  const csv = [
    headers.join(','),
    ...datos.map(row => headers.map(h => `"${row[h]}"`).join(','))
  ].join('\n')
  
  const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' })
  const link = document.createElement('a')
  link.href = URL.createObjectURL(blob)
  link.download = `financiamientos_${new Date().toISOString().split('T')[0]}.csv`
  link.click()
}

onMounted(() => {
  cargarDatos()
})
</script>