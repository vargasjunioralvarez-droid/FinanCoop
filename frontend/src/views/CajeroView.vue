<template>
  <v-container v-if="esAdminCentral">
    <v-row>
      <v-col cols="12">
        <h1 class="text-h4 mb-4">🛒 Nueva Venta - Financiamiento</h1>
        <v-chip color="info" class="mb-2">
          Tasa referencia: {{ tasaDolar }} BS/$
        </v-chip>
      </v-col>
      
      <!-- PASO 1: Cliente -->
      <v-col cols="12" v-if="paso === 1">
        <v-card>
          <v-card-title class="text-h5">1. Identificar Cliente</v-card-title>
          <v-card-text>
            <v-text-field
              v-model="busquedaCedula"
              label="Cédula del Cliente"
              @keyup.enter="buscarCliente"
              append-inner-icon="mdi-magnify"
              @click:append-inner="buscarCliente"
              variant="outlined"
              density="comfortable"
            ></v-text-field>
            
            <v-alert v-if="clienteEncontrado" type="success" class="mt-3" border="start">
              <div>
                <strong class="text-h6">{{ clienteEncontrado.nombre }}</strong><br>
                <v-chip :color="colorNivel(clienteEncontrado.nivel)" class="mt-1">
                  {{ clienteEncontrado.nivel.toUpperCase() }}
                </v-chip>
                <span class="ml-2">Score: {{ clienteEncontrado.score }} pts</span><br>
                
                <div class="text-caption mt-2">
                  <v-icon size="small">mdi-phone</v-icon> {{ clienteEncontrado.telefono }}<br>
                  <v-icon size="small" v-if="clienteEncontrado.direccion">mdi-map-marker</v-icon> 
                  {{ clienteEncontrado.direccion }}<br>
                  <v-icon size="small" v-if="clienteEncontrado.referencia_nombre">mdi-account-check</v-icon>
                  Ref: {{ clienteEncontrado.referencia_nombre }} ({{ clienteEncontrado.referencia_parentesco }}) - {{ clienteEncontrado.referencia_telefono }}
                </div>
                
                <span v-if="clienteEncontrado.nivel_config" class="text-caption">
                  Límite: ${{ clienteEncontrado.nivel_config.monto_max_usd }} USD 
                  (BS {{ formatearNumero(clienteEncontrado.nivel_config.monto_max_bs) }}) | 
                  Entrada: {{ clienteEncontrado.nivel_config.entrada_pct }}% | 
                  Cuotas: {{ clienteEncontrado.nivel_config.cuotas_base }}-{{ clienteEncontrado.nivel_config.cuotas_max }}
                </span>
              </div>
            </v-alert>
            
            <v-alert v-if="clienteNoEncontrado" type="warning" class="mt-3" border="start">
              <p class="mb-2 font-weight-bold">Cliente no encontrado. Registre nuevo cliente:</p>
              
              <v-text-field v-model="nuevoCliente.nombre" label="Nombre completo *" variant="outlined" density="comfortable" required />
              <v-text-field v-model="nuevoCliente.telefono" label="Teléfono *" variant="outlined" density="comfortable" required />
              <v-text-field v-model="nuevoCliente.email" label="Email *" variant="outlined" density="comfortable" required />
              
              <v-textarea v-model="nuevoCliente.direccion" label="Dirección completa *" rows="2" placeholder="Calle, casa, urbanización, ciudad..." variant="outlined" density="comfortable" required />
              
              <v-divider class="my-3"></v-divider>
              <p class="text-subtitle-2 mb-2 font-weight-bold">Referencia personal (obligatorio):</p>
              
              <v-text-field v-model="nuevoCliente.referencia_nombre" label="Nombre de referencia *" variant="outlined" density="comfortable" required />
              <v-text-field v-model="nuevoCliente.referencia_telefono" label="Teléfono de referencia *" variant="outlined" density="comfortable" required />
              <v-select v-model="nuevoCliente.referencia_parentesco" :items="['Vecino', 'Familiar', 'Jefe de trabajo', 'Amigo', 'Otro']" label="Parentesco/Relación *" variant="outlined" density="comfortable" required />
              
              <v-btn color="primary" @click="registrarCliente" block size="large" :disabled="!registroValido">
                <v-icon start>mdi-account-plus</v-icon>Registrar Cliente
              </v-btn>
            </v-alert>
            
            <v-btn v-if="clienteEncontrado && !clienteEncontrado.bloqueado" color="primary" @click="paso = 2" class="mt-3" block size="large">
              Continuar →
            </v-btn>
          </v-card-text>
        </v-card>
      </v-col>
      
      <!-- PASO 2: Monto en BS -->
      <v-col cols="12" v-if="paso === 2">
        <v-card>
          <v-card-title class="text-h5">2. Monto de la Compra (BS)</v-card-title>
          <v-card-text>
            <v-text-field v-model="montoTotalBS" label="Monto Total en Bolívares" type="number" prefix="BS" @input="calcularPropuesta" variant="outlined" density="comfortable" hint="Ingrese el monto en Bolívares" persistent-hint />
            
            <div class="text-caption mb-2" v-if="tasaDolar && montoTotalBS">
              <v-icon color="info" size="small">mdi-information</v-icon>
              Equivalente: ~${{ (parseFloat(montoTotalBS) / tasaDolar).toFixed(2) }} USD (referencia)
            </div>
            
            <v-alert v-if="propuesta" type="info" class="mt-3" border="start">
              <h3 class="text-h6 mb-2">Propuesta para {{ clienteEncontrado?.nombre }}</h3>
              <v-divider class="my-2"></v-divider>
              
              <div class="d-flex justify-space-between mb-1"><span>Monto Total:</span><strong>BS {{ formatearNumero(propuesta.propuesta?.monto_solicitado_bs || propuesta.monto_total_bs) }}</strong></div>
              <div class="d-flex justify-space-between mb-1 text-grey"><span>Monto en USD:</span><strong>${{ formatearNumero(propuesta.propuesta?.monto_solicitado_usd || propuesta.monto_total_usd) }}</strong></div>
              <div class="d-flex justify-space-between mb-1 text-error"><span>Entrada a pagar HOY ({{ propuesta.propuesta?.entrada_pct || propuesta.entrada_pct }}%):</span><strong>BS {{ formatearNumero(propuesta.propuesta?.entrada_bs || propuesta.monto_entrada_bs) }}</strong></div>
              <div class="d-flex justify-space-between mb-1 text-success"><span>A financiar ({{ propuesta.propuesta?.financia_pct || propuesta.financia_pct }}%):</span><strong>BS {{ formatearNumero(propuesta.propuesta?.financia_bs || propuesta.monto_financia_bs) }}</strong></div>
              <div class="d-flex justify-space-between mb-1"><span>Límite disponible:</span><strong>BS {{ formatearNumero(propuesta.propuesta?.disponible_bs || propuesta.disponible_bs) }}</strong></div>
              
              <div v-if="propuesta.propuesta?.excede_limite || propuesta.excede_limite" class="text-error mt-2">
                <v-icon color="error">mdi-alert</v-icon>⚠️ El monto excede el límite máximo permitido
              </div>
              
              <div class="text-caption mt-2">Tasa: {{ propuesta.tasa_dolar_actual || propuesta.tasa_aplicada || tasaDolar }} BS/$</div>
            </v-alert>
            
            <div v-if="propuesta" class="mt-3">
              <label class="text-subtitle-2 font-weight-bold">Seleccionar cuotas:</label>
              <v-radio-group v-model="cuotasSeleccionadas" class="mt-2">
                <v-radio v-for="cuota in opcionesCuotas" :key="cuota.value" :value="cuota.value">
                  <template v-slot:label>
                    <div><strong>{{ cuota.value }} cuotas</strong><span class="text-caption ml-2">BS {{ formatearNumero(cuota.monto) }} cada una<span class="text-grey">(${{ formatearNumero(cuota.monto_usd) }} ref.)</span></span></div>
                  </template>
                </v-radio>
              </v-radio-group>
              
              <v-alert v-if="requiereAprobacion" type="warning" class="mt-2" border="start">
                ⚠️ Requiere aprobación del establecimiento para {{ cuotasSeleccionadas }} cuotas
              </v-alert>
            </div>
            
            <v-btn v-if="cuotasSeleccionadas" color="success" @click="paso = 3" class="mt-3" block size="large">Confirmar Propuesta →</v-btn>
            <v-btn @click="paso = 1" class="mt-2" block variant="text">← Volver</v-btn>
          </v-card-text>
        </v-card>
      </v-col>
      
      <!-- PASO 3: Confirmar -->
      <v-col cols="12" v-if="paso === 3">
        <v-card>
          <v-card-title class="text-h5">3. Confirmar Venta</v-card-title>
          <v-card-text>
            <v-alert type="warning" class="mb-3" border="start">
              <h3 class="text-h6 mb-2">Resumen de la Venta</h3>
              <p><strong>Cliente:</strong> {{ clienteEncontrado?.nombre }}</p>
              <p><strong>Teléfono:</strong> {{ clienteEncontrado?.telefono }}</p>
              <p><strong>Dirección:</strong> {{ clienteEncontrado?.direccion }}</p>
              <p><strong>Producto/Servicio:</strong> {{ descripcion || 'Sin descripción' }}</p>
              <p><strong>Monto Total:</strong> BS {{ formatearNumero(montoTotalBS) }}</p>
              <p class="text-error"><strong>Entrada a cobrar HOY:</strong> BS {{ formatearNumero(propuesta?.propuesta?.entrada_bs || propuesta?.monto_entrada_bs) }}</p>
              <p class="text-success"><strong>Financia:</strong> BS {{ formatearNumero(propuesta?.propuesta?.financia_bs || propuesta?.monto_financia_bs) }}</p>
              <p><strong>Cuotas:</strong> {{ cuotasSeleccionadas }} quincenales</p>
              <p><strong>Monto cuota:</strong> BS {{ formatearNumero(montoCuotaSeleccionada) }}</p>
            </v-alert>
            
            <v-text-field v-model="descripcion" label="Descripción de la compra" placeholder="Ej: iPhone 15, Consulta Dental, etc." variant="outlined" density="comfortable" />
            
            <v-btn color="success" @click="crearFinanciamiento" block size="large">✅ Cobrar Entrada y Crear Financiamiento</v-btn>
            <v-btn @click="paso = 2" class="mt-2" block variant="text">← Volver</v-btn>
          </v-card-text>
        </v-card>
      </v-col>
      
      <!-- PASO 4: Éxito -->
      <v-col cols="12" v-if="paso === 4">
        <v-card color="success" dark>
          <v-card-title class="text-h5">✅ Financiamiento Creado</v-card-title>
          <v-card-text>
            <h3 class="text-h4 font-weight-bold">{{ resultado?.financiamiento?.codigo }}</h3>
            <p class="text-body-1">{{ resultado?.mensaje }}</p>
            <p class="text-caption">Tasa aplicada: {{ resultado?.financiamiento?.tasa_aplicada }} BS/$</p>
            
            <v-divider class="my-3"></v-divider>
            
            <h4 class="mb-2">Cuotas Generadas:</h4>
            <v-list bg-color="transparent">
              <v-list-item v-for="n in cuotasSeleccionadas" :key="n">
                <v-list-item-title class="font-weight-bold">Cuota {{ n }}</v-list-item-title>
                <v-list-item-subtitle>Vence: {{ fechaCuota(n) }} | BS {{ formatearNumero(resultado?.financiamiento?.monto_cuota_bs) }}</v-list-item-subtitle>
              </v-list-item>
            </v-list>
            
            <v-btn color="white" @click="resetear" block class="mt-3 text-success" size="large">Nueva Venta</v-btn>
          </v-card-text>
        </v-card>
      </v-col>
    </v-row>
  </v-container>
  
  <!-- No autorizado -->
  <v-container v-else>
    <v-alert type="error" class="mt-10">
      <v-icon start>mdi-shield-lock</v-icon>
      Solo el administrador central puede crear nuevas ventas.
    </v-alert>
  </v-container>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { api } from '@/config/api'

