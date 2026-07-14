// mobile/src/composables/useFinanCash.js
import { ref, computed } from 'vue'

const API_URL = 'https://financoop.onrender.com'

// ============ TIMEOUT DE INACTIVIDAD ============
const INACTIVITY_TIMEOUT = 15 * 60 * 1000
let inactivityTimer = null
let listenersAdded = false
let lastResetTime = 0

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

// ============ FUNCIONES DE INACTIVIDAD ============
function resetInactivityTimer() {
  const now = Date.now()
  if (now - lastResetTime < 1000) return
  lastResetTime = now
  
  if (inactivityTimer) {
    clearTimeout(inactivityTimer)
    inactivityTimer = null
  }
  
  if (token.value) {
    console.log('⏰ Iniciando timer de inactividad (15 minutos)')
    inactivityTimer = setTimeout(() => {
      console.log('⏰ Tiempo de inactividad agotado, cerrando sesión...')
      cerrarSesionPorInactividad()
    }, INACTIVITY_TIMEOUT)
  }
}

function cerrarSesionPorInactividad() {
  console.log('🔒 Cerrando sesión por inactividad')
  if (typeof window !== 'undefined') {
    window.dispatchEvent(new CustomEvent('inactividad', { 
      detail: { mensaje: 'Sesión cerrada por inactividad' }
    }))
  }
  cerrarSesion()
}

function iniciarListenersInactividad() {
  if (listenersAdded) return
  listenersAdded = true
  
  console.log('📡 Activando listeners de inactividad')
  
  const eventos = ['click', 'touchstart', 'mousemove', 'scroll', 'keydown', 'focus', 'input', 'change']
  let throttleTimer = null
  
  const reiniciar = () => {
    if (throttleTimer) return
    throttleTimer = setTimeout(() => {
      throttleTimer = null
      resetInactivityTimer()
    }, 5000)
  }
  
  eventos.forEach(evento => {
    document.addEventListener(evento, reiniciar, { passive: true })
  })
  
  window.__inactivityListeners = { eventos, reiniciar }
}

function limpiarListenersInactividad() {
  if (!listenersAdded) return
  const { eventos, reiniciar } = window.__inactivityListeners || {}
  if (eventos && reiniciar) {
    eventos.forEach(evento => document.removeEventListener(evento, reiniciar))
  }
  listenersAdded = false
  window.__inactivityListeners = null
}

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
  return new Intl.NumberFormat('es-VE', { minimumFractionDigits: 2, maximumFractionDigits: 2 }).format(valor)
}
function formatearUSD(valor) {
  if (!valor && valor !== 0) return '0.00'
  return new Intl.NumberFormat('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 }).format(valor)
}
function formatearNumero(valor) {
  if (!valor && valor !== 0) return '0'
  return new Intl.NumberFormat('es-VE').format(valor)
}
function formatearFecha(fechaStr) {
  if (!fechaStr) return ''
  const fecha = new Date(fechaStr)
  return fecha.toLocaleDateString('es-VE', { weekday: 'short', day: 'numeric', month: 'short' })
}
function formatearFechaCorta(fechaStr) {
  if (!fechaStr) return ''
  const fecha = new Date(fechaStr)
  return fecha.toLocaleDateString('es-VE', { day: 'numeric', month: 'short' })
}
function colorNivel(nivel) {
  const colores = { nuevo: 'grey', bronce: '#cd7f32', plata: '#c0c0c0', oro: '#ffd700', platino: '#e5e4e2' }
  return colores[nivel] || 'primary'
}
function iconoNivel(nivel) {
  const iconos = { nuevo: 'mdi-star-outline', bronce: 'mdi-medal', plata: 'mdi-medal-outline', oro: 'mdi-trophy', platino: 'mdi-crown' }
  return iconos[nivel] || 'mdi-account'
}
function copiarAlPortapapeles(texto) {
  if (navigator.clipboard) {
    navigator.clipboard.writeText(texto).then(() => console.log('✅ Copiado:', texto))
  } else {
    console.log('📋 Copiado:', texto)
  }
}

// ============ API CALLS CON fetch ============
async function apiCall(endpoint, options = {}) {
  const url = `${API_URL}${endpoint}`
  
  const currentToken = localStorage.getItem('financoop_token') || token.value
  
  const headers = {
    'Content-Type': 'application/json',
    'Accept': 'application/json',
    ...options.headers
  }
  
  if (currentToken && endpoint.includes('/app/')) {
    headers['Authorization'] = `Bearer ${currentToken}`
    console.log('🔑 Token enviado en header:', currentToken.substring(0, 20) + '...')
  }
  
  try {
    console.log(`🌐 API Call: ${options.method || 'GET'} ${url}`)
    
    const fetchOptions = {
      method: options.method || 'GET',
      headers: headers,
    }
    
    if (options.body && (options.method === 'POST' || options.method === 'PUT')) {
      fetchOptions.body = JSON.stringify(options.body)
    }
    
    console.log('📤 Headers enviados:', JSON.stringify(headers))
    
    const response = await fetch(url, fetchOptions)
    const data = await response.json()
    
    console.log(`✅ Response status:`, response.status)
    console.log(`📥 Response data:`, JSON.stringify(data).substring(0, 200))
    
    if (!response.ok) {
      const errorMsg = data?.detail || data?.error || `HTTP ${response.status}`
      throw new Error(errorMsg)
    }
    
    return data
    
  } catch (err) {
    console.error('❌ API Error:', err)
    if (err.message?.includes('401') || err.message?.includes('Sesión no válida') || err.message?.includes('Token')) {
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
    console.log('🔑 Intentando login con:', { cedula, pin: '***' })
    
    const response = await fetch(`${API_URL}/app/login`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Accept': 'application/json'
      },
      body: JSON.stringify({ cedula, pin })
    })
    
    const data = await response.json()
    console.log('📥 Respuesta login:', JSON.stringify(data).substring(0, 300))
    
    if (data.error) {
      error.value = data.error
      cargando.value = false
      return false
    }
    
    if (data.token) {
      token.value = data.token
      localStorage.setItem('financoop_token', data.token)
      console.log('✅ Login exitoso, token guardado:', data.token.substring(0, 20) + '...')
      
      iniciarListenersInactividad()
      resetInactivityTimer()
    } else {
      error.value = 'Error: No se recibió token'
      cargando.value = false
      return false
    }
    
    usuario.value = data.cliente || {}
    
    console.log('🔄 Cargando datos después del login...')
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
  console.log('🔒 Cerrando sesión manualmente')
  if (inactivityTimer) {
    clearTimeout(inactivityTimer)
    inactivityTimer = null
  }
  limpiarListenersInactividad()
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
    formData.forEach((value, key) => data[key] = value)
    
    const response = await fetch(`${API_URL}/clientes`, {
      method: 'POST',
      headers: { 'Content-Type': 'multipart/form-data' },
      body: data
    })
    
    const resData = await response.json()
    
    if (resData.error || resData.success === false) {
      error.value = resData.error || 'Error al registrar'
      cargando.value = false
      return { success: false, error: error.value }
    }
    
    if (resData.pin_generado) {
      localStorage.setItem('financoop_pin_temp', resData.pin_generado)
    }
    
    cargando.value = false
    return { success: true, pin: resData.pin_generado, mensaje: resData.mensaje }
  } catch (err) {
    console.error('❌ Error registrando:', err)
    error.value = 'Error de conexión: ' + (err.message || 'desconocido')
    cargando.value = false
    return { success: false, error: error.value }
  }
}

