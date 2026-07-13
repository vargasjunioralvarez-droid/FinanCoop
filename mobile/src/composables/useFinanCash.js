// mobile/src/composables/useFinanCash.js
import { ref, computed } from 'vue'
import { CapacitorHttp } from '@capacitor/core'

const API_URL = 'https://financoop.onrender.com'

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
// 🔥 FIX: Headers mínimos para evitar CORS preflight innecesario
async function apiCall(endpoint, options = {}) {
  const url = `${API_URL}${endpoint}`
  
  // 🔥 FIX: Headers básicos SIN cache-control (evita preflight complejo)
  const headers = {
    'Content-Type': 'application/json',
    'Accept': 'application/json',
    ...options.headers
  }
  
  // Token en header Authorization (NO en query param)
  if (token.value && endpoint.includes('/app/')) {
    headers['Authorization'] = `Bearer ${token.value}`
  }
  
  try {
    console.log(`🌐 API Call: ${options.method || 'GET'} ${url}`)
    
    const response = await CapacitorHttp.request({
      method: options.method || 'GET',
      url: url,
      headers: headers,
      data: options.body || undefined,
      connectTimeout: 30000,
      readTimeout: 30000
    })
    
    console.log(`✅ Response status:`, response.status)
    
    if (response.status >= 400) {
      const errorMsg = response.data?.detail || response.data?.error || `HTTP ${response.status}`
      throw new Error(errorMsg)
    }
    
    return response.data
    
  } catch (err) {
    console.error('❌ API Error:', err)
    
    if (err.message?.includes('401') || err.message?.includes('Sesión no válida')) {
      console.log('🔒 Token inválido, cerrando sesión...')
      cerrarSesion()
    }
    
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
  
  try {
    const response = await CapacitorHttp.request({
      method: 'POST',
      url: `${API_URL}/app/login`,
      headers: {
        'Content-Type': 'application/json',
        'Accept': 'application/json'
      },
      data: { cedula, pin },
      connectTimeout: 30000,
      readTimeout: 30000
    })
    
    const data = response.data
    
    if (data.error) {
      error.value = data.error
      cargando.value = false
      return false
    }
    
    if (data.token) {
      token.value = data.token
      localStorage.setItem('financoop_token', data.token)
      console.log('✅ Login exitoso, token guardado')
    } else {
      error.value = 'Error: No se recibió token'
      cargando.value = false
      return false
    }
    
    usuario.value = data.cliente || {}
    await cargarDatos()
    
    cargando.value = false
    return true
    
  } catch (err) {
    console.error('❌ Error en login:', err)
    error.value = 'Error de conexión: ' + (err.message || 'desconocido')
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
    const data = {}
    formData.forEach((value, key) => {
      data[key] = value
    })
    
    const response = await CapacitorHttp.request({
      method: 'POST',
      url: `${API_URL}/clientes`,
      headers: {
        'Content-Type': 'multipart/form-data'
      },
      data: data,
      connectTimeout: 60000,
      readTimeout: 60000
    })
    
    const resData = response.data
    
    if (resData.error || resData.success === false) {
      error.value = resData.error || 'Error al registrar'
      cargando.value = false
      return { success: false, error: error.value }
    }
    
    if (resData.pin_generado) {
      localStorage.setItem('financoop_pin_temp', resData.pin_generado)
    }
    
    cargando.value = false
    return { 
      success: true, 
      pin: resData.pin_generado, 
      mensaje: resData.mensaje 
    }
  } catch (err) {
    console.error('❌ Error registrando:', err)
    error.value = 'Error de conexión: ' + (err.message || 'desconocido')
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

// ============ CARGAR DATOS ============
async function cargarDatos() {
  if (!token.value) {
    console.log('⚠️ No hay token')
    return
  }
  
  console.log('🔄 Cargando datos...')
  
  try {
    const data = await apiCall('/app/mis-datos')
    
    if (data.error) {
      console.error('❌ Error:', data.error)
      if (data.error.includes('Sesión') || data.error.includes('Token')) {
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
      const cuotasData = await apiCall('/app/mis-cuotas')
      if (cuotasData && !cuotasData.error) {
        todasCuotas.value = cuotasData.cuotas || []
      }
    } catch (err) {
      console.error('❌ Error cuotas:', err)
      todasCuotas.value = []
    }
    
  } catch (err) {
    console.error('❌ Error cargando datos:', err)
  }
}

// ============ RECALCULAR MONTOS ============
function recalcularMontosConNuevaTasa(nuevaTasa) {
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
}

// ============ PAGOS ============
async function reportarPago() {
  if (!cuotaSeleccionada.value) {
    error.value = 'No hay cuota seleccionada'
    return false
  }
  
  const cuotaId = cuotaSeleccionada.value.cuota_id || cuotaSeleccionada.value.id
  if (!cuotaId) {
    error.value = 'ID de cuota no válido'
    return false
  }
  
  const monto = cuotaSeleccionada.value.monto_bs || cuotaSeleccionada.value.monto_total_bs
  if (!monto) {
    error.value = 'Monto de cuota no válido'
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
    
    const response = await CapacitorHttp.request({
      method: 'POST',
      url: `${API_URL}/pagos/reportar`,
      headers: {
        'Content-Type': 'application/json',
        'Authorization': token.value ? `Bearer ${token.value}` : ''
      },
      data: pagoData,
      connectTimeout: 30000,
      readTimeout: 30000
    })
    
    const data = response.data
    
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
    console.error('❌ Error reportando pago:', err)
    error.value = 'Error al reportar el pago'
    cargandoPago.value = false
    return false
  }
}

// ============ SELECCIONAR CUOTA ============
function setCuotaSeleccionada(cuota) {
  console.log('📌 Cuota seleccionada:', cuota)
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
    return { success: false, error: err.message || 'Error de conexión' }
  }
}

async function subirFotoCedula(file) {
  return { success: true, error: null }
}

// ============ EXPORT ============
export function useFinanCash() {
  return {
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
    nivelesConfig,
    loginForm,
    pagoForm,
    registroForm,
    metodosPago,
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
    formatearBS,
    formatearUSD,
    formatearNumero,
    formatearFecha,
    formatearFechaCorta,
    colorNivel,
    iconoNivel,
    copiarAlPortapapeles,
    iniciarSesion,
    cerrarSesion,
    cargarDatos,
    reportarPago,
    actualizarPerfil,
    subirFotoCedula,
    registrarCliente,
    verificarCedula,
    setCuotaSeleccionada,
    recalcularMontosConNuevaTasa
  }
}