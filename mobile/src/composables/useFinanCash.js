import { ref, computed } from 'vue'

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

// Estado global
const token = ref(localStorage.getItem('financoop_token') || null)
const usuario = ref({})
const datosCliente = ref({})
const financiamientos = ref([])
const todasCuotas = ref([])
const tasaActual = ref(0)
const historialDolar = ref([])
const datosPago = ref({})
const cuotaSeleccionada = ref(null)
const notificaciones = ref([])
const cargando = ref(false)
const error = ref(null)
const cargandoPago = ref(false)

// Configuración de niveles
const nivelesConfig = ref({
  nuevo: { monto_max_usd: 160, entrada_pct: 60, cuotas_max: 3, mora_diaria: 2.0 },
  bronce: { monto_max_usd: 200, entrada_pct: 50, cuotas_max: 5, mora_diaria: 1.5 },
  plata: { monto_max_usd: 250, entrada_pct: 40, cuotas_max: 8, mora_diaria: 1.0 },
  oro: { monto_max_usd: 350, entrada_pct: 30, cuotas_max: 12, mora_diaria: 0.5 },
  platino: { monto_max_usd: 500, entrada_pct: 20, cuotas_max: 15, mora_diaria: 0.5 }
})

// Formularios
const loginForm = ref({ cedula: '', pin: '' })
const pagoForm = ref({
  metodo: 'pago_movil',
  referencia: '',
  banco_origen: '',
  telefono_pago: '',
  cedula_pago: '',
  comprobante: null
})

const metodosPago = [
  { title: 'Pago Móvil', value: 'pago_movil' },
  { title: 'Transferencia', value: 'transferencia' },
  { title: 'Zelle', value: 'zelle' },
  { title: 'Binance', value: 'binance' }
]

// ============ COMPUTED ============
const nivelActual = computed(() => nivelesConfig.value[usuario.value.nivel] || {})

const siguienteNivel = computed(() => {
  const orden = ['nuevo', 'bronce', 'plata', 'oro', 'platino']
  const idx = orden.indexOf(usuario.value.nivel)
  if (idx >= orden.length - 1) return null
  const key = orden[idx + 1]
  const config = nivelesConfig.value[key]
  return { key, max_score: config ? config.min_score : 999 }
})

const progresoNivel = computed(() => {
  if (!siguienteNivel.value) return 100
  const min = nivelesConfig.value[usuario.value.nivel]?.min_score || 0
  const max = siguienteNivel.value.max_score
  const current = usuario.value.score || 0
  return Math.min(100, ((current - min) / (max - min)) * 100)
})

const lineaUsada = computed(() => datosCliente.value?.limite?.usado_usd || 0)
const lineaDisponible = computed(() => datosCliente.value?.limite?.disponible_usd || 0)

const cuotasPendientes = computed(() => 
  todasCuotas.value.filter(c => c.estado === 'pendiente' && new Date(c.fecha_vencimiento) >= new Date())
)

const cuotasVencidas = computed(() =>
  todasCuotas.value.filter(c => c.estado === 'pendiente' && new Date(c.fecha_vencimiento) < new Date())
)

const cuotasProximas = computed(() => {
  const hoy = new Date()
  return todasCuotas.value
    .filter(c => c.estado === 'pendiente')
    .sort((a, b) => new Date(a.fecha_vencimiento) - new Date(b.fecha_vencimiento))
})

const totalDeudaBs = computed(() => 
  financiamientos.value.reduce((sum, f) => sum + (f.saldo_pendiente_bs || 0), 0)
)

const totalDeudaUsd = computed(() => 
  financiamientos.value.reduce((sum, f) => sum + (f.saldo_pendiente_usd_ref || 0), 0)
)

const badgeCount = computed(() => cuotasVencidas.value.length)

// ============ FUNCIONES AUXILIARES ============
function formatearBS(valor) {
  if (!valor && valor !== 0) return '0,00'
  return new Intl.NumberFormat('es-VE', {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2
  }).format(valor)
}

function formatearUSD(valor) {
  if (!valor && valor !== 0) return '0.00'
  return new Intl.NumberFormat('en-US', {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2
  }).format(valor)
}

function formatearNumero(valor) {
  if (!valor && valor !== 0) return '0'
  return new Intl.NumberFormat('es-VE').format(valor)
}

function formatearFecha(fechaStr) {
  if (!fechaStr) return ''
  const fecha = new Date(fechaStr)
  return fecha.toLocaleDateString('es-VE', {
    weekday: 'short',
    day: 'numeric',
    month: 'short'
  })
}

function formatearFechaCorta(fechaStr) {
  if (!fechaStr) return ''
  const fecha = new Date(fechaStr)
  return fecha.toLocaleDateString('es-VE', {
    day: 'numeric',
    month: 'short'
  })
}

function colorNivel(nivel) {
  const colores = {
    nuevo: 'grey',
    bronce: '#cd7f32',
    plata: '#c0c0c0',
    oro: '#ffd700',
    platino: '#e5e4e2'
  }
  return colores[nivel] || 'primary'
}

function iconoNivel(nivel) {
  const iconos = {
    nuevo: 'mdi-star-outline',
    bronce: 'mdi-medal',
    plata: 'mdi-medal-outline',
    oro: 'mdi-trophy',
    platino: 'mdi-crown'
  }
  return iconos[nivel] || 'mdi-account'
}

function copiarAlPortapapeles(texto) {
  navigator.clipboard.writeText(texto).then(() => {
    // Podrías emitir un toast aquí
    console.log('Copiado:', texto)
  })
}

