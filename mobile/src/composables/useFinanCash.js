import { ref, computed } from 'vue'

const API_URL = import.meta.env.VITE_API_URL || 'http://192.168.10.122:8000'

// ============ ESTADO GLOBAL ============
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

// ============ CONFIGURACIÓN DE NIVELES ============
const nivelesConfig = ref({
  nuevo: { monto_max_usd: 160, entrada_pct: 60, cuotas_max: 3, mora_diaria: 2.0, min_score: 0 },
  bronce: { monto_max_usd: 200, entrada_pct: 50, cuotas_max: 5, mora_diaria: 1.5, min_score: 100 },
  plata: { monto_max_usd: 250, entrada_pct: 40, cuotas_max: 8, mora_diaria: 1.0, min_score: 250 },
  oro: { monto_max_usd: 350, entrada_pct: 30, cuotas_max: 12, mora_diaria: 0.5, min_score: 500 },
  platino: { monto_max_usd: 500, entrada_pct: 20, cuotas_max: 15, mora_diaria: 0.5, min_score: 1000 }
})

// ============ FORMULARIOS ============
const loginForm = ref({ cedula: '', pin: '' })
const pagoForm = ref({
  metodo: 'pago_movil',
  referencia: '',
  banco_origen: '',
  telefono_pago: '',
  cedula_pago: '',
  comprobante: null
})

