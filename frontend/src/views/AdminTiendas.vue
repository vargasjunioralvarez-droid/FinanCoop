<template>
  <v-container>
    <v-row>
      <v-col cols="12">
        <h1 class="text-h4 mb-4">🏪 Gestión de Tiendas</h1>
      </v-col>

      <!-- Lista de Tiendas -->
      <v-col cols="12" md="6">
        <v-card>
          <v-card-title class="d-flex align-center">
            <v-icon class="mr-2">mdi-store</v-icon>
            Tiendas
            <v-spacer></v-spacer>
            <v-btn color="primary" size="small" @click="dialogTienda = true; tiendaEdit = null">
              <v-icon start>mdi-plus</v-icon>
              Nueva Tienda
            </v-btn>
          </v-card-title>
          <v-card-text>
            <v-table>
              <thead>
                <tr>
                  <th>Nombre</th>
                  <th>Código</th>
                  <th>Clientes</th>
                  <th>Créditos</th>
                  <th>Estado</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="t in tiendas" :key="t.id">
                  <td>{{ t.nombre }}</td>
                  <td><v-chip size="small">{{ t.codigo }}</v-chip></td>
                  <td>{{ t.total_clientes }}</td>
                  <td>{{ t.total_creditos }}</td>
                  <td>
                    <v-chip :color="t.activo ? 'success' : 'grey'" size="small">
                      {{ t.activo ? 'Activa' : 'Inactiva' }}
                    </v-chip>
                  </td>
                </tr>
              </tbody>
            </v-table>
          </v-card-text>
        </v-card>
      </v-col>

      <!-- Lista de Usuarios -->
      <v-col cols="12" md="6">
        <v-card>
          <v-card-title class="d-flex align-center">
            <v-icon class="mr-2">mdi-account-group</v-icon>
            Usuarios
            <v-spacer></v-spacer>
            <v-btn color="primary" size="small" @click="abrirCrearUsuario">
              <v-icon start>mdi-plus</v-icon>
              Nuevo Usuario
            </v-btn>
          </v-card-title>
          <v-card-text>
            <v-table>
              <thead>
                <tr>
                  <th>Usuario</th>
                  <th>Rol</th>
                  <th>Tienda</th>
                  <th>Activo</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="u in usuarios" :key="u.id">
                  <td>
                    <strong>{{ u.nombre || u.username }}</strong>
                    <div class="text-caption text-grey">{{ u.username }}</div>
                  </td>
                  <td>
                    <v-chip :color="colorRol(u.rol)" size="small">
                      {{ u.rol }}
                    </v-chip>
                  </td>
                  <td>{{ u.tienda_nombre || 'Todas' }}</td>
                  <td>
                    <v-chip :color="u.activo ? 'success' : 'grey'" size="small">
                      {{ u.activo ? 'Sí' : 'No' }}
                    </v-chip>
                  </td>
                </tr>
              </tbody>
            </v-table>
          </v-card-text>
        </v-card>
      </v-col>
    </v-row>

    <!-- Dialog: Crear/Editar Tienda -->
    <v-dialog v-model="dialogTienda" max-width="500">
      <v-card>
        <v-card-title>{{ tiendaEdit ? 'Editar' : 'Nueva' }} Tienda</v-card-title>
        <v-card-text>
          <v-text-field v-model="tiendaForm.nombre" label="Nombre de la tienda/cooperativa *" variant="outlined" required />
          <v-text-field v-model="tiendaForm.codigo" label="Código único *" variant="outlined" required hint="Ej: CCS-BQTO" />
          <v-text-field v-model="tiendaForm.direccion" label="Dirección" variant="outlined" />
          <v-text-field v-model="tiendaForm.telefono" label="Teléfono" variant="outlined" />
        </v-card-text>
        <v-card-actions>
          <v-btn @click="dialogTienda = false">Cancelar</v-btn>
          <v-btn color="primary" @click="guardarTienda" :loading="cargando">
            Guardar
          </v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <!-- Dialog: Crear Usuario -->
    <v-dialog v-model="dialogUsuario" max-width="500">
      <v-card>
        <v-card-title>Nuevo Usuario</v-card-title>
        <v-card-text>
          <v-text-field v-model="usuarioForm.username" label="Usuario *" variant="outlined" required />
          <v-text-field v-model="usuarioForm.password" label="Contraseña *" type="password" variant="outlined" required hint="Mínimo 8 caracteres" />
          <v-text-field v-model="usuarioForm.nombre" label="Nombre completo" variant="outlined" />
          <v-text-field v-model="usuarioForm.email" label="Email" variant="outlined" />
          
          <v-select
            v-model="usuarioForm.rol"
            :items="rolesDisponibles"
            label="Rol *"
            variant="outlined"
            required
          />
          
          <!-- 🔥 SELECTOR DE TIENDA (aparece si el rol NO es admin) -->
          <v-select
            v-if="usuarioForm.rol !== 'admin'"
            v-model="usuarioForm.tienda_id"
            :items="tiendasSelect"
            item-title="nombre"
            item-value="id"
            label="Asignar a Tienda/Cooperativa *"
            variant="outlined"
            required
          />
        </v-card-text>
        <v-card-actions>
          <v-btn @click="dialogUsuario = false">Cancelar</v-btn>
          <v-btn color="primary" @click="guardarUsuario" :loading="cargando">
            Crear Usuario
          </v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <v-snackbar v-model="snackbar.show" :color="snackbar.color">
      {{ snackbar.text }}
    </v-snackbar>
  </v-container>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { api } from '@/config/api'

