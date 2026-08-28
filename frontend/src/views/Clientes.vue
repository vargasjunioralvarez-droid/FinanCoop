<template>
  <v-container fluid class="pa-0">
    <div class="background-gradient"></div>
    
    <v-row class="ma-0">
      <v-col cols="12" class="pa-4">
        <!-- HEADER PREMIUM -->
        <div class="header-premium d-flex align-center justify-space-between flex-wrap">
          <div class="d-flex align-center">
            <div class="icon-wrapper pulse-animation">
              <v-icon size="32" color="white">mdi-account-group</v-icon>
            </div>
            <div class="ml-3">
              <h1 class="text-h4 font-weight-bold text-white">Gestión de Clientes</h1>
              <p class="text-subtitle-2 text-white" style="opacity: 0.7;">Administración de clientes y solicitudes</p>
            </div>
          </div>
          <div class="d-flex align-center" style="gap: 12px;">
            <v-chip class="step-chip" color="transparent" size="large">
              <span class="text-white font-weight-bold">{{ clientes.length }} Clientes</span>
            </v-chip>
          </div>
        </div>

        <!-- TABS PREMIUM -->
        <div class="mt-4">
          <v-tabs v-model="tabActiva" color="#4facfe" grow class="premium-tabs">
            <v-tab value="verificados">
              <v-icon start size="20">mdi-check-circle</v-icon>
              <span class="font-weight-bold">Verificados ({{ clientesVerificados.length }})</span>
            </v-tab>
            <v-tab value="pendientes">
              <v-icon start size="20">mdi-clock-outline</v-icon>
              <span class="font-weight-bold">Por Verificar ({{ clientesPendientes.length }})</span>
            </v-tab>
          </v-tabs>

          <v-window v-model="tabActiva" class="mt-4">
            
            <!-- PESTAÑA: VERIFICADOS -->
            <v-window-item value="verificados">
              <v-card class="glass-card rounded-xl" elevation="0">
                <v-card-text class="pa-4">
                  <div class="d-flex align-center mb-3 flex-wrap" style="gap: 12px;">
                    <div class="search-wrapper flex-grow-1">
                      <v-text-field 
                        v-model="busquedaVerificados" 
                        label="Buscar cliente..." 
                        prepend-inner-icon="mdi-magnify" 
                        density="compact" 
                        hide-details 
                        variant="outlined"
                        dark
                        class="custom-input"
                      />
                    </div>
                    <v-chip color="success" variant="tonal" size="small">
                      <v-icon start size="16">mdi-check-circle</v-icon>
                      {{ clientesVerificados.length }} verificados
                    </v-chip>
                  </div>

                  <v-data-table 
                    :items="clientesVerificadosFiltrados" 
                    :headers="headersVerificados" 
                    :items-per-page="10"
                    class="premium-table"
                  >
                    <template v-slot:item.estado="{ item }">
                      <v-chip color="success" size="small" variant="flat">✅ Aprobado</v-chip>
                    </template>
                    <template v-slot:item.pin="{ item }">
  <v-chip v-if="item.pin && esAdminCentral" color="primary" size="small" variant="tonal">{{ item.pin }}</v-chip>
  <span v-else-if="item.pin" class="text-caption" style="color: rgba(255,255,255,0.3);">••••••</span>
  <span v-else class="text-caption" style="color: rgba(255,255,255,0.3);">Sin PIN</span>
