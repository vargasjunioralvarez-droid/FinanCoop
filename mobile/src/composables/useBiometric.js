// mobile/src/composables/useBiometric.js
import { ref } from 'vue'
import { BiometricAuth } from '@aparajita/capacitor-biometric-auth'
import { Capacitor } from '@capacitor/core'
import { Preferences } from '@capacitor/preferences'

const huellaSoportada = ref(false)
const huellaActivada = ref(false)
const plataformaNativa = ref(false)
const cargandoHuella = ref(false)
const biometricType = ref('')
const credencialesGuardadas = ref(null)

// ✅ Claves de Preferences
const KEY_CREDENCIALES = 'financoop_huella_credenciales'
const KEY_ACTIVADA = 'financoop_huella_activada'

async function verificarSoporte() {
  plataformaNativa.value = Capacitor.isNativePlatform()
  
  if (!plataformaNativa.value) {
    console.log('📱 Navegador - Sin biometría')
    return false
  }

  try {
    const result = await BiometricAuth.checkBiometry()
    console.log('📋 checkBiometry:', JSON.stringify(result))
    
    huellaSoportada.value = result.isAvailable
    biometricType.value = result.biometryType || 'fingerprint'
    
    // ✅ LEER DE PREFERENCES (persiste entre cierres)
    const { value: credencialesStr } = await Preferences.get({ key: KEY_CREDENCIALES })
    if (credencialesStr) {
      try {
        credencialesGuardadas.value = JSON.parse(credencialesStr)
        console.log('📦 Credenciales huella encontradas:', credencialesGuardadas.value.cedula)
      } catch (e) {
        console.log('⚠️ Credenciales corruptas, limpiando...')
        await Preferences.remove({ key: KEY_CREDENCIALES })
      }
    }
    
    if (huellaSoportada.value) {
      const { value: activada } = await Preferences.get({ key: KEY_ACTIVADA })
      huellaActivada.value = activada === 'true' && !!credencialesGuardadas.value
      console.log('🔐 Huella activada:', huellaActivada.value)
    }
    
    return huellaSoportada.value
  } catch (e) {
    console.log('❌ Error checkBiometry:', e.message)
    return false
  }
}

async function guardarCredencialesHuella(cedula, pin) {
  if (!cedula || !pin) {
    console.log('⚠️ No se guardan credenciales: cedula o pin vacío')
    return false
  }
  
  const credenciales = { 
    cedula: String(cedula).trim(), 
    pin: String(pin).trim(), 
    fecha: new Date().toISOString() 
  }
  
  // ✅ GUARDAR EN PREFERENCES (persiste entre cierres)
  await Preferences.set({
    key: KEY_CREDENCIALES,
    value: JSON.stringify(credenciales)
  })
  await Preferences.set({ key: KEY_ACTIVADA, value: 'true' })
  
  // También guardar en localStorage como respaldo
  try {
    localStorage.setItem('financoop_huella_credenciales', JSON.stringify(credenciales))
    localStorage.setItem('financoop_huella_activada', 'true')
    localStorage.setItem('financoop_usuario', JSON.stringify({ cedula }))
  } catch (e) {}
  
  credencialesGuardadas.value = credenciales
  huellaActivada.value = true
  
  console.log('✅ Credenciales guardadas permanentemente:', credenciales.cedula)
  return true
}

async function limpiarCredencialesHuella() {
  // ✅ LIMPIAR DE PREFERENCES
  await Preferences.remove({ key: KEY_CREDENCIALES })
  await Preferences.set({ key: KEY_ACTIVADA, value: 'false' })
  
  // También limpiar de localStorage
  try {
    localStorage.removeItem('financoop_huella_credenciales')
    localStorage.setItem('financoop_huella_activada', 'false')
  } catch (e) {}
  
  credencialesGuardadas.value = null
  huellaActivada.value = false
  console.log('🔒 Credenciales de huella eliminadas')
}