// ============ ✅ NUEVO: OBTENER PERFIL DEL CLIENTE (APP MÓVIL) ============
async function miPerfil() {
  try {
    const data = await apiCall('/app/mi-perfil')
    if (data.error) {
      console.error('❌ Error obteniendo perfil:', data.error)
      return null
    }
    return data
  } catch (err) {
    console.error('❌ Error en miPerfil:', err)
    return null
  }
}

// ============ CARGAR DATOS ============
async function cargarDatos() {
  const currentToken = localStorage.getItem('financoop_token')
  
  if (!currentToken) {
    console.log('⚠️ No hay token en localStorage')
    return
  }
  
  if (!token.value) {
    token.value = currentToken
  }
  
  console.log('🔄 Cargando datos...')
  console.log('🔑 Token usado:', currentToken.substring(0, 20) + '...')
  
  try {
    const data = await apiCall('/app/mis-datos')
    
    console.log('📥 Datos del cliente recibidos:', JSON.stringify(data).substring(0, 300))
    
    if (data.error) {
      console.error('❌ Error en mis-datos:', data.error)
      if (data.error.includes('Sesión') || data.error.includes('Token')) {
        cerrarSesion()
      }
      return
    }
    
    datosCliente.value = data
    if (data.cliente) {
      usuario.value = data.cliente
      console.log('✅ Usuario actualizado:', data.cliente.nombre)
    }
    
    tasaActual.value = data.tasa_actual || 0
    financiamientos.value = data.financiamientos_activos || []
    datosPago.value = data.datos_pago || {}
    
    console.log('✅ Datos principales cargados. Financiamientos:', financiamientos.value.length)
    
    try {
      console.log('🔄 Cargando cuotas...')
      const cuotasData = await apiCall('/app/mis-cuotas')
      console.log('📥 Respuesta de cuotas:', JSON.stringify(cuotasData).substring(0, 200))
      
      if (cuotasData && !cuotasData.error) {
        todasCuotas.value = cuotasData.cuotas || []
        console.log('✅ Cuotas cargadas:', todasCuotas.value.length)
      } else if (cuotasData?.error) {
        console.error('❌ Error en cuotas:', cuotasData.error)
        todasCuotas.value = []
      }
    } catch (err) {
      console.error('❌ Error cargando cuotas:', err)
      todasCuotas.value = []
    }
    
    console.log('✅ Todos los datos cargados exitosamente')
    resetInactivityTimer()
    
  } catch (err) {
    console.error('❌ Error cargando datos:', err)
    error.value = 'Error cargando datos: ' + (err.message || 'desconocido')
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
    
    const currentToken = localStorage.getItem('financoop_token') || token.value
    
    const response = await fetch(`${API_URL}/pagos/reportar`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': currentToken ? `Bearer ${currentToken}` : ''
      },
      body: JSON.stringify(pagoData)
    })
    
    const data = await response.json()
    
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
    if (data.error) return { success: false, error: data.error }
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
    miPerfil,
    setCuotaSeleccionada,
    recalcularMontosConNuevaTasa,
    resetInactivityTimer,
    cerrarSesionPorInactividad
  }
}