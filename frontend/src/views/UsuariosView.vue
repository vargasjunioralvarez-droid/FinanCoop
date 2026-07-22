<template>
  <v-container fluid class="pa-0">
    <div class="background-gradient"></div>
    
    <v-row class="ma-0">
      <v-col cols="12" class="pa-4">
        <!-- HEADER PREMIUM -->
        <div class="header-premium d-flex align-center justify-space-between flex-wrap">
          <div class="d-flex align-center">
            <div class="icon-wrapper pulse-animation">
              <v-icon size="32" color="white">mdi-shield-account</v-icon>
            </div>
            <div class="ml-3">
              <h1 class="text-h4 font-weight-bold text-white">Gestión de Usuarios</h1>
              <p class="text-subtitle-2 text-white" style="opacity: 0.7;">Administración de accesos al sistema</p>
            </div>
          </div>
          <div class="d-flex align-center" style="gap: 12px;">
            <v-chip class="step-chip" color="transparent" size="large">
              <span class="text-white font-weight-bold">{{ usuarios.length }} Usuarios</span>
            </v-chip>
            <v-btn v-if="esAdmin" color="#4caf50" rounded="pill" @click="abrirDialogCrear" elevation="0">
              <v-icon start>mdi-account-plus</v-icon>Nuevo Usuario
            </v-btn>
          </div>
        </div>

        <!-- TABLA PREMIUM -->
        <v-row class="mt-4">
          <v-col cols="12">
            <v-card class="glass-card rounded-xl" elevation="0">
              <v-card-title class="text-h6 font-weight-bold text-white pa-4 d-flex align-center">
                <v-icon color="#4facfe" class="mr-2">mdi-account-group</v-icon>
                Lista de Usuarios
                <v-spacer></v-spacer>
                <v-chip color="#4facfe" variant="tonal" size="small">{{ usuarios.length }} registros</v-chip>
              </v-card-title>
              <v-card-text class="pa-4 pt-0">
                <div class="table-wrapper">
                  <v-data-table
                    :items="usuarios"
                    :headers="headers"
                    :loading="cargando"
                    :items-per-page="10"
                    class="premium-table"
                  >
                    <template v-slot:item.id="{ item }">
                      <span class="text-caption" style="color: rgba(255,255,255,0.3);">#{{ item.id }}</span>
                    </template>
                    <template v-slot:item.username="{ item }">
                      <div class="d-flex align-center">
                        <v-avatar size="32" :color="colorRolBg(item.rol)" class="mr-2">
                          <span class="text-caption font-weight-bold text-white">{{ item.username?.charAt(0).toUpperCase() }}</span>
                        </v-avatar>
                        <div>
                          <div class="text-white font-weight-bold">{{ item.nombre || item.username }}</div>
                          <div class="text-caption" style="color: rgba(255,255,255,0.3);">@{{ item.username }}</div>
                        </div>
                      </div>
                    </template>
                    <template v-slot:item.rol="{ item }">
                      <v-chip :color="colorRol(item.rol)" size="x-small" variant="flat">{{ item.rol }}</v-chip>
                    </template>
                    <template v-slot:item.tienda="{ item }">
                      <span v-if="item.tienda_nombre" class="text-white">{{ item.tienda_nombre }}</span>
                      <v-chip v-else-if="item.rol === 'admin'" color="error" size="x-small" variant="tonal">Todas</v-chip>
                      <span v-else class="text-caption" style="color: rgba(255,255,255,0.3);">-</span>
                    </template>
                    <template v-slot:item.activo="{ item }">
                      <v-chip :color="item.activo ? 'success' : 'grey'" size="x-small" variant="flat">
                        {{ item.activo ? 'Activo' : 'Inactivo' }}
                      </v-chip>
                    </template>
                    <template v-slot:item.acciones="{ item }">
                      <div v-if="esAdmin" class="d-flex gap-1">
                        <v-btn icon="mdi-pencil" size="x-small" color="primary" variant="tonal" @click="editarUsuario(item)" />
                        <v-btn icon="mdi-delete" size="x-small" color="error" variant="tonal" @click="eliminarUsuario(item)" />
                      </div>
                      <span v-else class="text-caption" style="color: rgba(255,255,255,0.3);">-</span>
                    </template>
                  </v-data-table>
                </div>
                <div v-if="usuarios.length === 0 && !cargando" class="empty-state glass-effect rounded-xl mt-2">
                  <v-icon size="32" color="rgba(255,255,255,0.1)">mdi-account-off</v-icon>
                  <div class="text-caption" style="color: rgba(255,255,255,0.3);">No hay usuarios registrados</div>
                </div>
              </v-card-text>
            </v-card>
          </v-col>
        </v-row>
      </v-col>
    </v-row>

    <!-- DIALOG: Crear/Editar Usuario -->
    <v-dialog v-model="dialogUsuario" max-width="500">
      <v-card class="dialog-card">
        <v-card-title class="text-white pa-4" :style="`background: linear-gradient(135deg, ${usuarioEditando ? '#ffd54f, #f9a825' : '#4caf50, #2e7d32'});`">
          <v-icon start>{{ usuarioEditando ? 'mdi-pencil' : 'mdi-account-plus' }}</v-icon>
          {{ usuarioEditando ? 'Editar Usuario' : 'Nuevo Usuario' }}
        </v-card-title>
        <v-card-text class="pa-5">
          <v-text-field v-model="formUsuario.username" label="Usuario *" :disabled="!!usuarioEditando" variant="solo-filled" density="comfortable" dark class="custom-input mb-4" placeholder="Ej: ana" />
          <v-text-field v-model="formUsuario.password" label="Contraseña" type="password" variant="solo-filled" density="comfortable" dark class="custom-input mb-4" :placeholder="usuarioEditando ? '••••••••' : 'Mínimo 8 caracteres'" />
          <v-text-field v-model="formUsuario.nombre" label="Nombre completo" variant="solo-filled" density="comfortable" dark class="custom-input mb-4" placeholder="Ej: Ana García" />
          <v-text-field v-model="formUsuario.email" label="Email" variant="solo-filled" density="comfortable" dark class="custom-input mb-4" placeholder="Ej: ana@coop.com" />
          <v-select v-model="formUsuario.rol" :items="rolesDisponibles" label="Rol *" variant="solo-filled" density="comfortable" dark class="custom-input mb-4" />
          <v-select v-if="formUsuario.rol !== 'admin'" v-model="formUsuario.tienda_id" :items="tiendas" item-title="nombre" item-value="id" label="Asignar a Tienda/Cooperativa *" variant="solo-filled" density="comfortable" dark class="custom-input mb-4" />
          <v-switch v-model="formUsuario.activo" label="Usuario activo" color="#4caf50" hide-details class="mt-2" />
        </v-card-text>
        <v-card-actions class="pa-4">
          <v-btn @click="dialogUsuario = false" variant="text" color="grey">Cancelar</v-btn>
          <v-spacer></v-spacer>
          <v-btn :color="usuarioEditando ? '#ffd54f' : '#4caf50'" rounded="pill" @click="guardarUsuario" :loading="guardando" elevation="0">
            {{ usuarioEditando ? 'Actualizar' : 'Crear' }}
          </v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <!-- DIALOG: Eliminar -->
    <v-dialog v-model="dialogEliminar" max-width="400">
      <v-card class="dialog-card">
        <v-card-title class="text-white pa-4" style="background: linear-gradient(135deg, #f44336, #c62828);">
          <v-icon start>mdi-delete</v-icon>¿Eliminar usuario?
        </v-card-title>
        <v-card-text class="pa-4">
          <p class="text-white">¿Estás seguro de eliminar a <strong>{{ usuarioAEliminar?.username }}</strong>?</p>
          <p class="text-caption" style="color: rgba(255,255,255,0.3);">Esta acción no se puede deshacer.</p>
        </v-card-text>
        <v-card-actions class="pa-4">
          <v-btn @click="dialogEliminar = false" variant="text" color="grey">Cancelar</v-btn>
          <v-spacer></v-spacer>
          <v-btn color="#f44336" rounded="pill" @click="confirmarEliminar" elevation="0">Eliminar</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>
  </v-container>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { api } from '@/config/api'

