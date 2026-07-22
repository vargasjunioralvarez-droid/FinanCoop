<template>
  <v-container fluid class="pa-0">
    <div class="background-gradient"></div>
    
    <v-row class="ma-0">
      <v-col cols="12" class="pa-4">
        <!-- HEADER PREMIUM -->
        <div class="header-premium d-flex align-center justify-space-between flex-wrap">
          <div class="d-flex align-center">
            <div class="icon-wrapper pulse-animation">
              <v-icon size="32" color="white">mdi-store</v-icon>
            </div>
            <div class="ml-3">
              <h1 class="text-h4 font-weight-bold text-white">Gestión de Tiendas</h1>
              <p class="text-subtitle-2 text-white" style="opacity: 0.7;">Administración de cooperativas y usuarios</p>
            </div>
          </div>
          <v-chip class="step-chip" color="transparent" size="large">
            <span class="text-white font-weight-bold">{{ tiendas.length }} Tiendas</span>
          </v-chip>
        </div>

        <!-- TABLAS -->
        <v-row class="mt-4">
          <!-- TIENDAS -->
          <v-col cols="12" md="6">
            <v-card class="glass-card rounded-xl" elevation="0">
              <v-card-title class="text-h6 font-weight-bold text-white pa-4 d-flex align-center">
                <v-icon color="#4caf50" class="mr-2">mdi-store</v-icon>
                Tiendas
                <v-spacer></v-spacer>
                <v-btn v-if="esAdmin" color="#4caf50" size="small" rounded="pill" @click="abrirDialogTienda()" elevation="0">
                  <v-icon start>mdi-plus</v-icon>Nueva
                </v-btn>
              </v-card-title>
              <v-card-text class="pa-4 pt-0">
                <div class="table-wrapper">
                  <v-table class="premium-table">
                    <thead>
                      <tr>
                        <th>Nombre</th>
                        <th>Código</th>
                        <th class="text-center">Clientes</th>
                        <th class="text-center">Créditos</th>
                        <th class="text-center">Estado</th>
                        <th v-if="esAdmin" class="text-center">Acciones</th>
                      </tr>
                    </thead>
                    <tbody>
                      <tr v-for="t in tiendas" :key="t.id" class="fade-in">
                        <td>
                          <div class="d-flex align-center">
                            <v-avatar size="28" color="rgba(76,175,80,0.2)" class="mr-2">
                              <v-icon size="16" color="#4caf50">mdi-store</v-icon>
                            </v-avatar>
                            <span class="text-white font-weight-bold">{{ t.nombre }}</span>
                          </div>
                        </td>
                        <td><v-chip size="x-small" color="#4facfe" variant="tonal">{{ t.codigo }}</v-chip></td>
                        <td class="text-center"><span class="text-white">{{ t.total_clientes }}</span></td>
                        <td class="text-center"><span class="text-white">{{ t.total_creditos }}</span></td>
                        <td class="text-center">
                          <v-chip :color="t.activo ? 'success' : 'grey'" size="x-small" variant="flat">
                            {{ t.activo ? 'Activa' : 'Inactiva' }}
                          </v-chip>
                        </td>
                        <td v-if="esAdmin" class="text-center">
                          <div class="d-flex gap-1 justify-center">
                            <v-btn icon="mdi-pencil" size="x-small" color="primary" variant="tonal" @click="editarTienda(t)" />
                            <v-btn icon="mdi-delete" size="x-small" color="error" variant="tonal" @click="eliminarTienda(t)" />
                          </div>
                        </td>
                      </tr>
                    </tbody>
                  </v-table>
                </div>
                <div v-if="tiendas.length === 0" class="empty-state glass-effect rounded-xl mt-2">
                  <v-icon size="32" color="rgba(255,255,255,0.1)">mdi-store-off</v-icon>
                  <div class="text-caption" style="color: rgba(255,255,255,0.3);">No hay tiendas registradas</div>
                </div>
              </v-card-text>
            </v-card>
          </v-col>

          <!-- USUARIOS -->
          <v-col cols="12" md="6">
            <v-card class="glass-card rounded-xl" elevation="0">
              <v-card-title class="text-h6 font-weight-bold text-white pa-4 d-flex align-center">
                <v-icon color="#4facfe" class="mr-2">mdi-account-group</v-icon>
                Usuarios
                <v-spacer></v-spacer>
                <v-btn v-if="esAdmin" color="#4facfe" size="small" rounded="pill" @click="abrirCrearUsuario" elevation="0">
                  <v-icon start>mdi-plus</v-icon>Nuevo
                </v-btn>
              </v-card-title>
              <v-card-text class="pa-4 pt-0">
                <div class="table-wrapper">
                  <v-table class="premium-table">
                    <thead>
                      <tr>
                        <th>Usuario</th>
                        <th>Rol</th>
                        <th>Tienda</th>
                        <th class="text-center">Activo</th>
                        <th v-if="esAdmin" class="text-center">Acciones</th>
                      </tr>
                    </thead>
                    <tbody>
                      <tr v-for="u in usuarios" :key="u.id" class="fade-in">
                        <td>
                          <div>
                            <div class="text-white font-weight-bold">{{ u.nombre || u.username }}</div>
                            <div class="text-caption" style="color: rgba(255,255,255,0.3);">{{ u.username }}</div>
                          </div>
                        </td>
                        <td><v-chip :color="colorRol(u.rol)" size="x-small" variant="flat">{{ u.rol }}</v-chip></td>
                        <td><span class="text-white">{{ u.tienda_nombre || 'Todas' }}</span></td>
                        <td class="text-center">
                          <v-chip :color="u.activo ? 'success' : 'grey'" size="x-small" variant="flat">
                            {{ u.activo ? 'Sí' : 'No' }}
                          </v-chip>
                        </td>
                        <td v-if="esAdmin" class="text-center">
                          <div class="d-flex gap-1 justify-center">
                            <v-btn icon="mdi-pencil" size="x-small" color="primary" variant="tonal" @click="editarUsuario(u)" />
                            <v-btn icon="mdi-delete" size="x-small" color="error" variant="tonal" @click="confirmarEliminarUsuario(u)" />
                          </div>
                        </td>
                      </tr>
                    </tbody>
                  </v-table>
                </div>
                <div v-if="usuarios.length === 0" class="empty-state glass-effect rounded-xl mt-2">
                  <v-icon size="32" color="rgba(255,255,255,0.1)">mdi-account-off</v-icon>
                  <div class="text-caption" style="color: rgba(255,255,255,0.3);">No hay usuarios registrados</div>
                </div>
              </v-card-text>
            </v-card>
          </v-col>
        </v-row>
      </v-col>
    </v-row>

    <!-- DIALOG TIENDA -->
    <v-dialog v-model="dialogTienda" max-width="500">
      <v-card class="dialog-card">
        <v-card-title class="text-white pa-4" :style="`background: linear-gradient(135deg, ${tiendaEdit ? '#ffd54f, #f9a825' : '#4caf50, #2e7d32'});`">
          <v-icon start>{{ tiendaEdit ? 'mdi-pencil' : 'mdi-store' }}</v-icon>
          {{ tiendaEdit ? 'Editar' : 'Nueva' }} Tienda
        </v-card-title>
        <v-card-text class="pa-5">
          <v-text-field v-model="tiendaForm.nombre" label="Nombre de la tienda/cooperativa *" variant="solo-filled" density="comfortable" dark class="custom-input mb-4" placeholder="Ej: Cecosesola Barquisimeto" />
          <v-text-field v-model="tiendaForm.codigo" label="Código único *" variant="solo-filled" density="comfortable" dark class="custom-input mb-4" placeholder="Ej: CCS-BQTO" />
          <v-text-field v-model="tiendaForm.direccion" label="Dirección" variant="solo-filled" density="comfortable" dark class="custom-input mb-4" placeholder="Ej: Av. Principal, Centro" />
          <v-text-field v-model="tiendaForm.telefono" label="Teléfono" variant="solo-filled" density="comfortable" dark class="custom-input" placeholder="Ej: +584121234567" />
        </v-card-text>
        <v-card-actions class="pa-4">
          <v-btn @click="dialogTienda = false" variant="text" color="grey">Cancelar</v-btn>
          <v-spacer></v-spacer>
          <v-btn :color="tiendaEdit ? '#ffd54f' : '#4caf50'" rounded="pill" @click="guardarTienda" :loading="cargando" elevation="0">Guardar</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <!-- DIALOG USUARIO -->
    <v-dialog v-model="dialogUsuario" max-width="500">
      <v-card class="dialog-card">
        <v-card-title class="text-white pa-4" :style="`background: linear-gradient(135deg, ${usuarioEditando ? '#ffd54f, #f9a825' : '#4facfe, #6366f1'});`">
          <v-icon start>{{ usuarioEditando ? 'mdi-pencil' : 'mdi-account-plus' }}</v-icon>
          {{ usuarioEditando ? 'Editar Usuario' : 'Nuevo Usuario' }}
        </v-card-title>
        <v-card-text class="pa-5">
          <v-text-field v-model="usuarioForm.username" label="Usuario *" :disabled="!!usuarioEditando" variant="solo-filled" density="comfortable" dark class="custom-input mb-4" placeholder="Ej: ana" />
          <v-text-field v-model="usuarioForm.password" label="Contraseña" type="password" variant="solo-filled" density="comfortable" dark class="custom-input mb-4" :placeholder="usuarioEditando ? '••••••••' : 'Mínimo 8 caracteres'" />
          <v-text-field v-model="usuarioForm.nombre" label="Nombre completo" variant="solo-filled" density="comfortable" dark class="custom-input mb-4" placeholder="Ej: Ana García" />
          <v-text-field v-model="usuarioForm.email" label="Email" variant="solo-filled" density="comfortable" dark class="custom-input mb-4" placeholder="Ej: ana@coop.com" />
          <v-select v-model="usuarioForm.rol" :items="rolesDisponibles" label="Rol *" variant="solo-filled" density="comfortable" dark class="custom-input mb-4" />
          <v-select v-if="usuarioForm.rol !== 'admin'" v-model="usuarioForm.tienda_id" :items="tiendasSelect" item-title="nombre" item-value="id" label="Asignar a Tienda/Cooperativa *" variant="solo-filled" density="comfortable" dark class="custom-input" />
        </v-card-text>
        <v-card-actions class="pa-4">
          <v-btn @click="dialogUsuario = false" variant="text" color="grey">Cancelar</v-btn>
          <v-spacer></v-spacer>
          <v-btn :color="usuarioEditando ? '#ffd54f' : '#4facfe'" rounded="pill" @click="guardarUsuario" :loading="cargando" elevation="0">
            {{ usuarioEditando ? 'Actualizar' : 'Crear Usuario' }}
          </v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <!-- DIALOG ELIMINAR -->
    <v-dialog v-model="dialogEliminar" max-width="400">
      <v-card class="dialog-card">
        <v-card-title class="text-white pa-4" style="background: linear-gradient(135deg, #f44336, #c62828);">
          <v-icon start>mdi-delete</v-icon>¿Eliminar?
        </v-card-title>
        <v-card-text class="pa-4">
          <p class="text-white">¿Estás seguro de eliminar <strong>{{ eliminandoNombre }}</strong>?</p>
          <p class="text-caption" style="color: rgba(255,255,255,0.3);">Esta acción no se puede deshacer.</p>
        </v-card-text>
        <v-card-actions class="pa-4">
          <v-btn @click="dialogEliminar = false" variant="text" color="grey">Cancelar</v-btn>
          <v-spacer></v-spacer>
          <v-btn color="#f44336" rounded="pill" @click="ejecutarEliminar" :loading="cargando" elevation="0">Eliminar</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <v-snackbar v-model="snackbar.show" :color="snackbar.color" timeout="5000" rounded="pill">
      {{ snackbar.text }}
    </v-snackbar>
  </v-container>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { api } from '@/config/api'