</template>
                    <template v-slot:item.nivel="{ item }">
                      <div class="d-flex align-center">
                        <div class="level-dot" :style="`background: ${nivelColor2(item.nivel)}`"></div>
                        <v-chip :color="nivelColor2(item.nivel)" size="x-small" variant="tonal">{{ item.nivel }}</v-chip>
                      </div>
                    </template>
                    <template v-slot:item.acciones="{ item }">
                      <div class="d-flex gap-1">
                        <v-btn icon="mdi-eye" size="x-small" color="info" variant="tonal" @click="verDetalle(item)" />
                        <v-btn v-if="esAdminCentral" icon="mdi-pencil" size="x-small" color="primary" variant="tonal" @click="editarCliente(item)" />
                        <v-btn v-if="esAdminCentral" icon="mdi-delete" size="x-small" color="error" variant="tonal" @click="eliminarCliente(item)" />
                      </div>
                    </template>
                  </v-data-table>
                </v-card-text>
              </v-card>
            </v-window-item>

            <!-- PESTAÑA: POR VERIFICAR -->
            <v-window-item value="pendientes">
              <v-card class="glass-card rounded-xl" elevation="0">
                <v-card-text class="pa-4">
                  <div class="d-flex align-center mb-3 flex-wrap" style="gap: 12px;">
                    <div class="search-wrapper flex-grow-1">
                      <v-text-field 
                        v-model="busquedaPendientes" 
                        label="Buscar cliente..." 
                        prepend-inner-icon="mdi-magnify" 
                        density="compact" 
                        hide-details 
                        variant="outlined"
                        dark
                        class="custom-input"
                      />
                    </div>
                    <v-chip color="warning" variant="tonal" size="small">
                      <v-icon start size="16">mdi-clock-outline</v-icon>
                      {{ clientesPendientes.length }} pendientes
                    </v-chip>
                  </div>

                  <v-data-table 
                    :items="clientesPendientesFiltrados" 
                    :headers="headersPendientes" 
                    :items-per-page="10"
                    class="premium-table"
                  >
                    <template v-slot:item.estado="{ item }">
                      <v-chip color="warning" size="small" variant="flat">⏳ Pendiente</v-chip>
                    </template>
                    <template v-slot:item.foto="{ item }">
                      <div class="d-flex align-center">
                        <v-avatar v-if="tieneFotoReal(item)" size="36" class="cursor-pointer" @click="verFotoAmpliada(item)">
                          <v-img :src="item.url_cedula" cover>
                            <template v-slot:placeholder><v-icon color="grey" size="20">mdi-image</v-icon></template>
                          </v-img>
                        </v-avatar>
                        <v-icon v-else :color="item.url_cedula ? 'success' : 'grey'" size="20" class="mr-2">
                          {{ item.url_cedula ? 'mdi-check-circle' : 'mdi-image-off' }}
                        </v-icon>
                        <v-btn v-if="tieneFotoReal(item)" icon="mdi-magnify" size="x-small" color="primary" variant="text" @click="verFotoAmpliada(item)" title="Ver foto" />
                        <span v-else class="text-caption" style="color: rgba(255,255,255,0.3);">{{ item.url_cedula ? 'Sí' : 'No' }}</span>
                      </div>
                    </template>
                    <template v-slot:item.acciones="{ item }">
                      <div class="d-flex gap-1">
                        <v-btn icon="mdi-eye" size="x-small" color="info" variant="tonal" @click="verDetalle(item)" />
                        <v-btn v-if="esAdminCentral" icon="mdi-check-circle" size="x-small" color="success" variant="tonal" @click="aprobarCliente(item)" :loading="aprobandoId === item.id" title="Aprobar" />
                        <v-btn v-if="esAdminCentral" icon="mdi-delete" size="x-small" color="error" variant="tonal" @click="eliminarCliente(item)" />
                      </div>
                    </template>
                  </v-data-table>

                  <v-alert v-if="clientesPendientes.length === 0" type="success" variant="tonal" class="mt-4 rounded-xl">
                    <div class="d-flex align-center"><v-icon size="28" class="mr-2">mdi-check-circle</v-icon><div><strong>Todo al día</strong><div class="text-caption">No hay clientes pendientes por verificar</div></div></div>
                  </v-alert>
                </v-card-text>
              </v-card>
            </v-window-item>

          </v-window>
        </div>
      </v-col>
    </v-row>

    <!-- DIALOGS (se mantienen igual) -->
    <v-dialog v-model="dialogFoto" max-width="800">
      <v-card v-if="fotoCliente" class="glass-card">
        <v-card-title class="d-flex align-center text-white">
          <v-icon class="mr-2">mdi-card-account-details</v-icon>Foto de Cédula - {{ fotoCliente.nombre }}
          <v-spacer></v-spacer>
          <v-btn icon="mdi-close" variant="text" @click="dialogFoto = false" color="white" />
        </v-card-title>
        <v-card-text class="text-center pa-4">
          <v-img :src="fotoCliente.url_cedula" max-height="70vh" contain class="rounded-lg">
            <template v-slot:placeholder><v-row align="center" justify="center" class="fill-height"><v-progress-circular indeterminate color="primary" /></v-row></template>
          </v-img>
          <div class="mt-4 d-flex justify-center gap-2">
            <v-btn :href="fotoCliente.url_cedula" target="_blank" color="#4facfe" rounded="pill" prepend-icon="mdi-open-in-new">Abrir</v-btn>
            <v-btn color="#6366f1" rounded="pill" prepend-icon="mdi-download" @click="descargarFoto(fotoCliente)">Descargar</v-btn>
          </div>
        </v-card-text>
      </v-card>
    </v-dialog>

    <v-dialog v-model="dialogAprobar" max-width="450">
      <v-card class="glass-card">
        <v-card-title class="text-h5 text-white pa-4" style="background: linear-gradient(135deg, #4caf50, #2e7d32);">
          <v-icon start>mdi-check-circle</v-icon>Aprobar Cliente
        </v-card-title>
        <v-card-text class="pt-4" v-if="clienteAprobar">
          <p class="text-white">¿Aprobar a <strong>{{ clienteAprobar.nombre }}</strong>?</p>
          <div v-if="tieneFotoReal(clienteAprobar)" class="mt-3 text-center">
            <v-img :src="clienteAprobar.url_cedula" max-height="150" contain class="rounded-lg" />
          </div>
          <div class="glass-effect pa-3 mt-3 rounded-lg">
            <div class="d-flex justify-space-between"><span style="color: rgba(255,255,255,0.5);">Cédula</span><span class="text-white">{{ clienteAprobar.cedula }}</span></div>
            <div class="d-flex justify-space-between mt-1"><span style="color: rgba(255,255,255,0.5);">Teléfono</span><span class="text-white">{{ clienteAprobar.telefono }}</span></div>
          </div>
          
          <v-alert v-if="pinGenerado" type="info" variant="tonal" class="mt-3 rounded-xl" density="compact">
            <div class="text-center">
              <div class="text-caption">PIN generado:</div>
              <div class="text-h4 font-weight-bold" style="letter-spacing: 8px;">{{ pinGenerado }}</div>
              <div class="text-caption mt-1">Entrega este PIN al cliente</div>
            </div>
          </v-alert>
          <p class="text-caption mt-3" style="color: rgba(255,255,255,0.3);" v-if="!pinGenerado">Se enviará SMS/WhatsApp con el PIN</p>
        </v-card-text>
        <v-card-actions class="pa-4">
          <v-spacer></v-spacer>
          <v-btn v-if="!pinGenerado" @click="dialogAprobar = false" variant="text" color="grey">Cancelar</v-btn>
          <v-btn v-if="!pinGenerado" color="#4caf50" rounded="pill" @click="confirmarAprobar" :loading="aprobando">
            <v-icon start>mdi-send</v-icon>Aprobar
          </v-btn>
          <v-btn v-else color="#4facfe" rounded="pill" @click="dialogAprobar = false; pinGenerado = null">Cerrar</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <v-dialog v-model="dialogDetalle" max-width="700">
      <v-card v-if="clienteSeleccionado" class="glass-card">
        <v-card-title class="text-h5 text-white pa-4">
          {{ clienteSeleccionado.nombre }}
          <v-chip :color="clienteSeleccionado.estado === 'aprobado' ? 'success' : 'warning'" class="ml-2" size="small">
            {{ clienteSeleccionado.estado === 'aprobado' ? '✅ Aprobado' : '⏳ Pendiente' }}
          </v-chip>
        </v-card-title>
        <v-card-text class="pa-4">
          <v-row>
            <v-col cols="12" md="6">
              <div class="glass-effect pa-3 rounded-lg mb-2">
                <p class="text-white"><strong>Cédula:</strong> {{ clienteSeleccionado.cedula }}</p>
                <p class="text-white"><strong>Teléfono:</strong> {{ clienteSeleccionado.telefono }}</p>
                <p class="text-white"><strong>Email:</strong> {{ clienteSeleccionado.email || 'N/A' }}</p>
                <p class="text-white"><strong>Dirección:</strong> {{ clienteSeleccionado.direccion || 'N/A' }}</p>
              </div>
            </v-col>
            <v-col cols="12" md="6">
              <div class="glass-effect pa-3 rounded-lg mb-2">
                <p class="text-white"><strong>Score:</strong> {{ clienteSeleccionado.score }} pts</p>
                <p class="text-white"><strong>Compras:</strong> {{ clienteSeleccionado.total_compras }}</p>
                <p class="text-white"><strong>Nivel:</strong> <v-chip :color="colorNivel(clienteSeleccionado.nivel)" size="x-small">{{ clienteSeleccionado.nivel }}</v-chip></p>
                <p class="text-white">
  <strong>PIN:</strong> 
  <v-chip v-if="clienteSeleccionado.pin && esAdminCentral" color="primary" size="x-small">{{ clienteSeleccionado.pin }}</v-chip>
  <span v-else-if="clienteSeleccionado.pin" style="color: rgba(255,255,255,0.3);">••••••</span>
  <span v-else style="color: rgba(255,255,255,0.3);">Sin PIN</span>