const registroForm = ref({
  nombre: '',
  cedula: '',
  telefono: '',
  email: '',
  direccion: '',
  referencia_nombre: '',
  referencia_telefono: '',
  referencia_parentesco: '',
  cedula_foto: null
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
  if (navigator.clipboard) {
    navigator.clipboard.writeText(texto).then(() => {
      console.log('✅ Copiado:', texto)
    }).catch(() => {
      console.log('📋 Copiado (fallback):', texto)
    })
  } else {
    console.log('📋 Copiado (fallback):', texto)
  }
}

// ============ API CALLS ============
async function apiCall(endpoint, options = {}) {
  const url = `${API_URL}${endpoint}`
  
  const headers = {
    'Content-Type': 'application/json',
    'Cache-Control': 'no-cache',
    ...options.headers
  }
  
  let finalUrl = url
  
  if (token.value && endpoint.includes('/app/')) {
    const separator = endpoint.includes('?') ? '&' : '?'
    finalUrl = `${url}${separator}token=${token.value}`
  }
  
  const config = {
    headers,
    ...options
  }
  
  if (config.body && typeof config.body === 'object') {
    config.body = JSON.stringify(config.body)
  }
  
  try {
    console.log(`🌐 API Call: ${finalUrl}`)
    const res = await fetch(finalUrl, config)
    
    if (!res.ok) {
      const errorData = await res.json().catch(() => ({}))
      console.error(`❌ API Error ${res.status}:`, errorData)
      throw new Error(errorData.error || `HTTP ${res.status}`)
    }
    
    const data = await res.json()
    console.log(`✅ API Response:`, data)
    return data
  } catch (err) {
    console.error('❌ API Error:', err)
    throw err
  }
}

// ============ AUTH ============
async function iniciarSesion() {
  cargando.value = true
  error.value = null
  
  const cedula = loginForm.value.cedula?.trim()
  const pin = loginForm.value.pin?.trim()
  
  if (!cedula || !pin) {
    error.value = 'Ingresa tu cédula y PIN'
    cargando.value = false
    return false
  }
  
  console.log('🔑 Intentando login con:', { cedula, pin })
  
  try {
    const data = await apiCall('/app/login', {
      method: 'POST',
      body: { cedula, pin }
    })
    
    console.log('📥 Respuesta login:', data)
    
    if (data.error) {
      error.value = data.error
      cargando.value = false
      return false
    }
    
    if (data.token) {
      token.value = data.token
      localStorage.setItem('financoop_token', data.token)
      console.log('✅ Token guardado:', token.value)
    } else {
      console.error('❌ No se recibió token en la respuesta')
      error.value = 'Error: No se recibió token'
      cargando.value = false
      return false
    }
    
    usuario.value = data.cliente || {}
    console.log('✅ Usuario:', usuario.value)
    
    await cargarDatos()
    
    console.log('✅ Datos cargados exitosamente')
    
    cargando.value = false
    return true
    
  } catch (err) {
    console.error('❌ Error en login:', err)
    error.value = 'Error de conexión con el servidor'
    cargando.value = false
    return false
  }
}

function cerrarSesion() {
  token.value = null
  localStorage.removeItem('financoop_token')
  usuario.value = {}
  datosCliente.value = {}
  financiamientos.value = []
  todasCuotas.value = []
  cuotaSeleccionada.value = null
}

// ============ REGISTRO ============
async function registrarCliente(formData) {
  cargando.value = true
  error.value = null
  
  try {
    const url = `${API_URL}/clientes`
    console.log('📤 Enviando a:', url)
    console.log('📞 Teléfono en formData:', formData.get('telefono'))
    
    const res = await fetch(url, {
      method: 'POST',
      body: formData
    })
    
    console.log('📥 Status:', res.status)
    
    const data = await res.json()
    console.log('📥 Respuesta:', data)
    
    if (data.error || data.success === false) {
      error.value = data.error || 'Error al registrar'
      cargando.value = false
      return { success: false, error: error.value }
    }
    
    if (data.pin_generado) {
      localStorage.setItem('financoop_pin_temp', data.pin_generado)
    }
    
    cargando.value = false
    return { 
      success: true, 
      pin: data.pin_generado, 
      mensaje: data.mensaje 
    }
  } catch (err) {
    console.error('❌ Error registrando:', err)
    error.value = 'Error de conexión con el servidor'
    cargando.value = false
    return { success: false, error: error.value }
  }
}

async function verificarCedula(cedula) {
  try {
    const data = await apiCall(`/clientes/buscar/${cedula}`)
    return data.encontrado || false
  } catch (err) {
    return false
  }
}

// ============ CARGAR DATOS DEL CLIENTE ============
async function cargarDatos() {
  if (!token.value) {
    console.log('⚠️ No hay token, no se cargan datos')
    return
  }
  
  console.log('🔄 Cargando datos del cliente...')
  console.log('🔑 Token usado:', token.value)
  
  try {
    const data = await apiCall('/app/mis-datos')
    console.log('📥 Datos del cliente:', data)
    
    if (data.error) {
      console.error('❌ Error en mis-datos:', data.error)
      
      if (data.error.includes('Sesión no válida') || data.error.includes('Token no proporcionado')) {
        console.log('⚠️ Token inválido, cerrando sesión...')
        cerrarSesion()
      }
      return
    }
    
    datosCliente.value = data
    
    if (data.cliente) {
      usuario.value = data.cliente
    }
    
    tasaActual.value = data.tasa_actual || 0
    financiamientos.value = data.financiamientos_activos || []
    datosPago.value = data.datos_pago || {}
    
    try {
      console.log('🔄 Cargando cuotas...')
      const cuotasData = await apiCall('/app/mis-cuotas')
      console.log('📥 Respuesta de cuotas:', cuotasData)
      
      if (cuotasData && !cuotasData.error) {
        todasCuotas.value = cuotasData.cuotas || []
        console.log('✅ Cuotas cargadas:', todasCuotas.value.length)
      } else {
        console.warn('⚠️ No se pudieron cargar cuotas:', cuotasData?.error)
        todasCuotas.value = []
      }
    } catch (err) {
      console.error('❌ Error cargando cuotas:', err)
      todasCuotas.value = []
    }
    
    console.log('✅ Datos cargados exitosamente')
    
  } catch (err) {
    console.error('❌ Error cargando datos:', err)
  }
}

// ============ RECALCULAR MONTOS CON NUEVA TASA ============
function recalcularMontosConNuevaTasa(nuevaTasa) {
  console.log('🔄 Recalculando montos con nueva tasa:', nuevaTasa)
  
  tasaActual.value = nuevaTasa
  
  financiamientos.value = financiamientos.value.map(fin => {
    fin.monto_total_bs = (fin.monto_total_usd_ref || 0) * nuevaTasa
    fin.saldo_pendiente_bs = (fin.saldo_pendiente_usd_ref || 0) * nuevaTasa
    fin.monto_entrada_bs = (fin.monto_entrada_usd_ref || 0) * nuevaTasa
    
    if (fin.proxima_cuota) {
      fin.proxima_cuota.monto_bs = (fin.proxima_cuota.monto_usd_ref || 0) * nuevaTasa
    }
    
    return fin
  })
  
  todasCuotas.value = todasCuotas.value.map(c => {
    const usdRef = c.monto_total_usd_ref || c.monto_usd_ref || 0
    c.monto_total_bs = usdRef * nuevaTasa
    c.monto_bs = usdRef * nuevaTasa
    return c
  })
  
  console.log('✅ Montos recalculados con nueva tasa:', nuevaTasa)
}

// ============ PAGOS ============
async function reportarPago() {
  if (!cuotaSeleccionada.value) {
    error.value = 'No hay cuota seleccionada'
    console.error('❌ Error: No hay cuota seleccionada')
    return false
  }
  
  const cuotaId = cuotaSeleccionada.value.cuota_id || cuotaSeleccionada.value.id
  if (!cuotaId) {
    error.value = 'ID de cuota no válido'
    console.error('❌ Error: ID de cuota no válido', cuotaSeleccionada.value)
    return false
  }
  
  const monto = cuotaSeleccionada.value.monto_bs || cuotaSeleccionada.value.monto_total_bs
  if (!monto) {
    error.value = 'Monto de cuota no válido'
    console.error('❌ Error: Monto no válido', cuotaSeleccionada.value)
    return false
  }
  
  if (!pagoForm.value.referencia) {
    error.value = 'Ingresa el número de referencia'
    return false
  }
  
  if (!pagoForm.value.metodo) {
    error.value = 'Selecciona un método de pago'
    return false
  }
  
  cargandoPago.value = true
  error.value = null
  
  try {
    const pagoData = {
      cuota_id: cuotaId,
      monto_bs: monto,
      metodo: pagoForm.value.metodo,
      referencia: pagoForm.value.referencia,
      banco_origen: pagoForm.value.banco_origen || '',
      telefono_pago: pagoForm.value.telefono_pago || '',
      cedula_pago: pagoForm.value.cedula_pago || ''
    }
    
    console.log('📤 Enviando pago:', pagoData)
    
    const url = `${API_URL}/pagos/reportar`
    const res = await fetch(url, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        ...(token.value ? { 'Authorization': `Bearer ${token.value}` } : {})
      },
      body: JSON.stringify(pagoData)
    })
    
    const data = await res.json()
    console.log('📥 Respuesta del servidor:', data)
    
    if (data.error) {
      error.value = data.error
      cargandoPago.value = false
      return false
    }
    
    pagoForm.value = {
      metodo: 'pago_movil',
      referencia: '',
      banco_origen: '',
      telefono_pago: '',
      cedula_pago: '',
      comprobante: null
    }
    
    cuotaSeleccionada.value = null
    await cargarDatos()
    
    cargandoPago.value = false
    return true
    
  } catch (err) {
    console.error('❌ Error en reportarPago:', err)
    error.value = 'Error al reportar el pago. Intenta de nuevo.'
    cargandoPago.value = false
    return false
  }
}

// ============ SELECCIONAR CUOTA ============
function setCuotaSeleccionada(cuota) {
  console.log('📌 Seteando cuota seleccionada:', cuota)
  cuotaSeleccionada.value = cuota
}

// ============ ACTUALIZAR PERFIL ============
async function actualizarPerfil(datos) {
  try {
    const data = await apiCall(`/clientes/${usuario.value.id}`, {
      method: 'PUT',
      body: datos
    })
    
    if (data.error) {
      return { success: false, error: data.error }
    }
    
    await cargarDatos()
    return { success: true }
  } catch (err) {
    return { success: false, error: 'Error de conexión' }
  }
}

async function subirFotoCedula(file) {
  return { success: true, error: null }
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
    registroForm,
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
    
    // Funciones auxiliares
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
    subirFotoCedula,
    registrarCliente,
    verificarCedula,
    
    // Seleccionar cuota
    setCuotaSeleccionada,
    
    // Recalcular con nueva tasa
    recalcularMontosConNuevaTasa
  }
}