const tiendas = ref([])
const usuarios = ref([])
const cargando = ref(false)
const dialogTienda = ref(false)
const dialogUsuario = ref(false)
const dialogEliminar = ref(false)
const tiendaEdit = ref(null)
const usuarioEditando = ref(null)
const eliminandoId = ref(null)
const eliminandoNombre = ref('')
const eliminandoTipo = ref('')

const tiendaForm = ref({ nombre: '', codigo: '', direccion: '', telefono: '' })
const usuarioForm = ref({ username: '', password: '', nombre: '', email: '', rol: 'cajero', tienda_id: null })
const snackbar = ref({ show: false, text: '', color: 'success' })

const esAdmin = computed(() => {
  const rol = localStorage.getItem('admin_rol')
  return rol === 'admin_central' || rol === 'admin'
})

const rolesDisponibles = [
  { title: 'Administrador Central (ve todo)', value: 'admin_central' },
  { title: 'Administrador Tienda', value: 'admin_tienda' },
  { title: 'Cajero', value: 'cajero' }
]

const tiendasSelect = computed(() => tiendas.value.filter(t => t.activo).map(t => ({ id: t.id, nombre: t.nombre })))
const colorRol = (rol) => ({ admin: 'error', tienda: 'primary', cajero: 'warning' })[rol] || 'grey'

