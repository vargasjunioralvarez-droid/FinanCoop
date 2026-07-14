<template>
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
          <template v-slot:item.estado="{ item }">
            <v-chip 
              :color="item.estado === 'aprobado' ? 'success' : 'warning'" 
              size="small"
            >
              {{ item.estado === 'aprobado' ? '✅ Aprobado' : '⏳ Pendiente' }}
            </v-chip>
          </template>
          
          <template v-slot:item.nivel="{ item }">
            <v-chip :color="colorNivel(item.nivel)" size="small">
              {{ item.nivel }}
            </v-chip>
          </template>
          
          <template v-slot:item.pin="{ item }">
            <v-chip color="primary" v-if="item.pin" size="small">{{ item.pin }}</v-chip>
            <span v-else class="text-grey text-caption">Sin PIN</span>
          </template>
          
          <template v-slot:item.acciones="{ item }">
            <div class="d-flex gap-1">
              <v-btn 
                icon="mdi-eye" 
                size="small" 
                color="info"
                @click="verDetalle(item)"
              ></v-btn>
              
              <!-- ✅ BOTÓN APROBAR (solo si está pendiente) -->
              <v-btn 
                v-if="esAdmin && item.estado !== 'aprobado'"
                icon="mdi-check-circle" 
                size="small" 
                color="success"
                @click="aprobarCliente(item)"
                :loading="aprobandoId === item.id"
              ></v-btn>
              
              <v-btn 
                v-if="esAdmin"
                icon="mdi-pencil" 
                size="small" 
                color="primary"
                @click="editarCliente(item)"
              ></v-btn>
              <v-btn 
                v-if="esAdmin"
                icon="mdi-delete" 
                size="small" 
                color="error"
                @click="eliminarCliente(item)"
              ></v-btn>
            </div>
          </template>
        </v-data-table>
      </v-col>
      
      <v-col cols="12" v-else-if="busquedaRealizada && !cargando">
        <v-alert type="info" border="start">
          No se encontraron clientes con: <strong>{{ busqueda }}</strong>
        </v-alert>
      </v-col>
    </v-row>
    
    <!-- Dialog: Aprobar Cliente -->
    <v-dialog v-model="dialogAprobar" max-width="400">
      <v-card>
        <v-card-title>✅ Aprobar Cliente</v-card-title>
        <v-card-text v-if="clienteAprobar">
          <p>¿Aprobar a <strong>{{ clienteAprobar.nombre }}</strong>?</p>
          <p class="text-caption text-grey">
            Se enviará un SMS con el PIN de acceso al número:<br>
            <strong>{{ clienteAprobar.telefono }}</strong>
          </p>
        </v-card-text>
        <v-card-actions>
          <v-btn @click="dialogAprobar = false">Cancelar</v-btn>
          <v-btn 
            color="success" 
            @click="confirmarAprobar" 
            :loading="aprobando"
          >
            <v-icon start>mdi-check</v-icon>
            Aprobar y Enviar PIN
          </v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <!-- Dialog: Editar Cliente -->
    <v-dialog v-model="dialogEditar" max-width="500">
      <v-card>
        <v-card-title>✏️ Editar Cliente</v-card-title>
        <v-card-text>
          <v-text-field v-model="clienteEditando.nombre" label="Nombre" variant="outlined" />
          <v-text-field v-model="clienteEditando.telefono" label="Teléfono" variant="outlined" />
          <v-text-field v-model="clienteEditando.email" label="Email" variant="outlined" />
          <v-textarea v-model="clienteEditando.direccion" label="Dirección" variant="outlined" rows="2" />
        </v-card-text>
        <v-card-actions>
          <v-btn @click="dialogEditar = false">Cancelar</v-btn>
          <v-btn color="primary" @click="guardarEdicion" :loading="guardando">Guardar</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

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
              <p><strong>Estado:</strong> 
                <v-chip 
                  :color="clienteSeleccionado.estado === 'aprobado' ? 'success' : 'warning'" 
                  size="small"
                >
                  {{ clienteSeleccionado.estado === 'aprobado' ? 'Aprobado' : 'Pendiente' }}
                </v-chip>
              </p>
              <p><strong>PIN:</strong> {{ clienteSeleccionado.pin || 'Sin PIN' }}</p>
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
    
    <!-- Dialog: Cuotas -->
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
import { api } from '@/config/api'

const busqueda = ref('')
const clientes = ref([])
const cargando = ref(false)
const guardando = ref(false)
const aprobando = ref(false)
const aprobandoId = ref(null)
const busquedaRealizada = ref(false)
const dialogDetalle = ref(false)
const dialogCuotas = ref(false)
const dialogEditar = ref(false)
const dialogAprobar = ref(false)
const clienteSeleccionado = ref(null)
const clienteEditando = ref(null)
const clienteAprobar = ref(null)
const financiamientosCliente = ref([])
const cuotas = ref([])

