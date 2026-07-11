<template>
  <v-container>
    <v-row>
      <v-col cols="12">
        <div class="d-flex justify-space-between align-center mb-4">
          <h1 class="text-h4">👥 Gestión de Usuarios</h1>
          <v-btn color="success" @click="abrirDialogCrear">
            <v-icon start>mdi-account-plus</v-icon>
            Nuevo Usuario
          </v-btn>
        </div>
      </v-col>
    </v-row>

    <!-- Tabla de usuarios -->
    <v-row>
      <v-col cols="12">
        <v-card>
          <v-card-text>
            <v-data-table
              :items="usuarios"
              :headers="headers"
              :loading="cargando"
              :items-per-page="10"
            >
              <template v-slot:item.activo="{ item }">
                <v-chip :color="item.activo ? 'success' : 'error'" size="small">
                  {{ item.activo ? 'Activo' : 'Inactivo' }}
                </v-chip>
              </template>

              <template v-slot:item.rol="{ item }">
                <v-chip :color="item.rol === 'admin' ? 'error' : 'info'" size="small">
                  {{ item.rol }}
                </v-chip>
              </template>

              <template v-slot:item.acciones="{ item }">
                <v-btn icon="mdi-pencil" size="small" color="primary" @click="editarUsuario(item)"></v-btn>
                <v-btn icon="mdi-delete" size="small" color="error" @click="eliminarUsuario(item)"></v-btn>
              </template>
            </v-data-table>
          </v-card-text>
        </v-card>
      </v-col>
    </v-row>

    <!-- Dialog: Crear/Editar Usuario -->
    <v-dialog v-model="dialogUsuario" max-width="500">
      <v-card>
        <v-card-title>
          {{ usuarioEditando ? 'Editar Usuario' : 'Nuevo Usuario' }}
        </v-card-title>
        <v-card-text>
          <v-text-field
            v-model="formUsuario.username"
            label="Usuario *"
            :disabled="!!usuarioEditando"
            variant="outlined"
          />
          <v-text-field
            v-model="formUsuario.password"
            label="Contraseña"
            type="password"
            variant="outlined"
            :rules="[v => !usuarioEditando ? !!v || 'Requerido' : true]"
          />
          <v-text-field
            v-model="formUsuario.nombre"
            label="Nombre completo"
            variant="outlined"
          />
          <v-text-field
            v-model="formUsuario.email"
            label="Email"
            variant="outlined"
          />
          <v-select
            v-model="formUsuario.rol"
            :items="['admin', 'cajero', 'usuario']"
            label="Rol"
            variant="outlined"
          />
          <v-switch
            v-model="formUsuario.activo"
            label="Usuario activo"
            color="success"
          />
        </v-card-text>
        <v-card-actions>
          <v-btn @click="dialogUsuario = false">Cancelar</v-btn>
          <v-btn color="primary" @click="guardarUsuario" :loading="guardando">
            {{ usuarioEditando ? 'Actualizar' : 'Crear' }}
          </v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <!-- Dialog: Confirmar Eliminar -->
    <v-dialog v-model="dialogEliminar" max-width="400">
      <v-card>
        <v-card-title class="text-error">¿Eliminar usuario?</v-card-title>
        <v-card-text>
          ¿Estás seguro de eliminar al usuario <strong>{{ usuarioAEliminar?.username }}</strong>?
        </v-card-text>
        <v-card-actions>
          <v-btn @click="dialogEliminar = false">Cancelar</v-btn>
          <v-btn color="error" @click="confirmarEliminar">Eliminar</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>
  </v-container>
</template>

<script setup>
import { ref, onMounted } from 'vue'

const API_URL = import.meta.env.VITE_API_URL || 'https://financoop.onrender.com'

// ✅ OBTENER TOKEN DIRECTAMENTE
const token = localStorage.getItem('admin_token')

const usuarios = ref([])
const cargando = ref(false)
const guardando = ref(false)
const dialogUsuario = ref(false)
const dialogEliminar = ref(false)
const usuarioEditando = ref(null)
const usuarioAEliminar = ref(null)