</p>
              </div>
            </v-col>
          </v-row>
          <div class="glass-effect pa-3 rounded-lg mt-2">
            <h4 class="text-white mb-2">Referencia</h4>
            <p class="text-white"><strong>Nombre:</strong> {{ clienteSeleccionado.referencia_nombre || 'N/A' }}</p>
            <p class="text-white"><strong>Teléfono:</strong> {{ clienteSeleccionado.referencia_telefono || 'N/A' }}</p>
            <p class="text-white"><strong>Parentesco:</strong> {{ clienteSeleccionado.referencia_parentesco || 'N/A' }}</p>
          </div>
          <div class="glass-effect pa-3 rounded-lg mt-2">
            <h4 class="text-white mb-2">Foto de Cédula</h4>
            <div v-if="tieneFotoReal(clienteSeleccionado)" class="text-center">
              <v-img :src="clienteSeleccionado.url_cedula" max-height="250" contain class="rounded-lg cursor-pointer" @click="verFotoAmpliada(clienteSeleccionado)" />
            </div>
            <p v-else class="text-caption" style="color: rgba(255,255,255,0.3);">No hay foto registrada</p>
          </div>
          <div class="glass-effect pa-3 rounded-lg mt-2">
            <h4 class="text-white mb-2">Financiamientos</h4>
            <v-alert v-if="!financiamientosCliente.length" type="info" variant="tonal" density="compact" class="rounded-lg">Sin financiamientos</v-alert>
            <v-expansion-panels v-else>
              <v-expansion-panel v-for="fin in financiamientosCliente" :key="fin.id" class="glass-effect mb-1 rounded-lg">
                <v-expansion-panel-title>
                  <div class="d-flex align-center w-100">
                    <v-icon :color="fin.estado === 'activo' ? 'success' : 'grey'" class="mr-2">{{ fin.estado === 'activo' ? 'mdi-clock-outline' : 'mdi-check-circle' }}</v-icon>
                    <span class="text-white flex-grow-1">{{ fin.codigo }}</span>
                    <v-chip :color="fin.estado === 'activo' ? 'warning' : 'success'" size="x-small">{{ fin.estado }}</v-chip>
                  </div>
                </v-expansion-panel-title>
                <v-expansion-panel-text>
                  <p class="text-white"><strong>Descripción:</strong> {{ fin.descripcion }}</p>
                  <p class="text-white"><strong>Total:</strong> BS {{ formatearBS(fin.monto_total_bs) }}</p>
                  <p class="text-white"><strong>Cuotas:</strong> {{ fin.cuotas_aprobadas }}</p>
                </v-expansion-panel-text>
              </v-expansion-panel>
            </v-expansion-panels>
          </div>
        </v-card-text>
        <v-card-actions class="pa-4">
          <v-btn @click="dialogDetalle = false" variant="text" color="grey">Cerrar</v-btn>
          <v-btn v-if="esAdminCentral && clienteSeleccionado.estado !== 'aprobado'" color="#4caf50" rounded="pill" @click="dialogDetalle = false; aprobarCliente(clienteSeleccionado)">Aprobar</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <v-dialog v-model="dialogEditar" max-width="500">
      <v-card class="glass-card">
        <v-card-title class="text-white pa-4">✏️ Editar Cliente</v-card-title>
        <v-card-text class="pa-4">
          <v-text-field v-model="clienteEditando.nombre" label="Nombre" variant="outlined" dark class="custom-input mb-2" />
          <v-text-field v-model="clienteEditando.telefono" label="Teléfono" variant="outlined" dark class="custom-input mb-2" />
          <v-text-field v-model="clienteEditando.email" label="Email" variant="outlined" dark class="custom-input mb-2" />
          <v-textarea v-model="clienteEditando.direccion" label="Dirección" variant="outlined" dark class="custom-input" rows="2" />
        </v-card-text>
        <v-card-actions class="pa-4">
          <v-btn @click="dialogEditar = false" variant="text" color="grey">Cancelar</v-btn>
          <v-btn color="#4facfe" rounded="pill" @click="guardarEdicion" :loading="guardando">Guardar</v-btn>
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
import { useAuthStore } from '@/stores/auth'
const auth = useAuthStore()

