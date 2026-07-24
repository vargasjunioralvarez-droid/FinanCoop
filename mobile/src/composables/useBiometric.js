// mobile/src/composables/useBiometric.js
import { ref } from 'vue'
import { BiometricAuth } from '@aparajita/capacitor-biometric-auth'
import { Capacitor } from '@capacitor/core'

const huellaSoportada = ref(false)
const huellaActivada = ref(false)
const plataformaNativa = ref(false)
const cargandoHuella = ref(false)
const biometricType = ref('')

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

async function toggleHuella(activar) {
  cargandoHuella.value = true
  try {
    if (activar) {
      // authenticate() lanza excepción si falla
      await BiometricAuth.authenticate({
        reason: 'Verifica tu identidad para activar huella',
        cancelTitle: 'Cancelar',
        androidTitle: 'Activar huella',
        androidSubtitle: 'Coloca tu dedo en el sensor'
      })
      
      localStorage.setItem('financoop_huella_activada', 'true')
      huellaActivada.value = true
      console.log('✅ Huella ACTIVADA')
      return { success: true }
    } else {
      localStorage.setItem('financoop_huella_activada', 'false')
      huellaActivada.value = false
      console.log('🔒 Huella DESACTIVADA')
      return { success: true }
    }
  } catch (e) {
    console.error('❌ Error:', e.message)
    return { success: false, error: e.message || 'No se pudo verificar' }
  } finally {
    cargandoHuella.value = false
  }
}

async function autenticarConHuella(cedula) {
  if (!huellaSoportada.value) {
    return { success: false, error: 'Biometría no disponible' }
  }

  cargandoHuella.value = true
  try {
    await BiometricAuth.authenticate({
      reason: 'Autentícate para acceder a FinanCoop',
      cancelTitle: 'Cancelar',
      androidTitle: 'Iniciar sesión',
      androidSubtitle: 'Usa tu huella para ingresar'
    })

    console.log('✅ Huella verificada')

    const { buildApiUrl } = await import('@/config')
    const response = await fetch(buildApiUrl('/auth/login-biometrico'), {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        cedula,
        biometric_verified: true,
        device_id: Capacitor.getPlatform() + '_' + Date.now()
      })
    })

    const data = await response.json()
    if (!response.ok) return { success: false, error: data.detail }
    return { success: true, data }

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
    verificarSoporte,
    toggleHuella,
    autenticarConHuella
  }
}