// mobile/src/composables/useBiometric.js
import { ref } from 'vue'
import { BiometricAuth } from '@aparajita/capacitor-biometric-auth'
import { Capacitor } from '@capacitor/core'

const huellaSoportada = ref(false)
const huellaActivada = ref(false)
const plataformaNativa = ref(false)
const cargandoHuella = ref(false)
const biometricType = ref('')
const credencialesGuardadas = ref(null)

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
    
    const credenciales = localStorage.getItem('financoop_huella_credenciales')
    if (credenciales) {
      try {
        credencialesGuardadas.value = JSON.parse(credenciales)
        console.log('📦 Credenciales huella encontradas:', credencialesGuardadas.value.cedula)
      } catch (e) {
        console.log('⚠️ Credenciales corruptas, limpiando...')
        localStorage.removeItem('financoop_huella_credenciales')
      }
    }
    
    if (huellaSoportada.value) {
      const pref = localStorage.getItem('financoop_huella_activada')
      huellaActivada.value = pref === 'true' && !!credencialesGuardadas.value
    }
    
    return huellaSoportada.value
  } catch (e) {
    console.log('❌ Error checkBiometry:', e.message)
    return false
  }
}

function guardarCredencialesHuella(cedula, pin) {
  if (!cedula || !pin) {
    console.log('⚠️ No se guardan credenciales: cedula o pin vacío')
    return false
  }
  const credenciales = { 
    cedula: String(cedula).trim(), 
    pin: String(pin).trim(), 
    fecha: new Date().toISOString() 
  }
  localStorage.setItem('financoop_huella_credenciales', JSON.stringify(credenciales))
  credencialesGuardadas.value = credenciales
  huellaActivada.value = true
  localStorage.setItem('financoop_huella_activada', 'true')
  console.log('✅ Credenciales guardadas para huella:', credenciales.cedula)
  return true
}

function limpiarCredencialesHuella() {
  localStorage.removeItem('financoop_huella_credenciales')
  credencialesGuardadas.value = null
  huellaActivada.value = false
  localStorage.setItem('financoop_huella_activada', 'false')
  console.log('🔒 Credenciales de huella eliminadas')
}

async function toggleHuella(activar, cedulaParam, pinParam) {
  cargandoHuella.value = true
  try {
    if (activar) {
      // 1. Verificar identidad con huella
      await BiometricAuth.authenticate({
        reason: 'Verifica tu identidad para activar huella',
        cancelTitle: 'Cancelar',
        androidTitle: 'Activar huella',
        androidSubtitle: 'Coloca tu dedo en el sensor'
      })
      
      // 2. Obtener cédula y PIN
      let cedula = cedulaParam
      let pin = pinParam
      
      // Si no vienen por parámetro, buscar en localStorage
      if (!cedula || !pin) {
        try {
          const loginForm = JSON.parse(localStorage.getItem('financoop_login_form') || '{}')
          cedula = cedula || loginForm.cedula
          pin = pin || loginForm.pin
        } catch (e) {}
      }
      
      // Buscar en usuario
      if (!cedula) {
        try {
          const usuario = JSON.parse(localStorage.getItem('financoop_usuario') || '{}')
          cedula = usuario.cedula
        } catch (e) {}
      }
      
      if (!cedula || !pin) {
        return { success: false, error: 'No se encontraron credenciales. Inicia sesión con PIN primero.' }
      }
      
      // 3. Guardar
      guardarCredencialesHuella(cedula, pin)
      return { success: true }
    } else {
      limpiarCredencialesHuella()
      return { success: true }
    }
  } catch (e) {
    console.error('❌ Error toggleHuella:', e.message)
    return { success: false, error: e.message || 'No se pudo verificar' }
  } finally {
    cargandoHuella.value = false
  }
}

// ✅ AUTENTICAR CON HUELLA - Sin necesidad de escribir cédula
async function autenticarConHuella() {
  if (!huellaSoportada.value) {
    return { success: false, error: 'Biometría no disponible en este dispositivo' }
  }

  if (!credencialesGuardadas.value || !credencialesGuardadas.value.cedula || !credencialesGuardadas.value.pin) {
    return { 
      success: false, 
      error: 'No hay huella configurada. Inicia sesión con PIN primero para activarla.' 
    }
  }

  cargandoHuella.value = true
  try {
    // 1. Verificar huella
    await BiometricAuth.authenticate({
      reason: `Bienvenido de nuevo, ${credencialesGuardadas.value.cedula}`,
      cancelTitle: 'Cancelar',
      androidTitle: 'Iniciar sesión',
      androidSubtitle: 'Usa tu huella para ingresar'
    })

    console.log('✅ Huella verificada para:', credencialesGuardadas.value.cedula)

    // 2. Login con las credenciales guardadas
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
      // Si el PIN cambió, limpiar credenciales
      if (response.status === 401) {
        limpiarCredencialesHuella()
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
    // Si el usuario canceló, no es un error grave
    if (e.message?.toLowerCase().includes('cancel')) {
      return { success: false, error: null, cancelled: true }
    }
    return { success: false, error: e.message || 'Huella no reconocida' }
  } finally {
    cargandoHuella.value = false
  }
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
    limpiarCredencialesHuella
  }
}