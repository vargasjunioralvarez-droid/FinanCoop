<<template>
  <v-container>
    <v-row>
      <v-col cols="12">
        <h1 class="text-h4 mb-4">👥 Clientes</h1>
      </v-col>
      
      <!-- Buscador -->
      <v-col cols="12">
        <v-card class="mb-4">
          <v-card-text>
            <v-text-field
              v-model="busqueda"
              label="Buscar por Cédula, Nombre o Código de Financiamiento"
              prepend-inner-icon="mdi-magnify"
              @keyup.enter="buscar"
              clearable
              variant="outlined"
              density="comfortable"
              hint="Ej: 25474725, Juan Pérez, F-123456"
              persistent-hint
            ></v-text-field>
            
            <v-btn 
              color="primary" 
              @click="buscar" 
              block 
              class="mt-3"
              size="large"
              :loading="cargando"
            >
              <v-icon start>mdi-magnify</v-icon>
              Buscar
            </v-btn>
          </v-card-text>
        </v-card>
      </v-col>
      
      <!-- Resultados -->
      <v-col cols="12" v-if="clientes.length > 0">
        <v-data-table
          :items="clientes"
          :headers="headers"
          :items-per-page="10"
          class="elevation-1"
        >
          <template v-slot:item.nivel="{ item }">
            <v-chip :color="colorNivel(item.nivel)" size="small">
              {{ item.nivel }}
            </v-chip>
          </template>
          
          <template v-slot:item.score="{ item }">
            <v-chip color="info" size="small">{{ item.score }}</v-chip>
          </template>
          
          <template v-slot:item.total_compras="{ item }">
            <v-chip color="primary" size="small">{{ item.total_compras }}</v-chip>
          </template>
          
          <template v-slot:item.pin="{ item }">
            <v-chip color="primary" v-if="item.pin" size="small">{{ item.pin }}</v-chip>
            <span v-else class="text-grey text-caption">Sin PIN</span>
          </template>
          
          <template v-slot:item.acciones="{ item }">
            <v-btn 
              icon="mdi-eye" 
              size="small" 
              color="info"
              @click="verDetalle(item)"
            ></v-btn>
          </template>
        </v-data-table>
      </v-col>
      
      <v-col cols="12" v-else-if="busquedaRealizada && !cargando">
        <v-alert type="info" border="start">
          No se encontraron clientes con: <strong>{{ busqueda }}</strong>
        </v-alert>
      </v-col>
    </v-row>
    
    <!-- Dialog: Detalle del Cliente -->
    <v-dialog v-model="dialogDetalle" max-width="600">
      <v-card v-if="clienteSeleccionado">
        <v-card-title class="text-h5">
          {{ clienteSeleccionado.nombre }}
          <v-chip :color="colorNivel(clienteSeleccionado.nivel)" class="ml-2">
            {{ clienteSeleccionado.nivel }}
          </v-chip>
        </v-card-title>
        
        <v-card-text>
          <v-row>
            <v-col cols="6">
              <p><strong>Cédula:</strong> {{ clienteSeleccionado.cedula }}</p>
              <p><strong>Teléfono:</strong> {{ clienteSeleccionado.telefono }}</p>
              <p><strong>Email:</strong> {{ clienteSeleccionado.email || 'N/A' }}</p>
            </v-col>
            <v-col cols="6">
              <p><strong>Score:</strong> {{ clienteSeleccionado.score }} compras</p>
              <p><strong>Total Compras:</strong> {{ clienteSeleccionado.total_compras }}</p>
              <p><strong>PIN App:</strong> {{ clienteSeleccionado.pin || 'Sin PIN' }}</p>
            </v-col>
          </v-row>
          
          <v-divider class="my-3"></v-divider>
          
          <h3 class="text-h6 mb-2">Financiamientos</h3>
          
          <v-alert 
            v-if="!financiamientosCliente.length" 
            type="info" 
            density="compact"
          >
            Sin financiamientos
          </v-alert>
          
          <v-expansion-panels v-else>
            <v-expansion-panel
              v-for="fin in financiamientosCliente"
              :key="fin.id"
            >
              <v-expansion-panel-title>
                <div class="d-flex align-center w-100">
                  <v-icon :color="fin.estado === 'activo' ? 'success' : 'grey'" class="mr-2">
                    {{ fin.estado === 'activo' ? 'mdi-clock-outline' : 'mdi-check-circle' }}
                  </v-icon>
                  <span class="flex-grow-1">{{ fin.codigo }}</span>
                  <v-chip :color="fin.estado === 'activo' ? 'warning' : 'success'" size="small">
                    {{ fin.estado }}
                  </v-chip>
                </div>
              </v-expansion-panel-title>
              
              <v-expansion-panel-text>
                <p><strong>Descripción:</strong> {{ fin.descripcion }}</p>
                <p><strong>Total:</strong> BS {{ formatearBS(fin.monto_total_bs) }}</p>
                <p><strong>Entrada:</strong> BS {{ formatearBS(fin.monto_entrada_bs) }}</p>
                <p><strong>Cuotas:</strong> {{ fin.cuotas_aprobadas }}</p>
                <p><strong>Cuota mensual:</strong> BS {{ formatearBS(fin.monto_cuota_bs) }}</p>
                <p><strong>Tasa:</strong> {{ fin.tasa_aplicada }} BS/$</p>
                <p><strong>Fecha:</strong> {{ formatearFecha(fin.fecha_creacion) }}</p>
                
                <v-btn 
                  color="primary" 
                  size="small" 
                  class="mt-2"
                  @click="verCuotas(fin.id)"
                >
                  Ver Cuotas
                </v-btn>
              </v-expansion-panel-text>
            </v-expansion-panel>
          </v-expansion-panels>
        </v-card-text>
        
        <v-card-actions>
          <v-btn @click="dialogDetalle = false">Cerrar</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>
    
    <!-- Dialog: Cuotas del Financiamiento -->
    <v-dialog v-model="dialogCuotas" max-width="500">
      <v-card>
        <v-card-title>
          <v-btn icon @click="dialogCuotas = false" class="mr-2">
            <v-icon>mdi-arrow-left</v-icon>
          </v-btn>
          Cuotas
        </v-card-title>
        <v-card-text>
          <v-list>
            <v-list-item 
              v-for="c in cuotas" 
              :key="c.id"
              :class="{
                'bg-success-lighten-4': c.estado === 'pagada',
                'bg-error-lighten-4': c.dias_atraso > 0,
                'bg-warning-lighten-4': c.estado === 'pendiente' && c.dias_atraso === 0
              }"
              class="mb-2 rounded"
            >
              <v-list-item-title>
                <v-icon 
                  :color="c.estado === 'pagada' ? 'success' : c.dias_atraso > 0 ? 'error' : 'warning'"
                  class="mr-2"
                >
                  {{ c.estado === 'pagada' ? 'mdi-check-circle' : c.dias_atraso > 0 ? 'mdi-alert-circle' : 'mdi-clock-outline' }}
                </v-icon>
                Cuota #{{ c.numero }}
              </v-list-item-title>
              
              <v-list-item-subtitle>
                <v-chip 
                  :color="c.estado === 'pagada' ? 'success' : c.dias_atraso > 0 ? 'error' : 'warning'" 
                  size="small"
                >
                  {{ c.estado }}
                </v-chip>
                <span v-if="c.dias_atraso > 0" class="text-error ml-2">
                  {{ c.dias_atraso }} días atraso
                </span>
              </v-list-item-subtitle>
              
              <template v-slot:append>
                <div class="text-right">
                  <div class="text-h6">BS {{ formatearBS(c.monto_total_bs) }}</div>
                  <div class="text-caption text-grey">Ref: ${{ formatearUSD(c.monto_total_usd) }}</div>
                  <div v-if="c.monto_interes_mora_bs > 0" class="text-error text-caption">
                    +BS {{ formatearBS(c.monto_interes_mora_bs) }} mora
                  </div>
                  <div class="text-caption">{{ formatearFecha(c.fecha_vencimiento) }}</div>
                </div>
              </template>
            </v-list-item>
          </v-list>
        </v-card-text>
      </v-card>
    </v-dialog>
  </v-container>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import axios from 'axios'

