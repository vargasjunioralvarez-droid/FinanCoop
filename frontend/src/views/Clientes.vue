<template>
  <v-container>
    <v-row>
      <v-col cols="12">
        <h1 class="text-h4 mb-4">👥 Gestión de Clientes</h1>
      </v-col>

      <!-- Tabs -->
      <v-col cols="12">
        <v-tabs v-model="tabActiva" color="primary" grow>
          <v-tab value="verificados">
            <v-icon start>mdi-check-circle</v-icon>
            Verificados ({{ clientesVerificados.length }})
          </v-tab>
          <v-tab value="pendientes">
            <v-icon start>mdi-clock-outline</v-icon>
            Por Verificar ({{ clientesPendientes.length }})
          </v-tab>
        </v-tabs>

        <v-window v-model="tabActiva" class="mt-4">
          
          <!-- PESTAÑA: CLIENTES VERIFICADOS -->
          <v-window-item value="verificados">
            <v-card>
              <v-card-title class="d-flex align-center">
                <v-icon color="success" class="mr-2">mdi-check-circle</v-icon>
                Clientes Verificados
                <v-spacer></v-spacer>
                <v-text-field
                  v-model="busquedaVerificados"
                  label="Buscar..."
                  prepend-inner-icon="mdi-magnify"
                  density="compact"
                  hide-details
                  variant="outlined"
                  style="max-width: 300px;"
                ></v-text-field>
              </v-card-title>
              
              <v-data-table
                :items="clientesVerificadosFiltrados"
                :headers="headersVerificados"
                :items-per-page="10"
              >
                <template v-slot:item.estado="{ item }">
                  <v-chip color="success" size="small">✅ Aprobado</v-chip>
                </template>

                <template v-slot:item.pin="{ item }">
                  <v-chip color="primary" size="small" v-if="item.pin">{{ item.pin }}</v-chip>
                  <span v-else class="text-grey">Sin PIN</span>
                </template>

                <template v-slot:item.nivel="{ item }">
                  <v-chip :color="colorNivel(item.nivel)" size="small">{{ item.nivel }}</v-chip>
                </template>

                <template v-slot:item.acciones="{ item }">
                  <div class="d-flex gap-1">
                    <v-btn icon="mdi-eye" size="small" color="info" @click="verDetalle(item)"></v-btn>
                    <v-btn v-if="esAdminCentral" icon="mdi-pencil" size="small" color="primary" @click="editarCliente(item)"></v-btn>
                    <v-btn v-if="esAdminCentral" icon="mdi-delete" size="small" color="error" @click="eliminarCliente(item)"></v-btn>
                  </div>
                </template>
              </v-data-table>
            </v-card>
          </v-window-item>

          <!-- PESTAÑA: CLIENTES POR VERIFICAR -->
          <v-window-item value="pendientes">
            <v-card>
              <v-card-title class="d-flex align-center">
                <v-icon color="warning" class="mr-2">mdi-clock-outline</v-icon>
                Clientes por Verificar
                <v-spacer></v-spacer>
                <v-text-field
                  v-model="busquedaPendientes"
                  label="Buscar..."
                  prepend-inner-icon="mdi-magnify"
                  density="compact"
                  hide-details
                  variant="outlined"
                  style="max-width: 300px;"
                ></v-text-field>
              </v-card-title>

              <v-data-table
                :items="clientesPendientesFiltrados"
                :headers="headersPendientes"
                :items-per-page="10"
              >
                <template v-slot:item.estado="{ item }">
                  <v-chip color="warning" size="small">⏳ Pendiente</v-chip>
                </template>

                <template v-slot:item.foto="{ item }">
                  <div class="d-flex align-center">
                    <v-avatar v-if="tieneFotoReal(item)" size="40" class="mr-2 cursor-pointer" @click="verFotoAmpliada(item)">
                      <v-img :src="item.url_cedula" cover>
                        <template v-slot:placeholder><v-icon color="grey">mdi-image</v-icon></template>
                      </v-img>
                    </v-avatar>
                    <v-icon v-else :color="item.url_cedula ? 'success' : 'grey'" size="24" class="mr-2">
                      {{ item.url_cedula ? 'mdi-check-circle' : 'mdi-image-off' }}
                    </v-icon>
                    <v-btn v-if="tieneFotoReal(item)" icon="mdi-magnify" size="x-small" color="primary" variant="text" @click="verFotoAmpliada(item)" title="Ver foto"></v-btn>
                    <span v-else class="text-caption text-grey">{{ item.url_cedula ? 'Sí (sin URL)' : 'No' }}</span>
                  </div>
                </template>

                <template v-slot:item.acciones="{ item }">
                  <div class="d-flex gap-1">
                    <v-btn icon="mdi-eye" size="small" color="info" @click="verDetalle(item)"></v-btn>
                    <v-btn v-if="esAdminCentral" icon="mdi-check-circle" size="small" color="success" @click="aprobarCliente(item)" :loading="aprobandoId === item.id" title="Aprobar y enviar PIN"></v-btn>
                    <v-btn v-if="esAdminCentral" icon="mdi-delete" size="small" color="error" @click="eliminarCliente(item)"></v-btn>
                  </div>
                </template>
              </v-data-table>

              <v-alert v-if="clientesPendientes.length === 0" type="info" class="ma-4">
                🎉 No hay clientes pendientes por verificar.
              </v-alert>
            </v-card>
          </v-window-item>

        </v-window>
      </v-col>
    </v-row>

    <!-- DIALOG: Ver Foto Ampliada -->
    <v-dialog v-model="dialogFoto" max-width="800">
      <v-card v-if="fotoCliente">
        <v-card-title class="d-flex align-center">
          <v-icon class="mr-2">mdi-card-account-details</v-icon>
          Foto de Cédula - {{ fotoCliente.nombre }}
          <v-spacer></v-spacer>
          <v-btn icon="mdi-close" variant="text" @click="dialogFoto = false"></v-btn>
        </v-card-title>
        <v-card-text class="text-center pa-4">
          <v-img :src="fotoCliente.url_cedula" max-height="70vh" contain class="rounded-lg elevation-2 bg-grey-darken-3">
            <template v-slot:placeholder>
              <v-row align="center" justify="center" class="fill-height"><v-progress-circular indeterminate color="primary"></v-progress-circular></v-row>
            </template>
          </v-img>
          <div class="mt-4 d-flex justify-center gap-2">
            <v-btn :href="fotoCliente.url_cedula" target="_blank" color="primary" prepend-icon="mdi-open-in-new">Abrir en nueva pestaña</v-btn>
            <v-btn color="secondary" prepend-icon="mdi-download" @click="descargarFoto(fotoCliente)">Descargar</v-btn>
          </div>
        </v-card-text>
      </v-card>
    </v-dialog>

    <!-- DIALOG: Aprobar Cliente -->
    <v-dialog v-model="dialogAprobar" max-width="450">
      <v-card>
        <v-card-title class="text-h5 bg-success text-white">
          <v-icon start>mdi-check-circle</v-icon>Aprobar Cliente
        </v-card-title>
        <v-card-text class="pt-4" v-if="clienteAprobar">
          <p class="text-body-1">¿Aprobar a <strong>{{ clienteAprobar.nombre }}</strong>?</p>
          <div v-if="tieneFotoReal(clienteAprobar)" class="mt-3 text-center">
            <p class="text-caption text-grey mb-2">Foto de cédula:</p>
            <v-img :src="clienteAprobar.url_cedula" max-height="150" contain class="rounded" @click="verFotoAmpliada(clienteAprobar)"></v-img>
          </div>
          <v-list density="compact" class="bg-grey-lighten-4 rounded mt-2">
            <v-list-item><v-list-item-title>Cédula</v-list-item-title><v-list-item-subtitle>{{ clienteAprobar.cedula }}</v-list-item-subtitle></v-list-item>
            <v-list-item><v-list-item-title>Teléfono</v-list-item-title><v-list-item-subtitle>{{ clienteAprobar.telefono }}</v-list-item-subtitle></v-list-item>
          </v-list>
          <p class="text-caption text-grey mt-3">Se enviará un SMS/WhatsApp con el PIN de acceso al número registrado.</p>
        </v-card-text>
        <v-card-actions>
          <v-spacer></v-spacer>
          <v-btn @click="dialogAprobar = false">Cancelar</v-btn>
          <v-btn color="success" @click="confirmarAprobar" :loading="aprobando">
            <v-icon start>mdi-send</v-icon>Aprobar y Enviar PIN
          </v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <!-- DIALOG: Detalle del Cliente -->
    <v-dialog v-model="dialogDetalle" max-width="700">
      <v-card v-if="clienteSeleccionado">
        <v-card-title class="text-h5">
          {{ clienteSeleccionado.nombre }}
          <v-chip :color="clienteSeleccionado.estado === 'aprobado' ? 'success' : 'warning'" class="ml-2">
            {{ clienteSeleccionado.estado === 'aprobado' ? '✅ Aprobado' : '⏳ Pendiente' }}
          </v-chip>
        </v-card-title>
        <v-card-text>
          <v-row>
            <v-col cols="12" md="6">
              <p><strong>Cédula:</strong> {{ clienteSeleccionado.cedula }}</p>
              <p><strong>Teléfono:</strong> {{ clienteSeleccionado.telefono }}</p>
              <p><strong>Email:</strong> {{ clienteSeleccionado.email || 'N/A' }}</p>
              <p><strong>Dirección:</strong> {{ clienteSeleccionado.direccion || 'N/A' }}</p>
            </v-col>
            <v-col cols="12" md="6">
              <p><strong>Score:</strong> {{ clienteSeleccionado.score }} pts</p>
              <p><strong>Total Compras:</strong> {{ clienteSeleccionado.total_compras }}</p>
              <p><strong>Nivel:</strong> <v-chip :color="colorNivel(clienteSeleccionado.nivel)" size="small">{{ clienteSeleccionado.nivel }}</v-chip></p>
              <p><strong>PIN:</strong> <v-chip color="primary" size="small" v-if="clienteSeleccionado.pin">{{ clienteSeleccionado.pin }}</v-chip><span v-else class="text-grey">Sin PIN</span></p>
            </v-col>
          </v-row>
          <v-divider class="my-3"></v-divider>
          <h3 class="text-h6 mb-2">Referencia</h3>
          <p><strong>Nombre:</strong> {{ clienteSeleccionado.referencia_nombre || 'N/A' }}</p>
          <p><strong>Teléfono:</strong> {{ clienteSeleccionado.referencia_telefono || 'N/A' }}</p>
          <p><strong>Parentesco:</strong> {{ clienteSeleccionado.referencia_parentesco || 'N/A' }}</p>
          <v-divider class="my-3"></v-divider>
          <h3 class="text-h6 mb-2">Foto de Cédula</h3>
          <div v-if="tieneFotoReal(clienteSeleccionado)" class="text-center">
            <v-img :src="clienteSeleccionado.url_cedula" max-height="250" contain class="rounded-lg elevation-2 cursor-pointer bg-grey-darken-3" @click="verFotoAmpliada(clienteSeleccionado)">
              <template v-slot:placeholder><v-row align="center" justify="center" class="fill-height"><v-progress-circular indeterminate color="primary"></v-progress-circular></v-row></template>
            </v-img>
            <div class="mt-2">
              <v-btn color="primary" size="small" prepend-icon="mdi-magnify" @click="verFotoAmpliada(clienteSeleccionado)" class="mr-2">Ver ampliada</v-btn>
              <v-btn :href="clienteSeleccionado.url_cedula" target="_blank" color="secondary" size="small" prepend-icon="mdi-open-in-new">Abrir original</v-btn>
            </div>
          </div>
          <div v-else-if="esClienteLocal(clienteSeleccionado)" class="text-center py-4 bg-grey-lighten-4 rounded">
            <v-icon size="48" color="grey">mdi-image-off</v-icon>
            <p class="text-body-2 text-grey mt-2">Cliente registrado localmente</p>
            <p class="text-caption text-grey">La foto no está disponible en el servidor</p>
          </div>
          <v-alert v-else type="warning" density="compact" class="mt-2"><v-icon start>mdi-image-off</v-icon>No hay foto de cédula registrada</v-alert>
          <v-divider class="my-3"></v-divider>
          <h3 class="text-h6 mb-2">Financiamientos</h3>
          <v-alert v-if="!financiamientosCliente.length" type="info" density="compact">Sin financiamientos</v-alert>
          <v-expansion-panels v-else>
            <v-expansion-panel v-for="fin in financiamientosCliente" :key="fin.id">
              <v-expansion-panel-title>
                <div class="d-flex align-center w-100">
                  <v-icon :color="fin.estado === 'activo' ? 'success' : 'grey'" class="mr-2">{{ fin.estado === 'activo' ? 'mdi-clock-outline' : 'mdi-check-circle' }}</v-icon>
                  <span class="flex-grow-1">{{ fin.codigo }}</span>
                  <v-chip :color="fin.estado === 'activo' ? 'warning' : 'success'" size="small">{{ fin.estado }}</v-chip>
                </div>
              </v-expansion-panel-title>
              <v-expansion-panel-text>
                <p><strong>Descripción:</strong> {{ fin.descripcion }}</p>
                <p><strong>Total:</strong> BS {{ formatearBS(fin.monto_total_bs) }}</p>
                <p><strong>Entrada:</strong> BS {{ formatearBS(fin.monto_entrada_bs) }}</p>
                <p><strong>Cuotas:</strong> {{ fin.cuotas_aprobadas }}</p>
                <p><strong>Cuota mensual:</strong> BS {{ formatearBS(fin.monto_cuota_bs) }}</p>
                <v-btn color="primary" size="small" class="mt-2" @click="verCuotas(fin.id)">Ver Cuotas</v-btn>
              </v-expansion-panel-text>
            </v-expansion-panel>
          </v-expansion-panels>
        </v-card-text>
        <v-card-actions>
          <v-btn @click="dialogDetalle = false">Cerrar</v-btn>
          <v-btn v-if="esAdminCentral && clienteSeleccionado.estado !== 'aprobado'" color="success" @click="dialogDetalle = false; aprobarCliente(clienteSeleccionado)">Aprobar</v-btn>
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

    <!-- Dialog: Cuotas -->
    <v-dialog v-model="dialogCuotas" max-width="500">
      <v-card>
        <v-card-title><v-btn icon @click="dialogCuotas = false" class="mr-2"><v-icon>mdi-arrow-left</v-icon></v-btn>Cuotas</v-card-title>
        <v-card-text>
          <v-list>
            <v-list-item v-for="c in cuotas" :key="c.id" :class="{ 'bg-success-lighten-4': c.estado === 'pagada', 'bg-error-lighten-4': c.dias_atraso > 0 }" class="mb-2 rounded">
              <v-list-item-title><v-icon :color="c.estado === 'pagada' ? 'success' : 'error'" class="mr-2">{{ c.estado === 'pagada' ? 'mdi-check-circle' : 'mdi-alert-circle' }}</v-icon>Cuota #{{ c.numero }}</v-list-item-title>
              <v-list-item-subtitle><v-chip :color="c.estado === 'pagada' ? 'success' : 'warning'" size="small">{{ c.estado }}</v-chip></v-list-item-subtitle>
              <template v-slot:append><div class="text-right"><div class="text-h6">BS {{ formatearBS(c.monto_total_bs) }}</div><div class="text-caption">{{ formatearFecha(c.fecha_vencimiento) }}</div></div></template>
            </v-list-item>
          </v-list>
        </v-card-text>
      </v-card>
    </v-dialog>

    <!-- Snackbar -->
    <v-snackbar v-model="snackbar.show" :color="snackbar.color" timeout="5000" multi-line>
      {{ snackbar.text }}
      <template v-slot:actions><v-btn variant="text" @click="snackbar.show = false">Cerrar</v-btn></template>
    </v-snackbar>

  </v-container>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { api } from '@/config/api'

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

