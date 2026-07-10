// src/config/api.js
// Detectar si estamos en desarrollo (localhost) o producción (Render)
const isDev = import.meta.env.DEV

// En desarrollo usa el proxy (/api), en producción usa la URL completa
export const API_URL = isDev ? '/api' : (import.meta.env.VITE_API_URL || 'https://financoop.onrender.com')

export const api = {
  get: async (endpoint) => {
    const url = `${API_URL}${endpoint}`
    console.log(`🌐 API Call: ${url}`)
    const response = await fetch(url)
    return response.json()
  },
  post: async (endpoint, data) => {
    const url = `${API_URL}${endpoint}`
    console.log(`🌐 API Call: ${url}`)
    const response = await fetch(url, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data)
    })
    return response.json()
  }
}