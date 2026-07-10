import axios from 'axios'

// Usar variable de entorno o fallback local
const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

const api = axios.create({
  baseURL: API_URL,  // ✅ Usa variable de entorno
  headers: {
    'Content-Type': 'application/json'
  }
})

export default api