const paso = ref(1)
const busquedaCedula = ref('')
const clienteEncontrado = ref(null)
const clienteNoEncontrado = ref(false)
const nuevoCliente = ref({ nombre: '', telefono: '', email: '', cedula: '', direccion: '', referencia_nombre: '', referencia_telefono: '', referencia_parentesco: '' })
const montoTotalBS = ref('')
const propuesta = ref(null)
const cuotasSeleccionadas = ref(null)
const descripcion = ref('')
const resultado = ref({})
const tasaDolar = ref(40.0)
const requiereAprobacion = ref(false)

const esAdminCentral = computed(() => localStorage.getItem('admin_rol') === 'admin_central')

const opcionesCuotas = computed(() => {
  if (!propuesta.value) return []
  const p = propuesta.value.propuesta || propuesta.value
  const config = propuesta.value.configuracion_nivel || {}
  const cuotasBase = p.cuotas_base || config.cuotas_base || 4
  const cuotasMax = p.cuotas_max || config.cuotas_max || 12
  const financiaBs = p.financia_bs || propuesta.value.monto_financia_bs || 0
  const opciones = []
  for (let i = cuotasBase; i <= cuotasMax; i++) {
    const montoCuota = financiaBs / i
    opciones.push({ value: i, monto: montoCuota, monto_usd: montoCuota / (propuesta.value.tasa_dolar_actual || tasaDolar.value || 40) })
  }
  return opciones
})