const tabActiva = ref('verificados')
const busquedaVerificados = ref('')
const busquedaPendientes = ref('')
const clientes = ref([])
const cargando = ref(false)
const guardando = ref(false)
const aprobando = ref(false)
const aprobandoId = ref(null)
const dialogDetalle = ref(false)
const dialogCuotas = ref(false)
const dialogEditar = ref(false)
const dialogAprobar = ref(false)
const dialogFoto = ref(false)
const clienteSeleccionado = ref(null)
const clienteEditando = ref(null)
const clienteAprobar = ref(null)
const fotoCliente = ref(null)
const financiamientosCliente = ref([])
const cuotas = ref([])
const snackbar = ref({ show: false, text: '', color: 'success' })
const pinGenerado = ref(null)

const esAdminCentral = computed(() => auth.esAdmin)

const headersVerificados = [
  { title: 'Nombre', key: 'nombre', sortable: true }, { title: 'Cédula', key: 'cedula', sortable: true },
  { title: 'Teléfono', key: 'telefono' }, { title: 'Tienda', key: 'tienda_nombre' },
  { title: 'Nivel', key: 'nivel' }, { title: 'Score', key: 'score' }, { title: 'PIN', key: 'pin' },
  { title: 'Acciones', key: 'acciones', sortable: false }
]
const headersPendientes = [
  { title: 'Nombre', key: 'nombre', sortable: true }, { title: 'Cédula', key: 'cedula', sortable: true },
  { title: 'Teléfono', key: 'telefono' }, { title: 'Tienda', key: 'tienda_nombre' },
  { title: 'Foto', key: 'foto', sortable: false }, { title: 'Registrado', key: 'creado_en' },
  { title: 'Acciones', key: 'acciones', sortable: false }
]