const formUsuario = ref({
  username: '',
  password: '',
  nombre: '',
  email: '',
  rol: 'usuario',
  activo: true
})

const headers = [
  { title: 'ID', key: 'id' },
  { title: 'Usuario', key: 'username' },
  { title: 'Nombre', key: 'nombre' },
  { title: 'Email', key: 'email' },
  { title: 'Rol', key: 'rol' },
  { title: 'Estado', key: 'activo' },
  { title: 'Acciones', key: 'acciones', sortable: false }
]

// ============================================================
// ✅ FUNCIÓN PARA PETICIONES CON TOKEN
// ============================================================
const apiCall = async (url, options = {}) => {
  const token = localStorage.getItem('admin_token')
  const response = await fetch(url, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${token}`,
      ...options.headers
    }
  })
  
  if (!response.ok) {
    if (response.status === 401) {
      localStorage.removeItem('admin_token')
      localStorage.removeItem('admin_rol')
      localStorage.removeItem('admin_username')
      window.location.href = '/admin-login'
    }
    const error = await response.json()
    throw new Error(error.detail || 'Error en la petición')
  }
  
  return response.json()
}

// ============================================================
// ✅ CARGAR USUARIOS
// ============================================================
const cargarUsuarios = async () => {
  cargando.value = true
  try {
    const data = await apiCall(`${API_URL}/admin/usuarios`)
    usuarios.value = data
    console.log('✅ Usuarios cargados:', usuarios.value)
  } catch (error) {
    console.error('Error cargando usuarios:', error)
    alert('Error al cargar usuarios: ' + error.message)
  } finally {
    cargando.value = false
  }
}

// ============================================================
// ✅ GUARDAR USUARIO
// ============================================================
const guardarUsuario = async () => {
  if (!formUsuario.value.username) {
    alert('El nombre de usuario es obligatorio')
    return
  }

  guardando.value = true
  try {
    const url = usuarioEditando.value 
      ? `${API_URL}/admin/usuarios/${usuarioEditando.value.id}`
      : `${API_URL}/admin/usuarios`
    
    const method = usuarioEditando.value ? 'PUT' : 'POST'
    
    const data = await apiCall(url, {
      method,
      body: JSON.stringify(formUsuario.value)
    })
    
    alert(usuarioEditando.value ? '✅ Usuario actualizado' : '✅ Usuario creado')
    dialogUsuario.value = false
    await cargarUsuarios()
  } catch (error) {
    console.error('Error guardando usuario:', error)
    alert('❌ Error: ' + error.message)
  } finally {
    guardando.value = false
  }
}

// ============================================================
// ✅ ELIMINAR USUARIO
// ============================================================
const confirmarEliminar = async () => {
  try {
    await apiCall(`${API_URL}/admin/usuarios/${usuarioAEliminar.value.id}`, {
      method: 'DELETE'
    })
    alert('✅ Usuario eliminado')
    dialogEliminar.value = false
    await cargarUsuarios()
  } catch (error) {
    console.error('Error eliminando usuario:', error)
    alert('❌ Error al eliminar usuario')
  }
}

// ============================================================
// ✅ FUNCIONES DE UI
// ============================================================
const abrirDialogCrear = () => {
  usuarioEditando.value = null
  formUsuario.value = {
    username: '',
    password: '',
    nombre: '',
    email: '',
    rol: 'usuario',
    activo: true
  }
  dialogUsuario.value = true
}

const editarUsuario = (usuario) => {
  usuarioEditando.value = usuario
  formUsuario.value = {
    username: usuario.username,
    password: '',
    nombre: usuario.nombre || '',
    email: usuario.email || '',
    rol: usuario.rol || 'usuario',
    activo: usuario.activo !== undefined ? usuario.activo : true
  }
  dialogUsuario.value = true
}

const eliminarUsuario = (usuario) => {
  usuarioAEliminar.value = usuario
  dialogEliminar.value = true
}

// ============================================================
// ✅ MOUNTED
// ============================================================
onMounted(() => {
  if (!token) {
    alert('Debes iniciar sesión como administrador')
    return
  }
  console.log('🔑 Token de admin:', token)
  cargarUsuarios()
})
</script>