const montoCuotaSeleccionada = computed(() => {
  const opcion = opcionesCuotas.value.find(o => o.value === cuotasSeleccionadas.value)
  return opcion?.monto || 0
})

const registroValido = computed(() => {
  return nuevoCliente.value.nombre && nuevoCliente.value.telefono && nuevoCliente.value.email &&
         nuevoCliente.value.direccion && nuevoCliente.value.referencia_nombre &&
         nuevoCliente.value.referencia_telefono && nuevoCliente.value.referencia_parentesco
})

const colorNivel = (nivel) => ({ nuevo: 'grey', bronce: 'brown', plata: 'blue', oro: 'amber', platino: 'purple' })[nivel] || 'grey'
const formatearNumero = (num) => num ? Number(num).toLocaleString('es-VE', { minimumFractionDigits: 2, maximumFractionDigits: 2 }) : '0,00'

onMounted(async () => {
  try { const data = await api.get('/config/tasa-dolar'); tasaDolar.value = data.tasa } catch (e) {}
})

const buscarCliente = async () => {
  if (!busquedaCedula.value) return
  try {
    const data = await api.get(`/clientes/buscar/${busquedaCedula.value}`)
    if (data.error || !data.encontrado) {
      clienteEncontrado.value = null; clienteNoEncontrado.value = true; nuevoCliente.value.cedula = busquedaCedula.value
    } else {
      clienteEncontrado.value = { ...data, bloqueado: false }; clienteNoEncontrado.value = false
    }
  } catch (e) {
    clienteEncontrado.value = null; clienteNoEncontrado.value = true; nuevoCliente.value.cedula = busquedaCedula.value
  }
}

