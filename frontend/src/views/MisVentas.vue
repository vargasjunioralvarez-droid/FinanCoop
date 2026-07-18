<template>
  <v-container>
    <v-row>
      <v-col cols="12">
        <h1 class="text-h4 mb-2">🛒 Mis Ventas del Día</h1>
        <p class="text-subtitle-1 text-grey mb-4">{{ fechaHoy }} | 🏪 {{ tiendaNombre }}</p>
      </v-col>

      <v-col cols="12" sm="4">
        <v-card color="success" dark>
          <v-card-text class="text-center">
            <div class="text-h3">{{ ventasHoy.length }}</div>
            <div class="text-subtitle-1">Ventas Hoy</div>
          </v-card-text>
        </v-card>
      </v-col>
      <v-col cols="12" sm="4">
        <v-card color="primary" dark>
          <v-card-text class="text-center">
            <div class="text-h3">BS {{ formatearBS(totalHoy) }}</div>
            <div class="text-subtitle-1">Total Financiado</div>
          </v-card-text>
        </v-card>
      </v-col>
      <v-col cols="12" sm="4">
        <v-card color="warning" dark>
          <v-card-text class="text-center">
            <div class="text-h3">BS {{ formatearBS(totalEntrada) }}</div>
            <div class="text-subtitle-1">Entradas Cobradas</div>
          </v-card-text>
        </v-card>
      </v-col>

      <v-col cols="12">
        <v-card>
          <v-card-title>Ventas de Hoy</v-card-title>
          <v-card-text>
            <v-table>
              <thead>
                <tr><th>Código</th><th>Cliente</th><th>Monto</th><th>Entrada</th><th>Cuotas</th><th>Hora</th></tr>
              </thead>
              <tbody>
                <tr v-for="v in ventasHoy" :key="v.id">
                  <td><v-chip size="small">{{ v.codigo }}</v-chip></td>
                  <td>{{ v.cliente_nombre }}</td>
                  <td>BS {{ formatearBS(v.monto_total_bs) }}</td>
                  <td>BS {{ formatearBS(v.monto_entrada_bs) }}</td>
                  <td>{{ v.cuotas_aprobadas }}</td>
                  <td>{{ formatearHora(v.creado_en) }}</td>
                </tr>
              </tbody>
            </v-table>
            <v-alert v-if="ventasHoy.length === 0" type="info" class="mt-2">No hay ventas registradas hoy</v-alert>
          </v-card-text>
        </v-card>
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

onMounted(() => { cargarVentas(); cargarUsuario() })
</script>