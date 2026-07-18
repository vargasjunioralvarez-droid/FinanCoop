// mobile/src/composables/useFinanCash.js
import { ref, computed } from 'vue'
import { CapacitorHttp } from '@capacitor/core'

// ✅ URL con /api/v1
const API_URL = import.meta.env.VITE_API_URL || 'https://financoop.onrender.com/api/v1'
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
const cargandoUpload = ref(false)

// ============ CONFIGURACIÓN DE NIVELES ============
const nivelesConfig = ref({})
const nivelesCargados = ref(false)

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
    inactivityTimer = setTimeout(() => {
      cerrarSesionPorInactividad()
    }, INACTIVITY_TIMEOUT)
  }
}

function cerrarSesionPorInactividad() {
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

// ============ CARGAR NIVELES ============
async function cargarNiveles() {
  try {
    const data = await apiCall('/config/niveles')
    const niveles = data.niveles || data
    
    if (niveles && typeof niveles === 'object' && !niveles.error) {
      nivelesConfig.value = niveles
      nivelesCargados.value = true
      return true
    }
    return false
  } catch (err) {
    nivelesConfig.value = {}
    nivelesCargados.value = false
    return false
  }
}

// ============ COMPUTED ============
const nivelActual = computed(() => {
  const nivel = usuario.value.nivel
  if (!nivel || !nivelesConfig.value[nivel]) return {}
  return nivelesConfig.value[nivel]
})

const siguienteNivel = computed(() => {
  const orden = ['nuevo', 'bronce', 'plata', 'oro', 'platino']
  const idx = orden.indexOf(usuario.value.nivel)
  if (idx >= orden.length - 1) return null
  const key = orden[idx + 1]
  const config = nivelesConfig.value[key]
  if (!config) return null
  return { key, max_score: config.min_score }
})

const progresoNivel = computed(() => {
  if (!siguienteNivel.value) return 100
  const currentConfig = nivelesConfig.value[usuario.value.nivel]
  if (!currentConfig) return 0
  const min = currentConfig.min_score || 0
  const max = siguienteNivel.value.max_score
  const current = usuario.value.score || 0
  if (max <= min) return 100
  return Math.min(100, Math.max(0, ((current - min) / (max - min)) * 100))
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
    navigator.clipboard.writeText(texto)
  }
}

// ============ API CALLS CON CapacitorHttp ============
async function apiCall(endpoint, options = {}) {
  const url = `${API_URL}${endpoint}`
  const currentToken = localStorage.getItem('financoop_token') || token.value

  const headers = {
    'Accept': 'application/json',
    ...options.headers
  }

  if (!(options.body instanceof FormData)) {
    headers['Content-Type'] = 'application/json'
  }

  if (currentToken) {
    headers['Authorization'] = `Bearer ${currentToken}`
  }

  try {
    const httpOptions = {
      method: options.method || 'GET',
      url: url,
      headers: headers,
    }

    if (options.body) {
      if (options.body instanceof FormData) {
        const formDataObj = {}
        options.body.forEach((value, key) => {
          formDataObj[key] = value
        })
        httpOptions.data = formDataObj
      } else {
        httpOptions.data = options.body
      }
    }

    const response = await CapacitorHttp.request(httpOptions)
    const data = response.data || {}

    if (response.status < 200 || response.status >= 300) {
      const errorMsg = data?.detail || data?.error || `Error ${response.status}`
      throw new Error(errorMsg)
    }

    return data

  } catch (err) {
    if (err.message?.includes('401') || err.message?.includes('Token')) {
      cerrarSesion()
    }
    throw err
  }
}

// ============ SUBIR COMPROBANTE ============
async function subirComprobante(file) {
  if (!file) return null
  
  cargandoUpload.value = true
  
  try {
    const formData = new FormData()
    formData.append('file', file)
    
    const data = await apiCall('/upload/comprobante', {
      method: 'POST',
      body: formData,
    })
    
    if (data.success && data.url) {
      return data.url
    }
    return null
  } catch (e) {
    return null
  } finally {
    cargandoUpload.value = false
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
    // ✅ NUEVO ENDPOINT UNIFICADO
    const data = await apiCall('/auth/login-cliente', {
      method: 'POST',
      body: { cedula, pin }
    })

    if (data.error) {
      error.value = data.error
      cargando.value = false
      return false
    }

    if (data.access_token) {
      token.value = data.access_token
      localStorage.setItem('financoop_token', data.access_token)

      iniciarListenersInactividad()
      resetInactivityTimer()
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
    error.value = err.message || 'Error de conexión. Verifica tu internet.'
    cargando.value = false
    return false
  }
}

function cerrarSesion() {
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
  nivelesConfig.value = {}
  nivelesCargados.value = false
}

// ============ REGISTRO ============
async function registrarCliente(formData) {
  cargando.value = true
  error.value = null

  try {
    if (!(formData instanceof FormData)) {
      error.value = 'Error interno: formato de datos incorrecto'
      cargando.value = false
      return { success: false, error: error.value }
    }

    const response = await fetch(`${API_URL}/clientes`, {
      method: 'POST',
      body: formData
    })

    const resData = await response.json()

    if (!response.ok) {
      error.value = resData.detail || 'Error al registrar'
      cargando.value = false
      return { success: false, error: error.value }
    }

    if (resData.pin) {
      localStorage.setItem('financoop_pin_temp', resData.pin)
    }

    cargando.value = false
    return { success: true, pin: resData.pin, mensaje: resData.mensaje }
  } catch (err) {
    error.value = 'Error de conexión: ' + (err.message || 'desconocido')
    cargando.value = false
    return { success: false, error: error.value }
  }
}

// ============ OBTENER PERFIL ============
async function miPerfil() {
  try {
    const data = await apiCall('/app/mi-perfil')
    if (data.error) return null
    return data
  } catch (err) {
    return null
  }
}

// ============ CARGAR DATOS ============
async function cargarDatos() {
  const currentToken = localStorage.getItem('financoop_token')

  if (!currentToken) return

  if (!token.value) {
    token.value = currentToken
  }

  try {
    if (!nivelesCargados.value) {
      await cargarNiveles()
    }

    const data = await apiCall('/app/mis-datos')

    if (data.error) {
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
      todasCuotas.value = []
    }

    resetInactivityTimer()

  } catch (err) {
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
async function reportarPago(payload = null) {
  if (payload) {
    cargandoPago.value = true
    error.value = null
    
    try {
      const data = await apiCall('/pagos/reportar', {
        method: 'POST',
        body: payload
      })
      
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
      error.value = err.message || 'Error desconocido'
      cargandoPago.value = false
      return false
    }
  }
  
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

  cargandoPago.value = true
  error.value = null

  try {
    let comprobanteUrl = null
    if (pagoForm.value.comprobante && pagoForm.value.comprobante instanceof File) {
      comprobanteUrl = await subirComprobante(pagoForm.value.comprobante)
      if (!comprobanteUrl) {
        error.value = 'No se pudo subir el comprobante'
        cargandoPago.value = false
        return false
      }
    }

    const pagoData = {
      cuota_id: cuotaId,
      monto_bs: monto,
      metodo: pagoForm.value.metodo,
      referencia: pagoForm.value.referencia,
      banco_origen: pagoForm.value.banco_origen || '',
      telefono_pago: pagoForm.value.telefono_pago || '',
      cedula_pago: pagoForm.value.cedula_pago || '',
      comprobante: comprobanteUrl || ''
    }

    const data = await apiCall('/pagos/reportar', {
      method: 'POST',
      body: pagoData
    })

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
    error.value = 'Error al reportar el pago: ' + (err.message || 'desconocido')
    cargandoPago.value = false
    return false
  }
}

// ============ SELECCIONAR CUOTA ============
function setCuotaSeleccionada(cuota) {
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
    cargandoUpload,
    nivelesConfig,
    nivelesCargados,
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
    cerrarSesionPorInactividad,
    cargarNiveles,
    subirComprobante
  }
}