const registrarCliente = async () => {
  if (!registroValido.value) { alert('Complete todos los campos obligatorios'); return }
  try {
    await api.post('/clientes', { nombre: nuevoCliente.value.nombre, cedula: busquedaCedula.value, telefono: nuevoCliente.value.telefono, email: nuevoCliente.value.email || '', direccion: nuevoCliente.value.direccion, referencia_nombre: nuevoCliente.value.referencia_nombre, referencia_telefono: nuevoCliente.value.referencia_telefono, referencia_parentesco: nuevoCliente.value.referencia_parentesco })
    alert('✅ Cliente registrado exitosamente'); await buscarCliente()
  } catch (e) { alert('Error registrando cliente') }
}

const calcularPropuesta = async () => {
  if (!montoTotalBS.value || parseFloat(montoTotalBS.value) <= 0 || !clienteEncontrado.value) { propuesta.value = null; cuotasSeleccionadas.value = null; return }
  try {
    const data = await api.get(`/clientes/${clienteEncontrado.value.id}/nivel-propuesta?monto_total_bs=${montoTotalBS.value}`)
    propuesta.value = data
    cuotasSeleccionadas.value = data.propuesta?.cuotas_base || data.configuracion_nivel?.cuotas_base || 4
    requiereAprobacion.value = data.propuesta?.requiere_aprobacion_extra || false
  } catch (e) { propuesta.value = null }
}

const fechaCuota = (n) => new Date(Date.now() + (15 * n * 24 * 60 * 60 * 1000)).toLocaleDateString('es-VE')

const crearFinanciamiento = async () => {
  try {
    const data = await api.post('/financiamientos', { cliente_id: clienteEncontrado.value.id, descripcion: descripcion.value || 'Compra', monto_total_bs: parseFloat(montoTotalBS.value), cuotas_solicitadas: cuotasSeleccionadas.value })
    if (data.error) { alert('Error: ' + data.error); return }
    resultado.value = data; paso.value = 4
  } catch (e) { alert('Error creando financiamiento') }
}

const resetear = () => {
  paso.value = 1; busquedaCedula.value = ''; clienteEncontrado.value = null; clienteNoEncontrado.value = false
  nuevoCliente.value = { nombre: '', telefono: '', email: '', cedula: '', direccion: '', referencia_nombre: '', referencia_telefono: '', referencia_parentesco: '' }
  montoTotalBS.value = ''; propuesta.value = null; cuotasSeleccionadas.value = null; descripcion.value = ''; resultado.value = {}; requiereAprobacion.value = false
}
</script>