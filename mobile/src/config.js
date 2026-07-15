// src/config.js
// Configuración centralizada de la API
export const API_URL = 'https://financoop.onrender.com'

// ✅ FIX: Helper para construir URLs de API
export function buildApiUrl(endpoint) {
  return `${API_URL}${endpoint}`
}

// ✅ FIX: Helper para obtener headers comunes
export function getCommonHeaders(token = null) {
  const headers = {
    'Accept': 'application/json'
  }

  if (token) {
    headers['Authorization'] = `Bearer ${token}`
  }

  return headers
}

// ✅ FIX: Verificar si estamos en Capacitor (app móvil)
export function isCapacitor() {
  return window.Capacitor !== undefined || 
         navigator.userAgent.includes('Capacitor') ||
         document.URL.includes('capacitor://')
}

// ✅ FIX: Verificar conexión a internet
export async function checkInternetConnection() {
  try {
    const controller = new AbortController()
    const timeoutId = setTimeout(() => controller.abort(), 5000)

    const response = await fetch(`${API_URL}/app/configuracion-pagos`, {
      method: 'HEAD',
      signal: controller.signal
    })

    clearTimeout(timeoutId)
    return response.ok
  } catch (err) {
    console.error('❌ Sin conexión a internet:', err.message)
    return false
  }
}