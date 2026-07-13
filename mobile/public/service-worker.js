// mobile/public/service-worker.js
const CACHE_NAME = 'financoop-v1'
const STATIC_ASSETS = [
  '/',
  '/index.html',
  '/manifest.json',
  '/icons/icon-192x192.png',
  '/icons/icon-512x512.png'
]

// ============================================================
// ✅ INSTALAR: cachear recursos estáticos
// ============================================================
self.addEventListener('install', event => {
  console.log('[SW] Install event')
  
  event.waitUntil(
    caches.open(CACHE_NAME)
      .then(cache => {
        console.log('[SW] Caching static assets...')
        return cache.addAll(STATIC_ASSETS)
      })
      .then(() => {
        console.log('[SW] Static assets cached')
        return self.skipWaiting()
      })
      .catch(err => {
        console.error('[SW] Error caching static assets:', err)
      })
  )
})

// ============================================================
// ✅ ACTIVAR: limpiar caches antiguas
// ============================================================
self.addEventListener('activate', event => {
  console.log('[SW] Activate event')
  
  event.waitUntil(
    caches.keys()
      .then(cacheNames => {
        const oldCaches = cacheNames.filter(name => name !== CACHE_NAME)
        console.log('[SW] Removing old caches:', oldCaches)
        
        return Promise.all(
          oldCaches.map(name => {
            console.log('[SW] Deleting cache:', name)
            return caches.delete(name)
          })
        )
      })
      .then(() => {
        console.log('[SW] Old caches removed')
        return self.clients.claim()
      })
  )
})

// ============================================================
// ✅ FETCH: servir desde cache o red
// ============================================================
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
    url.pathname.startsWith('/auth/') ||
    url.hostname.includes('onrender.com')
  ) {
    console.log('[SW] Bypassing API request:', url.pathname)
    return
  }
  
  // 🔥 FIX 2: NO interceptar esquemas no soportados
  if (
    url.protocol === 'chrome-extension:' ||
    url.protocol === 'chrome:' ||
    url.protocol === 'edge:' ||
    url.protocol === 'about:' ||
    url.protocol === 'data:' ||
    url.protocol === 'blob:' ||
    url.protocol === 'filesystem:'
  ) {
    console.log('[SW] Bypassing unsupported protocol:', url.protocol)
    return
  }
  
  // 🔥 FIX 3: NO interceptar WebSocket
  if (
    request.mode === 'websocket' || 
    url.protocol === 'ws:' || 
    url.protocol === 'wss:'
  ) {
    console.log('[SW] Bypassing WebSocket')
    return
  }
  
  // 🔥 FIX 4: NO interceptar métodos que no sean GET
  if (request.method !== 'GET') {
    console.log('[SW] Bypassing non-GET request:', request.method)
    return
  }
  
  event.respondWith(
    caches.match(request)
      .then(cached => {
        if (cached) {
          console.log('[SW] Serving from cache:', url.pathname)
          return cached
        }
        
        console.log('[SW] Fetching from network:', url.pathname)
        
        return fetch(request)
          .then(response => {
            // Cachear solo respuestas GET exitosas de mismo origen y tipo basic
            if (
              request.method === 'GET' && 
              response.status === 200 &&
              response.type === 'basic'
            ) {
              const clone = response.clone()
              caches.open(CACHE_NAME)
                .then(cache => {
                  console.log('[SW] Caching:', url.pathname)
                  cache.put(request, clone)
                })
                .catch(err => {
                  console.error('[SW] Error caching:', err)
                })
            }
            return response
          })
          .catch(error => {
            console.error('[SW] Network error for:', url.pathname, error)
            
            // Si falla la red y es navegación, mostrar offline
            if (request.mode === 'navigate') {
              return caches.match('/index.html')
                .then(cached => {
                  if (cached) {
                    console.log('[SW] Serving offline fallback: index.html')
                    return cached
                  }
                  console.log('[SW] No offline fallback available')
                  return new Response('Offline - No se pudo cargar la página', {
                    status: 503,
                    statusText: 'Service Unavailable',
                    headers: { 'Content-Type': 'text/html' }
                  })
                })
            }
            
            // Devolver Response válido para otros recursos
            return new Response('Sin conexión', {
              status: 503,
              statusText: 'Service Unavailable',
              headers: { 'Content-Type': 'text/plain' }
            })
          })
      })
  )
})

// ============================================================
// ✅ MENSAJE: escuchar mensajes del cliente
// ============================================================
self.addEventListener('message', event => {
  console.log('[SW] Message received:', event.data)
  
  if (event.data === 'skipWaiting') {
    console.log('[SW] Skipping waiting...')
    self.skipWaiting()
  }
})