const clientesVerificados = computed(() => clientes.value.filter(c => c.estado === 'aprobado'))
const clientesPendientes = computed(() => clientes.value.filter(c => c.estado !== 'aprobado'))
const clientesVerificadosFiltrados = computed(() => {
  if (!busquedaVerificados.value) return clientesVerificados.value
  const q = busquedaVerificados.value.toLowerCase()
  return clientesVerificados.value.filter(c => c.nombre.toLowerCase().includes(q) || c.cedula.includes(q))
})
const clientesPendientesFiltrados = computed(() => {
  if (!busquedaPendientes.value) return clientesPendientes.value
  const q = busquedaPendientes.value.toLowerCase()
  return clientesPendientes.value.filter(c => c.nombre.toLowerCase().includes(q) || c.cedula.includes(q))
})

const tieneFotoReal = (c) => c?.url_cedula?.startsWith('http') || false
const esClienteLocal = (c) => c?._esLocal || c?.id?.toString().startsWith('local_') || false
const colorNivel = (n) => ({ nuevo: 'grey', bronce: 'brown', plata: 'blue', oro: 'amber', platino: 'purple' })[n] || 'grey'
const nivelColor2 = (n) => ({ nuevo: '#78909C', bronce: '#A1887F', plata: '#90A4AE', oro: '#FFD54F', platino: '#7E57C2' })[n] || '#78909C'
const formatearBS = (m) => m ? Number(m).toLocaleString('es-VE', { minimumFractionDigits: 2 }) : '0,00'
const formatearFecha = (f) => f ? new Date(f).toLocaleDateString('es-VE', { day: '2-digit', month: '2-digit', year: 'numeric' }) : ''
const mostrarMensaje = (t, c = 'success') => { snackbar.value = { show: true, text: t, color: c } }