const esAdmin = localStorage.getItem('admin_rol') === 'admin'

const headers = [
  { title: 'Nombre', key: 'nombre', sortable: true },
  { title: 'Cédula', key: 'cedula', sortable: true },
  { title: 'Teléfono', key: 'telefono' },
  { title: 'Estado', key: 'estado' },
  { title: 'Nivel', key: 'nivel', sortable: true },
  { title: 'Score', key: 'score', sortable: true },
  { title: 'Compras', key: 'total_compras', sortable: true },
  { title: 'PIN', key: 'pin' },
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
    const data = await api.get(`/clientes/buscar/${busqueda.value}`)
    if (data.encontrado) {
      clientes.value = [data]
      cargando.value = false
      return
    }
  } catch (e) {}
  
  try {
    const financiamientos = await api.get('/financiamientos')
    const finEncontrado = financiamientos.find(f => 
      f.codigo.toLowerCase() === busqueda.value.toLowerCase()
    )
    if (finEncontrado) {
      const cliente = await api.get(`/clientes/${finEncontrado.cliente_id}`)
      if (!cliente.error) {
        clientes.value = [cliente]
        cargando.value = false
        return
      }
    }
  } catch (e) {}
  
  try {
    const todos = await api.get('/clientes')
    const filtrados = todos.filter(c => 
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
    const data = await api.get('/clientes')
    clientes.value = data
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
    const financiamientos = await api.get('/financiamientos')
    financiamientosCliente.value = financiamientos.filter(f => f.cliente_id === cliente.id)
  } catch (e) {
    financiamientosCliente.value = []
  }
}

const verCuotas = async (finId) => {
  try {
    const data = await api.get(`/financiamientos/${finId}/cuotas`)
    cuotas.value = data
    dialogCuotas.value = true
  } catch (e) {
    console.error('Error cargando cuotas:', e)
  }
}

// ✅ APROBAR CLIENTE
const aprobarCliente = (cliente) => {
  clienteAprobar.value = cliente
  dialogAprobar.value = true
}

const confirmarAprobar = async () => {
  if (!clienteAprobar.value) return
  
  aprobando.value = true
  aprobandoId.value = clienteAprobar.value.id
  
  try {
    const token = localStorage.getItem('admin_token')
    const response = await fetch(`${import.meta.env.VITE_API_URL || ''}/clientes/aprobar`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`
      },
      body: JSON.stringify({ cliente_id: clienteAprobar.value.id })
    })
    
    const data = await response.json()
    
    if (data.success) {
      alert(`✅ Cliente aprobado.\n📱 SMS enviado: ${data.sms_enviado ? 'Sí' : 'No'}\n🔑 PIN: ${data.cliente.pin}`)
      await cargarTodos()
    } else {
      alert('Error: ' + (data.error || 'No se pudo aprobar'))
    }
  } catch (error) {
    console.error('Error aprobando:', error)
    alert('Error al aprobar cliente')
  } finally {
    aprobando.value = false
    aprobandoId.value = null
    dialogAprobar.value = false
  }
}

const editarCliente = (cliente) => {
  clienteEditando.value = { ...cliente }
  dialogEditar.value = true
}

const guardarEdicion = async () => {
  guardando.value = true
  try {
    const token = localStorage.getItem('admin_token')
    const formData = new FormData()
    formData.append('nombre', clienteEditando.value.nombre)
    formData.append('telefono', clienteEditando.value.telefono)
    formData.append('email', clienteEditando.value.email || '')
    formData.append('direccion', clienteEditando.value.direccion || '')
    
    await api.put(`/clientes/${clienteEditando.value.id}`, formData, {
      headers: { 
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'multipart/form-data'
      }
    })
    
    alert('Cliente actualizado')
    dialogEditar.value = false
    await cargarTodos()
  } catch (error) {
    console.error('Error actualizando cliente:', error)
    alert('Error al actualizar cliente')
  } finally {
    guardando.value = false
  }
}

const eliminarCliente = async (cliente) => {
  if (!confirm(`¿Eliminar a ${cliente.nombre}?`)) return
  
  try {
    const token = localStorage.getItem('admin_token')
    await api.delete(`/clientes/${cliente.id}`, {
      headers: { 'Authorization': `Bearer ${token}` }
    })
    alert('Cliente eliminado')
    await cargarTodos()
  } catch (error) {
    console.error('Error eliminando cliente:', error)
    alert('Error al eliminar cliente')
  }
}

onMounted(() => {
  cargarTodos()
})
</script>