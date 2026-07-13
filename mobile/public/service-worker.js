const CACHE_NAME = 'financoop-v1'
const STATIC_ASSETS = [
  '/',
  '/index.html',
  '/manifest.json',
  '/icons/icon-192x192.png',
  '/icons/icon-512x512.png'
]

// Instalar: cachear recursos estáticos
self.addEventListener('install', event => {
  event.waitUntil(
    caches.open(CACHE_NAME)
      .then(cache => cache.addAll(STATIC_ASSETS))
      .then(() => self.skipWaiting())
  )
})

// Activar: limpiar caches antiguas
self.addEventListener('activate', event => {
  event.waitUntil(
    caches.keys().then(cacheNames => {
      return Promise.all(
        cacheNames
          .filter(name => name !== CACHE_NAME)
          .map(name => caches.delete(name))
      )
    }).then(() => self.clients.claim())
  )
})

// ============ FETCH ============
self.addEventListener('fetch', event => {
  const { request } = event
  const url = new URL(request.url)
  
  // 🔥 FIX CRÍTICO: NO interceptar peticiones a API externa (Render)
  // CapacitorHttp usa el SW del browser, y si interceptamos la API externa
  // causa "Failed to convert value to 'Response'"
  const API_HOSTS = [
    'financoop.onrender.com',
    'financash-backend.onrender.com',
    'financash-frontend.onrender.com'
  ]
  
  if (API_HOSTS.includes(url.hostname)) {
    // Pasar directo a la red, NO cachear
    return
  }
  
  // 🔥 FIX: NO interceptar chrome-extension o esquemas no-HTTP
  if (!url.protocol.startsWith('http')) {
    return
  }
  
  // 🔥 FIX: NO interceptar peticiones POST/PUT/DELETE (solo cachear GET)
  if (request.method !== 'GET') {
    return
  }
  
  event.respondWith(
    caches.match(request)
      .then(cached => {
        // Devolver cache si existe
        if (cached) {
          // Refrescar en background (stale-while-revalidate)
          fetch(request).then(response => {
            if (response && response.status === 200) {
              const clone = response.clone()
              caches.open(CACHE_NAME).then(cache => {
                cache.put(request, clone)
              })
            }
          }).catch(() => {})
          
          return cached
        }
        
        // Si no en cache, ir a la red
        return fetch(request)
          .then(response => {
            // Solo cachear respuestas válidas de mismo origen
            if (!response || response.status !== 200 || response.type !== 'basic') {
              return response
            }
            
            const clone = response.clone()
            caches.open(CACHE_NAME).then(cache => {
              cache.put(request, clone)
            })
            return response
          })
          .catch(error => {
            console.error('❌ SW fetch error:', error)
            
            // Si es navegación, devolver index.html (SPA fallback)
            if (request.mode === 'navigate') {
              return caches.match('/index.html')
            }
            
            // Para otros recursos, devolver error controlado
            return new Response(
              JSON.stringify({ error: 'Sin conexión', offline: true }),
              {
                status: 503,
                headers: { 'Content-Type': 'application/json' }
              }
            )
          })
      })
  )
})