const API_URL = 'http://localhost:8000'

const busqueda = ref('')
const clientes = ref([])
const cargando = ref(false)
const busquedaRealizada = ref(false)
const dialogDetalle = ref(false)
const dialogCuotas = ref(false)
const clienteSeleccionado = ref(null)
const financiamientosCliente = ref([])
const cuotas = ref([])

const headers = [
  { title: 'Nombre', key: 'nombre', sortable: true },
  { title: 'Cédula', key: 'cedula', sortable: true },
  { title: 'Teléfono', key: 'telefono' },
  { title: 'Nivel', key: 'nivel', sortable: true },
  { title: 'Score', key: 'score', sortable: true },
  { title: 'Compras', key: 'total_compras', sortable: true },
  { title: 'PIN App', key: 'pin' },
  { title: 'Acciones', key: 'acciones', sortable: false }
]

const colorNivel = (nivel) => {
  const colores = { 
    nuevo: 'grey', 
    bronce: 'brown', 
    plata: 'blue', 
    oro: 'amber', 
    platino: 'purple' 
  }
  return colores[nivel] || 'grey'
}

const formatearBS = (monto) => {
  if (!monto) return '0,00'
  return Number(monto).toLocaleString('es-VE', { 
    minimumFractionDigits: 2, 
    maximumFractionDigits: 2 
  })
}

