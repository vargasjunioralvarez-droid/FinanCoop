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
  event.respondWith(
    caches.match(event.request)
      .then(cached => {
        // Devolver cache si existe
        if (cached) return cached
        
        // Si no, ir a la red
        return fetch(event.request)
          .then(response => {
            // Cachear respuestas GET exitosas
            if (event.request.method === 'GET' && response.status === 200) {
              const clone = response.clone()
              caches.open(CACHE_NAME).then(cache => {
                cache.put(event.request, clone)
              })
            }
            return response
          })
          .catch(() => {
            // Si falla la red y es navegación, mostrar offline
            if (event.request.mode === 'navigate') {
              return caches.match('/index.html')
            }
          })
      })
  )
})