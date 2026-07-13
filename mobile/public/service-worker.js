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

// Fetch: servir desde cache o red
self.addEventListener('fetch', event => {
  const { request } = event
  const url = new URL(request.url)

  // 🔥 FIX 1: NO interceptar peticiones de API
  if (
    url.pathname.startsWith('/app/') ||
    url.pathname.startsWith('/pagos/') ||
    url.pathname.startsWith('/clientes/') ||
    url.pathname.startsWith('/config/') ||
    url.pathname.startsWith('/admin/') ||
    url.hostname.includes('onrender.com')
  ) {
    return
  }

  // 🔥 FIX 2: NO interceptar esquemas no soportados (chrome-extension, etc.)
  if (
    url.protocol === 'chrome-extension:' ||
    url.protocol === 'chrome:' ||
    url.protocol === 'edge:' ||
    url.protocol === 'about:' ||
    url.protocol === 'data:' ||
    url.protocol === 'blob:' ||
    url.protocol === 'filesystem:'
  ) {
    return
  }

  // 🔥 FIX 3: NO interceptar WebSocket
  if (
    request.mode === 'websocket' || 
    url.protocol === 'ws:' || 
    url.protocol === 'wss:'
  ) {
    return
  }

  // 🔥 FIX 4: NO interceptar métodos que no sean GET
  if (request.method !== 'GET') {
    return
  }

  event.respondWith(
    caches.match(request)
      .then(cached => {
        if (cached) return cached
        
        return fetch(request)
          .then(response => {
            // Cachear solo respuestas GET exitosas de mismo origen y tipo basic
            if (
              request.method === 'GET' && 
              response.status === 200 &&
              response.type === 'basic'
            ) {
              const clone = response.clone()
              caches.open(CACHE_NAME).then(cache => {
                cache.put(request, clone)
              })
            }
            return response
          })
          .catch(() => {
            // Si falla la red y es navegación, mostrar offline
            if (request.mode === 'navigate') {
              return caches.match('/index.html')
            }
            // Devolver Response válido
            return new Response('Sin conexión', { 
              status: 503, 
              statusText: 'Service Unavailable',
              headers: { 'Content-Type': 'text/plain' }
            })
          })
      })
  )
})