const formatearUSD = (monto) => {
  if (!monto) return '0.00'
  return Number(monto).toLocaleString('en-US', { 
    minimumFractionDigits: 2, 
    maximumFractionDigits: 2 
  })
}

const formatearFecha = (fechaStr) => {
  if (!fechaStr) return ''
  const fecha = new Date(fechaStr)
  return fecha.toLocaleDateString('es-VE', { 
    day: '2-digit', 
    month: '2-digit', 
    year: 'numeric' 
  })
}

const buscar = async () => {
  if (!busqueda.value.trim()) {
    await cargarTodos()
    return
  }
  
  cargando.value = true
  busquedaRealizada.value = true
  
  try {
    // Buscar por cédula primero
    const resCedula = await axios.get(`${API_URL}/clientes/buscar/${busqueda.value}`)
    if (resCedula.data.encontrado) {
      clientes.value = [resCedula.data]
      cargando.value = false
      return
    }
  } catch (e) {
    // No encontrado por cédula, continuar
  }
  
  try {
    // Buscar por código de financiamiento
    const resFin = await axios.get(`${API_URL}/financiamientos`)
    const finEncontrado = resFin.data.find(f => 
      f.codigo.toLowerCase() === busqueda.value.toLowerCase()
    )
    
    if (finEncontrado) {
      const resCliente = await axios.get(`${API_URL}/clientes/${finEncontrado.cliente_id}`)
      if (!resCliente.data.error) {
        clientes.value = [resCliente.data]
        cargando.value = false
        return
      }
    }
  } catch (e) {
    // Error buscando financiamiento
  }
  
  try {
    // Buscar por nombre (filtrar todos los clientes)
    const resTodos = await axios.get(`${API_URL}/clientes`)
    const filtrados = resTodos.data.filter(c => 
      c.nombre.toLowerCase().includes(busqueda.value.toLowerCase())
    )
    clientes.value = filtrados
  } catch (e) {
    console.error('Error buscando:', e)
    clientes.value = []
  } finally {
    cargando.value = false
  }
}

const cargarTodos = async () => {
  cargando.value = true
  try {
    const res = await axios.get(`${API_URL}/clientes`)
    clientes.value = res.data
  } catch (e) {
    console.error('Error cargando clientes:', e)
  } finally {
    cargando.value = false
  }
}

const verDetalle = async (cliente) => {
  clienteSeleccionado.value = cliente
  dialogDetalle.value = true
  
  try {
    const res = await axios.get(`${API_URL}/financiamientos`)
    financiamientosCliente.value = res.data.filter(f => f.cliente_id === cliente.id)
  } catch (e) {
    console.error('Error cargando financiamientos:', e)
    financiamientosCliente.value = []
  }
}

const verCuotas = async (finId) => {
  try {
    const res = await axios.get(`${API_URL}/financiamientos/${finId}/cuotas`)
    cuotas.value = res.data
    dialogCuotas.value = true
  } catch (e) {
    console.error('Error cargando cuotas:', e)
  }
}

onMounted(() => {
  cargarTodos()
})
</script>