// ============ API CALLS ============
async function apiCall(endpoint, options = {}) {
  const url = `${API_URL}${endpoint}`
  const config = {
    headers: {
      'Content-Type': 'application/json',
      ...(token.value ? { 'Authorization': `Bearer ${token.value}` } : {})
    },
    ...options
  }
  
  if (config.body && typeof config.body === 'object') {
    config.body = JSON.stringify(config.body)
  }
  
  try {
    const res = await fetch(url, config)
    if (!res.ok) throw new Error(`HTTP ${res.status}`)
    return await res.json()
  } catch (err) {
    console.error('API Error:', err)
    throw err
  }
}

// ============ AUTH ============
async function iniciarSesion() {
  cargando.value = true
  error.value = null
  
  try {
    const data = await apiCall('/app/login', {
      method: 'POST',
      body: loginForm.value
    })
    
    if (data.error) {
      error.value = data.error
      return false
    }
    
    token.value = data.token
    localStorage.setItem('financoop_token', data.token)
    usuario.value = data.cliente
    return true
  } catch (err) {
    error.value = 'Error de conexión. Intenta de nuevo.'
    return false
  } finally {
    cargando.value = false
  }
}

function cerrarSesion() {
  token.value = null
  localStorage.removeItem('financoop_token')
  localStorage.removeItem('financoop_theme')
  usuario.value = {}
  datosCliente.value = {}
  financiamientos.value = []
  todasCuotas.value = []
}

// ============ CARGAR DATOS ============
async function cargarDatos() {
  if (!token.value) return
  
  try {
    // Datos del cliente
    const misDatos = await apiCall(`/app/mis-datos?token=${token.value}`)
    if (misDatos.error) {
      if (misDatos.error.includes('Sesión')) {
        cerrarSesion()
      }
      return
    }
    
    datosCliente.value = misDatos
    usuario.value = misDatos.cliente
    tasaActual.value = misDatos.tasa_actual
    financiamientos.value = misDatos.financiamientos_activos || []
    datosPago.value = misDatos.datos_pago || {}
    
    // Cuotas
    const misCuotas = await apiCall(`/app/mis-cuotas?token=${token.value}`)
    if (!misCuotas.error) {
      todasCuotas.value = misCuotas.cuotas || []
    }
    
    // Historial de tasas
    const tasaData = await apiCall('/config/tasa-dolar')
    if (!tasaData.error) {
      historialDolar.value = tasaData.historial || []
    }
    
  } catch (err) {
    console.error('Error cargando datos:', err)
  }
}

// ============ PAGOS ============
async function reportarPago() {
  if (!cuotaSeleccionada.value) return false
  
  cargandoPago.value = true
  error.value = null
  
  try {
    const formData = new FormData()
    formData.append('cuota_id', cuotaSeleccionada.value.cuota_id)
    formData.append('monto_bs', cuotaSeleccionada.value.monto_total_bs)
    formData.append('metodo', pagoForm.value.metodo)
    formData.append('referencia', pagoForm.value.referencia)
    formData.append('banco_origen', pagoForm.value.banco_origen)
    formData.append('telefono_pago', pagoForm.value.telefono_pago)
    formData.append('cedula_pago', pagoForm.value.cedula_pago)
    
    if (pagoForm.value.comprobante) {
      formData.append('comprobante', pagoForm.value.comprobante)
    }
    
    const res = await fetch(`${API_URL}/pagos/reportar`, {
      method: 'POST',
      body: formData
    })
    
    const data = await res.json()
    
    if (data.error) {
      error.value = data.error
      return false
    }
    
    // Reset form
    pagoForm.value = {
      metodo: 'pago_movil',
      referencia: '',
      banco_origen: '',
      telefono_pago: '',
      cedula_pago: '',
      comprobante: null
    }
    
    return true
  } catch (err) {
    error.value = 'Error al reportar el pago'
    return false
  } finally {
    cargandoPago.value = false
  }
}

// ============ ACTUALIZAR PERFIL ============
async function actualizarPerfil(datos) {
  try {
    const data = await apiCall(`/app/cliente/${usuario.value.id}`, {
      method: 'PUT',
      body: datos
    })
    
    if (data.error) {
      return { success: false, error: data.error }
    }
    
    // Recargar datos
    await cargarDatos()
    return { success: true }
  } catch (err) {
    return { success: false, error: 'Error de conexión' }
  }
}

async function subirFotoCedula(file) {
  try {
    const formData = new FormData()
    formData.append('cedula_foto', file)
    
    const res = await fetch(`${API_URL}/app/cliente/${usuario.value.id}/cedula`, {
      method: 'POST',
      headers: token.value ? { 'Authorization': `Bearer ${token.value}` } : {},
      body: formData
    })
    
    const data = await res.json()
    return { success: !data.error, error: data.error }
  } catch (err) {
    return { success: false, error: 'Error al subir foto' }
  }
}

// ============ EXPORT ============
export function useFinanCash() {
  return {
    // Estado
    token,
    usuario,
    datosCliente,
    financiamientos,
    todasCuotas,
    tasaActual,
    historialDolar,
    datosPago,
    cuotaSeleccionada,
    notificaciones,
    cargando,
    error,
    cargandoPago,
    
    // Config
    nivelesConfig,
    loginForm,
    pagoForm,
    metodosPago,
    
    // Computed
    nivelActual,
    siguienteNivel,
    progresoNivel,
    lineaUsada,
    lineaDisponible,
    cuotasPendientes,
    cuotasVencidas,
    cuotasProximas,
    totalDeudaBs,
    totalDeudaUsd,
    badgeCount,
    
    // Funciones
    formatearBS,
    formatearUSD,
    formatearNumero,
    formatearFecha,
    formatearFechaCorta,
    colorNivel,
    iconoNivel,
    copiarAlPortapapeles,
    
    // API
    iniciarSesion,
    cerrarSesion,
    cargarDatos,
    reportarPago,
    actualizarPerfil,
    subirFotoCedula
  }
}