const verFotoAmpliada = (c) => { if (!tieneFotoReal(c)) { mostrarMensaje('Sin foto', 'warning'); return }; fotoCliente.value = c; dialogFoto.value = true }
const descargarFoto = (c) => { if (!tieneFotoReal(c)) return; const a = document.createElement('a'); a.href = c.url_cedula; a.download = `cedula_${c.cedula}.jpg`; a.click() }

const cargarTodos = async () => {
  cargando.value = true
  try { const d = await api.get('/clientes'); clientes.value = d.clientes || d } catch (e) { mostrarMensaje('Error al cargar', 'error') }
  finally { cargando.value = false }
}

const verDetalle = async (c) => {
  if (esClienteLocal(c)) { clienteSeleccionado.value = c; dialogDetalle.value = true; return }
  try { clienteSeleccionado.value = await api.get(`/clientes/${c.id}`) } catch (e) { clienteSeleccionado.value = c }
  dialogDetalle.value = true
  try { const f = await api.get('/financiamientos'); financiamientosCliente.value = f.filter(x => x.cliente_id === c.id) } catch (e) { financiamientosCliente.value = [] }
}

const aprobarCliente = (c) => { clienteAprobar.value = c; pinGenerado.value = null; dialogAprobar.value = true }

const confirmarAprobar = async () => {
  if (!clienteAprobar.value) return
  aprobando.value = true; aprobandoId.value = clienteAprobar.value.id
  try {
    const d = await api.post('/clientes/aprobar', { cliente_id: clienteAprobar.value.id })
    if (d.success && d.cliente?.pin) pinGenerado.value = d.cliente.pin
    mostrarMensaje(`✅ ${clienteAprobar.value.nombre} aprobado`, 'success')
    await cargarTodos(); tabActiva.value = 'verificados'
  } catch (e) { mostrarMensaje(e.message || 'Error', 'error') }
  finally { aprobando.value = false; aprobandoId.value = null }
}

