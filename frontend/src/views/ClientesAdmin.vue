<template>
  <v-container>
    <v-row>
      <v-col cols="12">
        <div class="d-flex justify-space-between align-center mb-4">
          <h1 class="text-h4">👥 Clientes</h1>
          <v-chip color="success">Admin</v-chip>
        </div>
      </v-col>
    </v-row>

    <!-- Buscador -->
    <v-col cols="12">
      <v-card class="mb-4">
        <v-card-text>
          <v-text-field
            v-model="busqueda"
            label="Buscar por Cédula o Nombre"
            prepend-inner-icon="mdi-magnify"
            @keyup.enter="buscar"
            clearable
            variant="outlined"
            density="comfortable"
          />
          <v-btn 
            color="primary" 
            @click="buscar" 
            block 
            class="mt-3"
            :loading="cargando"
          >
            <v-icon start>mdi-magnify</v-icon>
            Buscar
          </v-btn>
        </v-card-text>
      </v-card>
    </v-col>

    <!-- Tabla de clientes -->
    <v-col cols="12">
      <v-data-table
        :items="clientes"
        :headers="headers"
        :loading="cargando"
        :items-per-page="10"
        class="elevation-1"
      >
        <template v-slot:item.nivel="{ item }">
          <v-chip :color="colorNivel(item.nivel)" size="small">
            {{ item.nivel }}
          </v-chip>
        </template>

        <template v-slot:item.acciones="{ item }">
          <div class="d-flex gap-1">
            <v-btn icon="mdi-eye" size="small" color="info" @click="verDetalle(item)"></v-btn>
            <v-btn icon="mdi-pencil" size="small" color="primary" @click="editarCliente(item)"></v-btn>
            <v-btn icon="mdi-delete" size="small" color="error" @click="eliminarCliente(item)"></v-btn>
          </div>
        </template>
      </v-data-table>
    </v-col>

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

    <!-- Dialog: Detalle -->
    <v-dialog v-model="dialogDetalle" max-width="600">
      <v-card v-if="clienteSeleccionado">
        <v-card-title>
          {{ clienteSeleccionado.nombre }}
          <v-chip :color="colorNivel(clienteSeleccionado.nivel)" class="ml-2">
            {{ clienteSeleccionado.nivel }}
          </v-chip>
        </v-card-title>
        <v-card-text>
          <p><strong>Cédula:</strong> {{ clienteSeleccionado.cedula }}</p>
          <p><strong>Teléfono:</strong> {{ clienteSeleccionado.telefono }}</p>
          <p><strong>Email:</strong> {{ clienteSeleccionado.email || 'N/A' }}</p>
          <p><strong>Score:</strong> {{ clienteSeleccionado.score }}</p>
          <p><strong>Nivel:</strong> {{ clienteSeleccionado.nivel }}</p>
        </v-card-text>
        <v-card-actions>
          <v-btn @click="dialogDetalle = false">Cerrar</v-btn>
        </v-card-actions>
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
const dialogEditar = ref(false)
const dialogDetalle = ref(false)
const clienteEditando = ref(null)
const clienteSeleccionado = ref(null)

const token = localStorage.getItem('admin_token')

const headers = [
  { title: 'Nombre', key: 'nombre' },
  { title: 'Cédula', key: 'cedula' },
  { title: 'Teléfono', key: 'telefono' },
  { title: 'Nivel', key: 'nivel' },
  { title: 'Score', key: 'score' },
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

const cargarClientes = async () => {
  cargando.value = true
  try {
    const data = await api.get('/clientes')
    clientes.value = data
  } catch (error) {
    console.error('Error cargando clientes:', error)
    alert('Error al cargar clientes')
  } finally {
    cargando.value = false
  }
}

const buscar = async () => {
  if (!busqueda.value.trim()) {
    await cargarClientes()
    return
  }
  
  cargando.value = true
  try {
    const data = await api.get(`/clientes/buscar/${busqueda.value}`)
    if (data.encontrado) {
      clientes.value = [data]
    } else {
      alert('Cliente no encontrado')
      clientes.value = []
    }
  } catch (error) {
    console.error('Error buscando:', error)
    clientes.value = []
  } finally {
    cargando.value = false
  }
}

const verDetalle = (cliente) => {
  clienteSeleccionado.value = cliente
  dialogDetalle.value = true
}

const editarCliente = (cliente) => {
  clienteEditando.value = { ...cliente }
  dialogEditar.value = true
}

const guardarEdicion = async () => {
  guardando.value = true
  try {
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
    
    alert('✅ Cliente actualizado')
    dialogEditar.value = false
    await cargarClientes()
  } catch (error) {
    console.error('Error actualizando:', error)
    alert('❌ Error al actualizar cliente')
  } finally {
    guardando.value = false
  }
}

const eliminarCliente = async (cliente) => {
  if (!confirm(`¿Eliminar a ${cliente.nombre}?`)) return
  
  try {
    await api.delete(`/clientes/${cliente.id}`, {
      headers: { 'Authorization': `Bearer ${token}` }
    })
    alert('✅ Cliente eliminado')
    await cargarClientes()
  } catch (error) {
    console.error('Error eliminando:', error)
    alert('❌ Error al eliminar cliente')
  }
}

onMounted(() => {
  if (!token) {
    alert('Debes iniciar sesión como administrador')
    return
  }
  cargarClientes()
})
</script>