async function toggleHuella(activar, cedulaParam, pinParam) {
  cargandoHuella.value = true
  try {
    if (activar) {
      await BiometricAuth.authenticate({
        reason: 'Verifica tu identidad para activar huella',
        cancelTitle: 'Cancelar',
        androidTitle: 'Activar huella',
        androidSubtitle: 'Coloca tu dedo en el sensor'
      })
      
      let cedula = cedulaParam
      let pin = pinParam
      
      if (!cedula || !pin) {
        try {
          const loginForm = JSON.parse(localStorage.getItem('financoop_login_form') || '{}')
          cedula = cedula || loginForm.cedula
          pin = pin || loginForm.pin
        } catch (e) {}
      }
      
      if (!cedula) {
        try {
          const usuario = JSON.parse(localStorage.getItem('financoop_usuario') || '{}')
          cedula = usuario.cedula
        } catch (e) {}
      }
      
      if (!cedula || !pin) {
        return { success: false, error: 'No se encontraron credenciales. Inicia sesión con PIN primero.' }
      }
      
      await guardarCredencialesHuella(cedula, pin)
      return { success: true }
    } else {
      await limpiarCredencialesHuella()
      return { success: true }
    }
  } catch (e) {
    console.error('❌ Error toggleHuella:', e.message)
    return { success: false, error: e.message || 'No se pudo verificar' }
  } finally {
    cargandoHuella.value = false
  }
}

// ✅ AUTENTICAR CON HUELLA - Persiste entre cierres
async function autenticarConHuella() {
  if (!huellaSoportada.value) {
    return { success: false, error: 'Biometría no disponible en este dispositivo' }
  }

  // ✅ Si no hay credenciales en memoria, leer de Preferences
  if (!credencialesGuardadas.value) {
    const { value: credencialesStr } = await Preferences.get({ key: KEY_CREDENCIALES })
    if (credencialesStr) {
      try {
        credencialesGuardadas.value = JSON.parse(credencialesStr)
      } catch (e) {}
    }
  }

  if (!credencialesGuardadas.value || !credencialesGuardadas.value.cedula || !credencialesGuardadas.value.pin) {
    return { 
      success: false, 
      error: 'No hay huella configurada. Inicia sesión con PIN primero para activarla.' 
    }
  }

  cargandoHuella.value = true
  try {
    await BiometricAuth.authenticate({
      reason: `Bienvenido de nuevo, ${credencialesGuardadas.value.cedula}`,
      cancelTitle: 'Cancelar',
      androidTitle: 'Iniciar sesión',
      androidSubtitle: 'Usa tu huella para ingresar'
    })

    console.log('✅ Huella verificada para:', credencialesGuardadas.value.cedula)

    const API_URL = 'https://financoop-agd5.onrender.com/api/v1'
    
    const response = await fetch(`${API_URL}/auth/login-cliente`, {
      method: 'POST',
      headers: { 
        'Content-Type': 'application/json',
        'Accept': 'application/json'
      },
      body: JSON.stringify({ 
        cedula: credencialesGuardadas.value.cedula,
        pin: credencialesGuardadas.value.pin
      })
    })

    const data = await response.json()
    
    if (!response.ok) {
      if (response.status === 401) {
        await limpiarCredencialesHuella()
        return { success: false, error: 'PIN ha cambiado. Inicia sesión con PIN nuevamente.' }
      }
      return { success: false, error: data.detail || data.error || 'Error en login' }
    }
    
    const token = data.access_token || data.token
    if (!token) {
      return { success: false, error: 'No se recibió token' }
    }
    
    return { 
      success: true, 
      data: { 
        access_token: token, 
        cliente: data.cliente,
        cedula: credencialesGuardadas.value.cedula
      } 
    }

  } catch (e) {
    console.error('❌ Error autenticarConHuella:', e.message)
    if (e.message?.toLowerCase().includes('cancel')) {
      return { success: false, error: null, cancelled: true }
    }
    return { success: false, error: e.message || 'Huella no reconocida' }
  } finally {
    cargandoHuella.value = false
  }
}

// ✅ VERIFICAR SI HAY HUELLA ACTIVADA (para LoginView)
async function hayHuellaGuardada() {
  if (!plataformaNativa.value) await verificarSoporte()
  
  if (!huellaSoportada.value) return false
  
  const { value: credencialesStr } = await Preferences.get({ key: KEY_CREDENCIALES })
  const { value: activada } = await Preferences.get({ key: KEY_ACTIVADA })
  
  if (credencialesStr && activada === 'true') {
    try {
      credencialesGuardadas.value = JSON.parse(credencialesStr)
      huellaActivada.value = true
      return true
    } catch (e) {
      return false
    }
  }
  return false
}

export function useBiometric() {
  return {
    huellaSoportada,
    huellaActivada,
    plataformaNativa,
    cargandoHuella,
    biometricType,
    credencialesGuardadas,
    verificarSoporte,
    toggleHuella,
    autenticarConHuella,
    guardarCredencialesHuella,
    limpiarCredencialesHuella,
    hayHuellaGuardada
  }
}