// Datos
const tiendas = ref([])
const usuarios = ref([])
const cargando = ref(false)
const dialogTienda = ref(false)
const dialogUsuario = ref(false)
const tiendaEdit = ref(null)

const tiendaForm = ref({
  nombre: '',
  codigo: '',
  direccion: '',
  telefono: ''
})

const usuarioForm = ref({
  username: '',
  password: '',
  nombre: '',
  email: '',
  rol: 'cajero',
  tienda_id: null
})

const snackbar = ref({ show: false, text: '', color: 'success' })

// Roles disponibles
const rolesDisponibles = [
  { title: 'Administrador Central (ve todo)', value: 'admin' },
  { title: 'Tienda/Cooperativa (ve solo su tienda)', value: 'tienda' },
  { title: 'Cajero (ve solo su tienda)', value: 'cajero' }
]

// Tiendas para el select
const tiendasSelect = computed(() => 
  tiendas.value.filter(t => t.activo).map(t => ({ id: t.id, nombre: t.nombre }))
)

const colorRol = (rol) => {
  const colores = { admin: 'error', tienda: 'primary', cajero: 'warning' }
  return colores[rol] || 'grey'
}

// Cargar datos
const cargarTiendas = async () => {
  try {
    const data = await api.get('/admin/tiendas')
    tiendas.value = Array.isArray(data) ? data : []
  } catch (e) {
    console.error('Error cargando tiendas:', e)
  }
}

const cargarUsuarios = async () => {
  try {
    const data = await api.get('/admin/usuarios')
    usuarios.value = Array.isArray(data) ? data : []
  } catch (e) {
    console.error('Error cargando usuarios:', e)
  }
}

// Guardar tienda
const guardarTienda = async () => {
  if (!tiendaForm.value.nombre || !tiendaForm.value.codigo) {
    snackbar.value = { show: true, text: 'Nombre y código son requeridos', color: 'error' }
    return
  }

  cargando.value = true
  try {
    if (tiendaEdit.value) {
      await api.put(`/admin/tiendas/${tiendaEdit.value.id}`, tiendaForm.value)
      snackbar.value = { show: true, text: 'Tienda actualizada', color: 'success' }
    } else {
      await api.post('/admin/tiendas', tiendaForm.value)
      snackbar.value = { show: true, text: 'Tienda creada', color: 'success' }
    }
    dialogTienda.value = false
    tiendaForm.value = { nombre: '', codigo: '', direccion: '', telefono: '' }
    tiendaEdit.value = null
    await cargarTiendas()
  } catch (e) {
    snackbar.value = { show: true, text: e.response?.data?.detail || 'Error', color: 'error' }
  } finally {
    cargando.value = false
  }
}

// Crear usuario
const abrirCrearUsuario = () => {
  usuarioForm.value = { username: '', password: '', nombre: '', email: '', rol: 'cajero', tienda_id: null }
  dialogUsuario.value = true
}

const guardarUsuario = async () => {
  if (!usuarioForm.value.username || !usuarioForm.value.password) {
    snackbar.value = { show: true, text: 'Usuario y contraseña requeridos', color: 'error' }
    return
  }
  if (usuarioForm.value.rol !== 'admin' && !usuarioForm.value.tienda_id) {
    snackbar.value = { show: true, text: 'Debe seleccionar una tienda', color: 'error' }
    return
  }

  cargando.value = true
  try {
    await api.post('/admin/usuarios', {
      username: usuarioForm.value.username,
      password: usuarioForm.value.password,
      nombre: usuarioForm.value.nombre,
      email: usuarioForm.value.email,
      rol: usuarioForm.value.rol,
      tienda_id: usuarioForm.value.rol === 'admin' ? null : usuarioForm.value.tienda_id,
      activo: true
    })
    snackbar.value = { show: true, text: 'Usuario creado', color: 'success' }
    dialogUsuario.value = false
    await cargarUsuarios()
  } catch (e) {
    snackbar.value = { show: true, text: e.response?.data?.detail || 'Error', color: 'error' }
  } finally {
    cargando.value = false
  }
}

onMounted(() => {
  cargarTiendas()
  cargarUsuarios()
})
</script>