const usuarios = ref([])
const tiendas = ref([])
const cargando = ref(false)
const guardando = ref(false)
const dialogUsuario = ref(false)
const dialogEliminar = ref(false)
const usuarioEditando = ref(null)
const usuarioAEliminar = ref(null)

const formUsuario = ref({ username: '', password: '', nombre: '', email: '', rol: 'cajero', tienda_id: null, activo: true })

const esAdmin = computed(() => {
  const rol = localStorage.getItem('admin_rol')
  return rol === 'admin_central'
})

const rolesDisponibles = [
  { title: 'Administrador Central (ve todo)', value: 'admin_central' },
  { title: 'Administrador Tienda', value: 'admin_tienda' },
  { title: 'Cajero', value: 'cajero' }
]

const headers = [
  { title: '#', key: 'id', width: '60px' },
  { title: 'Usuario', key: 'username' },
  { title: 'Email', key: 'email' },
  { title: 'Rol', key: 'rol' },
  { title: 'Tienda', key: 'tienda' },
  { title: 'Estado', key: 'activo' },
  { title: 'Acciones', key: 'acciones', sortable: false }
]

const colorRol = (rol) => ({ admin: 'error', tienda: 'primary', cajero: 'warning' })[rol] || 'grey'
const colorRolBg = (rol) => ({ admin: '#f44336', tienda: '#4facfe', cajero: '#ffd54f' })[rol] || '#78909C'

const cargarTiendas = async () => {
  try { const d = await api.get('/admin/tiendas'); tiendas.value = Array.isArray(d) ? d : [] } catch (e) {}
}

