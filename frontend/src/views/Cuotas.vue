<template>
  <v-row>
    <v-col cols="12">
      <h1 class="text-h4 mb-4">Cuotas - Financiamiento #{{ id }}</h1>
      <v-btn to="/financiamientos" class="mb-4">Volver</v-btn>
    </v-col>
    
    <v-col cols="12">
      <v-data-table :items="cuotas" :headers="headers">
        <template v-slot:item.estado="{ item }">
          <v-chip :color="item.estado === 'pagada' ? 'success' : 'warning'">
            {{ item.estado }}
          </v-chip>
        </template>
        
        <template v-slot:item.acciones="{ item }">
          <v-btn 
            v-if="item.estado === 'pendiente'" 
            color="primary" 
            size="small" 
            @click="pagar(item.id)"
          >
            Pagar
          </v-btn>
        </template>
      </v-data-table>
    </v-col>
  </v-row>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import axios from 'axios'

const props = defineProps(['id'])
const cuotas = ref([])

const headers = [
  { title: 'Cuota', key: 'numero' },
  { title: 'Monto Base', key: 'monto_base' },
  { title: 'Interés Mora', key: 'monto_interes' },
  { title: 'Total', key: 'monto_total' },
  { title: 'Vencimiento', key: 'fecha_vencimiento' },
  { title: 'Estado', key: 'estado' },
  { title: 'Acciones', key: 'acciones' }
]

const cargar = async () => {
  try {
    import { API_URL } from '@/config/api'
    cuotas.value = res.data
  } catch (error) {
    console.error('Error cargando cuotas:', error)
  }
}

const pagar = async (cuotaId) => {
  try {
const res = await axios.get(`${API_URL}/financiamientos/${props.id}/cuotas`)
await axios.post(`${API_URL}/cuotas/${cuotaId}/pagar`)
  } catch (error) {
    console.error('Error pagando:', error)
  }
}

onMounted(cargar)
</script>