const cargarTiendas = async () => {
  try { const d = await api.get('/admin/tiendas'); tiendas.value = Array.isArray(d) ? d : [] } catch (e) {}
}
const cargarUsuarios = async () => {
  try { const d = await api.get('/admin/usuarios'); usuarios.value = Array.isArray(d) ? d : [] } catch (e) {}
}

const abrirDialogTienda = (t = null) => {
  if (t) { tiendaEdit.value = t; tiendaForm.value = { nombre: t.nombre, codigo: t.codigo, direccion: t.direccion || '', telefono: t.telefono || '' } }
  else { tiendaEdit.value = null; tiendaForm.value = { nombre: '', codigo: '', direccion: '', telefono: '' } }
  dialogTienda.value = true
}
const editarTienda = (t) => abrirDialogTienda(t)

const guardarTienda = async () => {
  if (!tiendaForm.value.nombre || !tiendaForm.value.codigo) { snackbar.value = { show: true, text: 'Nombre y código requeridos', color: 'error' }; return }
  cargando.value = true
  try {
    if (tiendaEdit.value) { await api.put(`/admin/tiendas/${tiendaEdit.value.id}`, tiendaForm.value); snackbar.value = { show: true, text: 'Tienda actualizada', color: 'success' } }
    else { await api.post('/admin/tiendas', tiendaForm.value); snackbar.value = { show: true, text: 'Tienda creada', color: 'success' } }
    dialogTienda.value = false; tiendaEdit.value = null; tiendaForm.value = { nombre: '', codigo: '', direccion: '', telefono: '' }
    await cargarTiendas()
  } catch (e) { snackbar.value = { show: true, text: e.response?.data?.detail || 'Error', color: 'error' } }
  finally { cargando.value = false }
}

