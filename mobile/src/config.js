// src/config.js
// Configuración centralizada de la API

// ✅ SIEMPRE CONECTAR A RENDER
export const API_URL = 'https://financoop.onrender.com/api/v1'

console.log('🌐 API URL configurada:', API_URL)

// ✅ FIX: Helper para construir URLs de API
export function buildApiUrl(endpoint) {
  // Asegurarse de que el endpoint empiece con /
  const cleanEndpoint = endpoint.startsWith('/') ? endpoint : `/${endpoint}`
  return `${API_URL}${cleanEndpoint}`
}

// ✅ FIX: Helper para obtener headers comunes
export function getCommonHeaders(token = null) {
  const headers = {
    'Accept': 'application/json',
    'Content-Type': 'application/json'
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
         document.URL.includes('capacitor://') ||
         document.URL.includes('localhost')
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