const cargarUsuarios = async () => {
  cargando.value = true
  try { usuarios.value = await api.get('/admin/usuarios') } catch (e) { if (e.response?.status === 401) { localStorage.clear(); window.location.href = '/login' } }
  finally { cargando.value = false }
}

const guardarUsuario = async () => {
  if (!formUsuario.value.username) { alert('Usuario requerido'); return }
  if (formUsuario.value.rol !== 'admin' && !formUsuario.value.tienda_id) { alert('Seleccione una tienda'); return }
  guardando.value = true
  try {
    const payload = { username: formUsuario.value.username, nombre: formUsuario.value.nombre, email: formUsuario.value.email, rol: formUsuario.value.rol, activo: formUsuario.value.activo, tienda_id: formUsuario.value.rol === 'admin' ? null : formUsuario.value.tienda_id }
    if (formUsuario.value.password) payload.password = formUsuario.value.password
    if (usuarioEditando.value) { await api.put(`/admin/usuarios/${usuarioEditando.value.id}`, payload); alert('✅ Actualizado') }
    else { if (!formUsuario.value.password) { alert('Contraseña requerida'); guardando.value = false; return }; await api.post('/admin/usuarios', payload); alert('✅ Creado') }
    dialogUsuario.value = false; await cargarUsuarios()
  } catch (e) { alert('❌ Error: ' + (e.response?.data?.detail || e.message)) }
  finally { guardando.value = false }
}

const confirmarEliminar = async () => {
  try { await api.delete(`/admin/usuarios/${usuarioAEliminar.value.id}`); alert('✅ Eliminado'); dialogEliminar.value = false; await cargarUsuarios() }
  catch (e) { alert('❌ Error al eliminar') }
}

const abrirDialogCrear = () => {
  usuarioEditando.value = null
  formUsuario.value = { username: '', password: '', nombre: '', email: '', rol: 'cajero', tienda_id: null, activo: true }
  dialogUsuario.value = true
}
const editarUsuario = (u) => {
  usuarioEditando.value = u
  formUsuario.value = { username: u.username, password: '', nombre: u.nombre || '', email: u.email || '', rol: u.rol || 'cajero', tienda_id: u.tienda_id || null, activo: u.activo !== undefined ? u.activo : true }
  dialogUsuario.value = true
}
const eliminarUsuario = (u) => { usuarioAEliminar.value = u; dialogEliminar.value = true }

onMounted(() => {
  if (!localStorage.getItem('admin_token')) { window.location.href = '/login'; return }
  cargarTiendas(); cargarUsuarios()
})
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
.dialog-card { background: #1a1f2e !important; border: 1px solid rgba(255,255,255,0.08) !important; border-radius: 16px !important; }
.table-wrapper { overflow-x: auto; }
.premium-table { background: transparent !important; }
.premium-table :deep(th) { color: rgba(255,255,255,0.7) !important; font-weight: 700 !important; font-size: 0.75rem !important; text-transform: uppercase; padding: 12px 8px !important; border-bottom: 1px solid rgba(255,255,255,0.06) !important; }
.premium-table :deep(td) { color: rgba(255,255,255,0.9) !important; padding: 10px 8px !important; border-bottom: 1px solid rgba(255,255,255,0.03) !important; }
.premium-table :deep(tr:hover) { background: rgba(255,255,255,0.02) !important; }

/* ✅ CAMPOS ESPACIADOS Y LABEL FIJO ARRIBA */
.custom-input :deep(.v-field) { background: rgba(255,255,255,0.06) !important; border-radius: 12px !important; border: 1px solid rgba(255,255,255,0.12) !important; min-height: 52px !important; padding-top: 8px !important; }
.custom-input :deep(.v-field--focused) { border-color: #4facfe !important; background: rgba(255,255,255,0.08) !important; }
.custom-input :deep(.v-label) { color: rgba(255,255,255,0.8) !important; font-weight: 600 !important; font-size: 12px !important; top: 8px !important; transform: none !important; position: absolute !important; }
.custom-input :deep(.v-field--focused .v-label) { color: #4facfe !important; }
.custom-input :deep(.v-field__input) { color: white !important; padding-top: 20px !important; padding-bottom: 6px !important; min-height: auto !important; }
.custom-input :deep(.v-field__input::placeholder) { color: rgba(255,255,255,0.3) !important; font-weight: 400 !important; opacity: 1 !important; }
.custom-input :deep(.v-field__outline) { display: none; }
.custom-input :deep(.v-select__selection-text) { color: white !important; }
.custom-input :deep(.v-select__selection) { color: white !important; padding-top: 20px !important; }

.empty-state { padding: 24px; text-align: center; border: 1px dashed rgba(255,255,255,0.08); }
.gap-1 { gap: 4px; }
@media (max-width: 600px) { .header-premium { flex-direction: column; gap: 12px; align-items: stretch !important; } }
</style>