const eliminarTienda = (t) => {
  eliminandoId.value = t.id; eliminandoNombre.value = t.nombre; eliminandoTipo.value = 'tienda'
  dialogEliminar.value = true
}

const abrirCrearUsuario = () => {
  usuarioEditando.value = null
  usuarioForm.value = { username: '', password: '', nombre: '', email: '', rol: 'cajero', tienda_id: null }
  dialogUsuario.value = true
}
const editarUsuario = (u) => {
  usuarioEditando.value = u
  usuarioForm.value = { username: u.username, password: '', nombre: u.nombre || '', email: u.email || '', rol: u.rol || 'cajero', tienda_id: u.tienda_id || null }
  dialogUsuario.value = true
}

const guardarUsuario = async () => {
  if (!usuarioForm.value.username) { snackbar.value = { show: true, text: 'Usuario requerido', color: 'error' }; return }
  if (usuarioForm.value.rol !== 'admin' && !usuarioForm.value.tienda_id) { snackbar.value = { show: true, text: 'Seleccione una tienda', color: 'error' }; return }
  cargando.value = true
  try {
    const payload = { username: usuarioForm.value.username, nombre: usuarioForm.value.nombre, email: usuarioForm.value.email, rol: usuarioForm.value.rol, tienda_id: usuarioForm.value.rol === 'admin' ? null : usuarioForm.value.tienda_id, activo: true }
    if (usuarioForm.value.password) payload.password = usuarioForm.value.password
    if (usuarioEditando.value) { await api.put(`/admin/usuarios/${usuarioEditando.value.id}`, payload); snackbar.value = { show: true, text: 'Usuario actualizado', color: 'success' } }
    else { if (!usuarioForm.value.password) { snackbar.value = { show: true, text: 'Contraseña requerida', color: 'error' }; cargando.value = false; return }; await api.post('/admin/usuarios', payload); snackbar.value = { show: true, text: 'Usuario creado', color: 'success' } }
    dialogUsuario.value = false; usuarioEditando.value = null
    await cargarUsuarios()
  } catch (e) { snackbar.value = { show: true, text: e.response?.data?.detail || 'Error', color: 'error' } }
  finally { cargando.value = false }
}

const confirmarEliminarUsuario = (u) => {
  eliminandoId.value = u.id; eliminandoNombre.value = u.username; eliminandoTipo.value = 'usuario'
  dialogEliminar.value = true
}

const ejecutarEliminar = async () => {
  cargando.value = true
  try {
    if (eliminandoTipo.value === 'tienda') {
      await api.delete(`/admin/tiendas/${eliminandoId.value}`)
      snackbar.value = { show: true, text: 'Tienda eliminada', color: 'success' }
      await cargarTiendas()
    } else {
      await api.delete(`/admin/usuarios/${eliminandoId.value}`)
      snackbar.value = { show: true, text: 'Usuario eliminado', color: 'success' }
      await cargarUsuarios()
    }
    dialogEliminar.value = false
  } catch (e) { snackbar.value = { show: true, text: e.response?.data?.detail || 'Error', color: 'error' } }
  finally { cargando.value = false }
}

onMounted(() => { cargarTiendas(); cargarUsuarios() })
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
.custom-input { margin-bottom: 4px; }
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
.fade-in { animation: fadeIn 0.4s ease; }
@keyframes fadeIn { from { opacity: 0; transform: translateY(10px); } to { opacity: 1; transform: translateY(0); } }
@media (max-width: 600px) { .header-premium { flex-direction: column; gap: 12px; align-items: stretch !important; } }
</style>