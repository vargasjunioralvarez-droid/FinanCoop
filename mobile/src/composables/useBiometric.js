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
      credencialesGuardadas.value = JSON.parse(credenciales)
    }
    
    if (huellaSoportada.value) {
      const pref = localStorage.getItem('financoop_huella_activada')
      huellaActivada.value = pref === 'true'
    }
    
    return huellaSoportada.value
  } catch (e) {
    console.log('❌ Error checkBiometry:', e.message)
    return false
  }
}

function guardarCredencialesHuella(cedula) {
  const credenciales = { cedula, fecha: new Date().toISOString() }
  localStorage.setItem('financoop_huella_credenciales', JSON.stringify(credenciales))
  credencialesGuardadas.value = credenciales
  huellaActivada.value = true
  localStorage.setItem('financoop_huella_activada', 'true')
  console.log('✅ Credenciales guardadas para huella:', cedula)
}

function limpiarCredencialesHuella() {
  localStorage.removeItem('financoop_huella_credenciales')
  credencialesGuardadas.value = null
  huellaActivada.value = false
  localStorage.setItem('financoop_huella_activada', 'false')
  console.log('🔒 Credenciales de huella eliminadas')
}

async function toggleHuella(activar) {
  cargandoHuella.value = true
  try {
    if (activar) {
      await BiometricAuth.authenticate({
        reason: 'Verifica tu identidad para activar huella',
        cancelTitle: 'Cancelar',
        androidTitle: 'Activar huella',
        androidSubtitle: 'Coloca tu dedo en el sensor'
      })
      
      const token = localStorage.getItem('financoop_token')
      if (!token) {
        return { success: false, error: 'Debes iniciar sesión primero' }
      }
      
      const usuario = JSON.parse(localStorage.getItem('financoop_usuario') || '{}')
      if (!usuario.cedula) {
        return { success: false, error: 'No se encontraron datos del usuario' }
      }
      
      guardarCredencialesHuella(usuario.cedula)
      
      return { success: true }
    } else {
      limpiarCredencialesHuella()
      return { success: true }
    }
  } catch (e) {
    console.error('❌ Error:', e.message)
    return { success: false, error: e.message || 'No se pudo verificar' }
  } finally {
    cargandoHuella.value = false
  }
}

// ✅ AUTENTICAR CON HUELLA - CORREGIDO Y SEGURO
async function autenticarConHuella(cedula) {
  if (!huellaSoportada.value) {
    return { success: false, error: 'Biometría no disponible' }
  }

  // ✅ VERIFICAR CREDENCIALES GUARDADAS
  if (!credencialesGuardadas.value) {
    return { 
      success: false, 
      error: 'No hay credenciales guardadas. Inicia sesión con PIN primero.' 
    }
  }

  // ✅ VERIFICAR QUE LA CÉDULA COINCIDA CON LA GUARDADA
  if (credencialesGuardadas.value.cedula !== cedula) {
    return { 
      success: false, 
      error: 'La cédula no coincide con la huella guardada. Usa tu PIN.' 
    }
  }

  cargandoHuella.value = true
  try {
    // ✅ VERIFICAR HUELLA
    await BiometricAuth.authenticate({
      reason: `Autentícate para acceder a FinanCoop como ${cedula}`,
      cancelTitle: 'Cancelar',
      androidTitle: 'Iniciar sesión',
      androidSubtitle: `Usa tu huella para ingresar como ${cedula}`
    })

    console.log('✅ Huella verificada para cédula:', cedula)

    // ✅ EL LOGIN BIOMÉTRICO ESTÁ DESHABILITADO EN EL BACKEND
    // Por seguridad (H11), no enviamos PIN ni hacemos login automático.
    return { 
      success: false, 
      error: 'El acceso con huella está temporalmente deshabilitado. Usa tu PIN para ingresar.' 
    }

  } catch (e) {
    console.error('❌ Error:', e.message)
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