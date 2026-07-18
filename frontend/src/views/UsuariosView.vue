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
                <v-chip :color="colorRol(item.rol)" size="small">
                  {{ item.rol }}
                </v-chip>
              </template>

              <!-- 🔥 NUEVO: Mostrar tienda asignada -->
              <template v-slot:item.tienda="{ item }">
                <span v-if="item.tienda_nombre">{{ item.tienda_nombre }}</span>
                <v-chip v-else-if="item.rol === 'admin'" color="error" size="small">Todas</v-chip>
                <span v-else class="text-grey">-</span>
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
            :hint="usuarioEditando ? 'Dejar vacío para no cambiar' : 'Mínimo 8 caracteres'"
            persistent-hint
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
          
          <!-- 🔥 ROLES ACTUALIZADOS -->
          <v-select
            v-model="formUsuario.rol"
            :items="rolesDisponibles"
            label="Rol *"
            variant="outlined"
          />
          
          <!-- 🔥 SELECTOR DE TIENDA (solo si NO es admin) -->
          <v-select
            v-if="formUsuario.rol !== 'admin'"
            v-model="formUsuario.tienda_id"
            :items="tiendas"
            item-title="nombre"
            item-value="id"
            label="Asignar a Tienda/Cooperativa *"
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
import { api } from '@/config/api'

const usuarios = ref([])
const tiendas = ref([])  // 🔥 NUEVO
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
  rol: 'cajero',
  tienda_id: null,  // 🔥 NUEVO
  activo: true
})

// 🔥 Roles disponibles
const rolesDisponibles = [
  { title: 'Administrador Central (ve todo)', value: 'admin' },
  { title: 'Tienda/Cooperativa (ve solo su tienda)', value: 'tienda' },
  { title: 'Cajero (ve solo su tienda)', value: 'cajero' }
]

const headers = [
  { title: 'ID', key: 'id' },
  { title: 'Usuario', key: 'username' },
  { title: 'Nombre', key: 'nombre' },
  { title: 'Email', key: 'email' },
  { title: 'Rol', key: 'rol' },
  { title: 'Tienda', key: 'tienda' },  // 🔥 NUEVO
  { title: 'Estado', key: 'activo' },
  { title: 'Acciones', key: 'acciones', sortable: false }
]

// 🔥 Colores por rol
const colorRol = (rol) => {
  const colores = { admin: 'error', tienda: 'primary', cajero: 'warning' }
  return colores[rol] || 'grey'
}

// ============================================================
// ✅ CARGAR TIENDAS
// ============================================================
const cargarTiendas = async () => {
  try {
    const data = await api.get('/admin/tiendas')
    tiendas.value = Array.isArray(data) ? data : []
  } catch (e) {
    console.error('Error cargando tiendas:', e)
  }
}

// ============================================================
// ✅ CARGAR USUARIOS
// ============================================================
const cargarUsuarios = async () => {
  cargando.value = true
  try {
    const data = await api.get('/admin/usuarios')
    usuarios.value = data
    console.log('✅ Usuarios cargados:', usuarios.value.length)
  } catch (error) {
    console.error('❌ Error cargando usuarios:', error)
    if (error.response?.status === 401) {
      alert('⛔ Sesión expirada o no autorizado')
      localStorage.clear()
      window.location.href = '/login'
    } else {
      alert('Error al cargar usuarios: ' + (error.response?.data?.detail || error.message))
    }
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
  
  // 🔥 Validar tienda si no es admin
  if (formUsuario.value.rol !== 'admin' && !formUsuario.value.tienda_id) {
    alert('Debe seleccionar una tienda/cooperativa')
    return
  }

  guardando.value = true
  try {
    const payload = {
      username: formUsuario.value.username,
      nombre: formUsuario.value.nombre,
      email: formUsuario.value.email,
      rol: formUsuario.value.rol,
      activo: formUsuario.value.activo,
      tienda_id: formUsuario.value.rol === 'admin' ? null : formUsuario.value.tienda_id  // 🔥
    }
    
    // Solo enviar password si se ingresó uno
    if (formUsuario.value.password) {
      payload.password = formUsuario.value.password
    }

    if (usuarioEditando.value) {
      await api.put(`/admin/usuarios/${usuarioEditando.value.id}`, payload)
      alert('✅ Usuario actualizado')
    } else {
      if (!formUsuario.value.password) {
        alert('La contraseña es obligatoria para nuevos usuarios')
        guardando.value = false
        return
      }
      await api.post('/admin/usuarios', payload)
      alert('✅ Usuario creado')
    }
    
    dialogUsuario.value = false
    await cargarUsuarios()
  } catch (error) {
    console.error('❌ Error guardando usuario:', error)
    alert('❌ Error: ' + (error.response?.data?.detail || error.message))
  } finally {
    guardando.value = false
  }
}

// ============================================================
// ✅ ELIMINAR USUARIO
// ============================================================
const confirmarEliminar = async () => {
  try {
    await api.delete(`/admin/usuarios/${usuarioAEliminar.value.id}`)
    alert('✅ Usuario eliminado')
    dialogEliminar.value = false
    await cargarUsuarios()
  } catch (error) {
    console.error('❌ Error eliminando usuario:', error)
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
    rol: 'cajero',
    tienda_id: null,  // 🔥
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
    rol: usuario.rol || 'cajero',
    tienda_id: usuario.tienda_id || null,  // 🔥
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
  const token = localStorage.getItem('admin_token')
  if (!token) {
    alert('Debes iniciar sesión como administrador')
    window.location.href = '/login'
    return
  }
  console.log('🔑 Token presente:', token.substring(0, 30) + '...')
  cargarTiendas()   // 🔥 Cargar tiendas primero
  cargarUsuarios()
})
</script>