// ✅ Solo admin_central puede aprobar/editar/eliminar
const esAdminCentral = computed(() => localStorage.getItem('admin_rol') === 'admin_central')

const headersVerificados = [
  { title: 'Nombre', key: 'nombre', sortable: true },
  { title: 'Cédula', key: 'cedula', sortable: true },
  { title: 'Teléfono', key: 'telefono' },
  { title: 'Tienda', key: 'tienda_nombre' },
  { title: 'Nivel', key: 'nivel' },
  { title: 'Score', key: 'score' },
  { title: 'PIN', key: 'pin' },
  { title: 'Acciones', key: 'acciones', sortable: false }
]

const headersPendientes = [
  { title: 'Nombre', key: 'nombre', sortable: true },
  { title: 'Cédula', key: 'cedula', sortable: true },
  { title: 'Teléfono', key: 'telefono' },
  { title: 'Tienda', key: 'tienda_nombre' },
  { title: 'Foto', key: 'foto', sortable: false },
  { title: 'Registrado', key: 'creado_en' },
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

const tieneFotoReal = (cliente) => cliente?.url_cedula?.startsWith('http') || false
const esClienteLocal = (cliente) => cliente?._esLocal || cliente?.id?.toString().startsWith('local_') || false

const verFotoAmpliada = (cliente) => {
  if (!tieneFotoReal(cliente)) { mostrarMensaje('Este cliente no tiene foto disponible', 'warning'); return }
  fotoCliente.value = cliente; dialogFoto.value = true
}

const descargarFoto = (cliente) => {
  if (!tieneFotoReal(cliente)) return
  const link = document.createElement('a'); link.href = cliente.url_cedula
  link.download = `cedula_${cliente.cedula}.jpg`; link.target = '_blank'
  document.body.appendChild(link); link.click(); document.body.removeChild(link)
}

const colorNivel = (nivel) => ({ nuevo: 'grey', bronce: 'brown', plata: 'blue', oro: 'amber', platino: 'purple' })[nivel] || 'grey'
const formatearBS = (monto) => monto ? Number(monto).toLocaleString('es-VE', { minimumFractionDigits: 2, maximumFractionDigits: 2 }) : '0,00'
const formatearFecha = (fechaStr) => fechaStr ? new Date(fechaStr).toLocaleDateString('es-VE', { day: '2-digit', month: '2-digit', year: 'numeric' }) : ''
const mostrarMensaje = (texto, color = 'success') => { snackbar.value = { show: true, text: texto, color } }

const cargarSolicitudesLocales = () => {
  const solicitudesStr = localStorage.getItem('solicitudes_clientes')
  if (!solicitudesStr) return
  try {
    const solicitudes = JSON.parse(solicitudesStr)
    if (!solicitudes.length) return
    const nuevosClientes = solicitudes.map((sol, index) => ({
      id: `local_${Date.now()}_${index}`, nombre: sol.nombre || 'Sin nombre', cedula: sol.cedula || '000000',
      telefono: sol.telefono || '', email: sol.email || '', direccion: sol.direccion || '',
      referencia_nombre: sol.referencia_nombre || '', referencia_telefono: sol.referencia_telefono || '',
      referencia_parentesco: sol.referencia_parentesco || '', estado: 'pendiente',
      url_cedula: sol.url_cedula || (sol.tiene_foto ? '📷 Sí' : null),
      creado_en: sol.fecha_solicitud ? new Date(sol.fecha_solicitud).toLocaleDateString('es-VE') : 'Hoy',
      score: 0, total_compras: 0, nivel: 'nuevo', pin: null, _esLocal: true
    }))
    const cedulasExistentes = new Set(clientes.value.map(c => c.cedula))
    const filtrados = nuevosClientes.filter(c => !cedulasExistentes.has(c.cedula))
    if (filtrados.length) clientes.value = [...clientes.value, ...filtrados]
  } catch (e) {}
}

const cargarTodos = async () => {
  cargando.value = true
  try {
    const data = await api.get('/clientes')
    clientes.value = data.clientes || data
    cargarSolicitudesLocales()
  } catch (e) { mostrarMensaje('Error al cargar clientes', 'error') }
  finally { cargando.value = false }
}

const verDetalle = async (cliente) => {
  if (esClienteLocal(cliente)) { clienteSeleccionado.value = cliente; dialogDetalle.value = true; financiamientosCliente.value = []; return }
  try { clienteSeleccionado.value = await api.get(`/clientes/${cliente.id}`) } catch (e) { clienteSeleccionado.value = cliente }
  dialogDetalle.value = true
  try { const fins = await api.get('/financiamientos'); financiamientosCliente.value = fins.filter(f => f.cliente_id === cliente.id) } catch (e) { financiamientosCliente.value = [] }
}

const verCuotas = async (finId) => {
  try { cuotas.value = await api.get(`/financiamientos/${finId}/cuotas`); dialogCuotas.value = true } catch (e) {}
}

const aprobarCliente = (cliente) => { clienteAprobar.value = cliente; dialogAprobar.value = true }

const confirmarAprobar = async () => {
  if (!clienteAprobar.value) return
  aprobando.value = true; aprobandoId.value = clienteAprobar.value.id
  try {
    const token = localStorage.getItem('admin_token')
    const esLocal = esClienteLocal(clienteAprobar.value)
    
    if (esLocal) {
      mostrarMensaje('📝 Creando cliente...', 'info')
      const r = await fetch('https://financoop.onrender.com/api/v1/clientes', {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ nombre: clienteAprobar.value.nombre, cedula: clienteAprobar.value.cedula, telefono: clienteAprobar.value.telefono, email: clienteAprobar.value.email || '', direccion: clienteAprobar.value.direccion || '', referencia_nombre: clienteAprobar.value.referencia_nombre || '', referencia_telefono: clienteAprobar.value.referencia_telefono || '', referencia_parentesco: clienteAprobar.value.referencia_parentesco || '' })
      })
      const d = await r.json()
      if (!r.ok || !d.success) throw new Error(d.error || 'Error al crear')
      localStorage.setItem('solicitudes_clientes', JSON.stringify(JSON.parse(localStorage.getItem('solicitudes_clientes') || '[]').filter(s => s.cedula !== clienteAprobar.value.cedula)))
      mostrarMensaje(`✅ ${clienteAprobar.value.nombre} creado`, 'success')
      if (d.id) {
        const ar = await fetch('https://financoop.onrender.com/api/v1/clientes/aprobar', {
          method: 'POST', headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${token}` },
          body: JSON.stringify({ cliente_id: d.id })
        })
        const ad = await ar.json()
        if (ad.success) mostrarMensaje(`✅ ${clienteAprobar.value.nombre} aprobado. PIN enviado.`, 'success')
        else throw new Error(ad.error || 'Error al aprobar')
      }
    } else {
      const r = await fetch('https://financoop.onrender.com/api/v1/clientes/aprobar', {
        method: 'POST', headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${token}` },
        body: JSON.stringify({ cliente_id: clienteAprobar.value.id })
      })
      const d = await r.json()
      if (!d.success) throw new Error(d.error || 'Error al aprobar')
      mostrarMensaje(`✅ ${clienteAprobar.value.nombre} aprobado`, 'success')
    }
    await cargarTodos(); tabActiva.value = 'verificados'
  } catch (e) { mostrarMensaje(e.message || 'Error', 'error') }
  finally { aprobando.value = false; aprobandoId.value = null; dialogAprobar.value = false }
}

const editarCliente = (cliente) => { clienteEditando.value = { ...cliente }; dialogEditar.value = true }

const guardarEdicion = async () => {
  guardando.value = true
  try {
    await api.put(`/clientes/${clienteEditando.value.id}`, { nombre: clienteEditando.value.nombre, telefono: clienteEditando.value.telefono, email: clienteEditando.value.email || '', direccion: clienteEditando.value.direccion || '' })
    mostrarMensaje('Cliente actualizado'); dialogEditar.value = false; await cargarTodos()
  } catch (e) { mostrarMensaje('Error al actualizar', 'error') }
  finally { guardando.value = false }
}

const eliminarCliente = async (cliente) => {
  if (!confirm(`¿Eliminar a ${cliente.nombre}?`)) return
  try { await api.delete(`/clientes/${cliente.id}`); mostrarMensaje('Cliente eliminado'); await cargarTodos() }
  catch (e) { mostrarMensaje('Error al eliminar', 'error') }
}

onMounted(() => { cargarTodos() })
</script>

<style scoped>
.cursor-pointer { cursor: pointer; }
.gap-1 { gap: 4px; }
.gap-2 { gap: 8px; }
</style>