const editarCliente = (c) => { clienteEditando.value = { ...c }; dialogEditar.value = true }
const guardarEdicion = async () => {
  guardando.value = true
  try { await api.put(`/clientes/${clienteEditando.value.id}`, { nombre: clienteEditando.value.nombre, telefono: clienteEditando.value.telefono, email: clienteEditando.value.email || '', direccion: clienteEditando.value.direccion || '' }); mostrarMensaje('Actualizado'); dialogEditar.value = false; await cargarTodos() }
  catch (e) { mostrarMensaje('Error', 'error') }
  finally { guardando.value = false }
}
const eliminarCliente = async (c) => {
  if (!confirm(`¿Eliminar a ${c.nombre}?`)) return
  try { await api.delete(`/clientes/${c.id}`); mostrarMensaje('Eliminado'); await cargarTodos() } catch (e) { mostrarMensaje('Error', 'error') }
}

onMounted(() => { cargarTodos() })
</script>

<style scoped>
.background-gradient {
  position: fixed; top: 0; left: 0; right: 0; bottom: 0;
  background: radial-gradient(ellipse at 20% 50%, rgba(79,172,254,0.12), transparent 70%),
              radial-gradient(ellipse at 80% 50%, rgba(99,102,241,0.08), transparent 70%), #0a0e1a;
  z-index: 0;
}
.header-premium {
  position: relative; z-index: 1; padding: 16px 24px;
  background: rgba(255,255,255,0.05); backdrop-filter: blur(20px);
  border-radius: 20px; border: 1px solid rgba(255,255,255,0.06);
}
.icon-wrapper {
  width: 48px; height: 48px; background: linear-gradient(135deg, #4facfe, #6366f1);
  border-radius: 14px; display: flex; align-items: center; justify-content: center;
}
.pulse-animation { animation: pulse 2s infinite; }
@keyframes pulse { 0%, 100% { transform: scale(1); } 50% { transform: scale(1.05); } }
.step-chip { background: rgba(255,255,255,0.08) !important; padding: 8px 16px !important; border-radius: 50px !important; }
.glass-effect { background: rgba(255,255,255,0.05) !important; backdrop-filter: blur(16px) !important; border: 1px solid rgba(255,255,255,0.08) !important; border-radius: 12px !important; }
.glass-card { background: rgba(255,255,255,0.03) !important; backdrop-filter: blur(24px) !important; border: 1px solid rgba(255,255,255,0.06) !important; border-radius: 24px !important; }
.premium-tabs :deep(.v-tab) { color: rgba(255,255,255,0.5) !important; }
.premium-tabs :deep(.v-tab--selected) { color: #4facfe !important; }
.premium-table { background: transparent !important; }
.premium-table :deep(th) { color: rgba(255,255,255,0.7) !important; font-weight: 700 !important; }
.premium-table :deep(td) { color: rgba(255,255,255,0.9) !important; border-bottom: 1px solid rgba(255,255,255,0.04) !important; }
.premium-table :deep(tr:hover) { background: rgba(255,255,255,0.03) !important; }
.level-dot { width: 8px; height: 8px; border-radius: 50%; margin-right: 8px; }
.custom-input :deep(.v-field) { background: rgba(255,255,255,0.05) !important; border-radius: 12px !important; border: 1px solid rgba(255,255,255,0.08) !important; }
.custom-input :deep(.v-field--focused) { border-color: #4facfe !important; }
.custom-input :deep(.v-label) { color: rgba(255,255,255,0.5) !important; }
.custom-input :deep(.v-field__input) { color: white !important; }
.cursor-pointer { cursor: pointer; }
.gap-1 { gap: 4px; }
.gap-2 { gap: 8px; }
.fade-in { animation: fadeIn 0.5s ease; }
@keyframes fadeIn { from { opacity: 0; transform: translateY(20px); } to { opacity: 1; transform: translateY(0); } }
@media (max-width: 600px) { .header-premium { flex-direction: column; gap: 12px; align-items: stretch !important; } }
</style>