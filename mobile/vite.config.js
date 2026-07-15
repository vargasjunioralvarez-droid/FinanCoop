import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import { VitePWA } from 'vite-plugin-pwa'
import { resolve } from 'path'

export default defineConfig({
  plugins: [
    vue(),
    VitePWA({
      registerType: 'autoUpdate',
      manifest: false,
      workbox: {
        globPatterns: ['**/*.{js,css,html,ico,png,svg,woff2,json}'],
        maximumFileSizeToCacheInBytes: 5 * 1024 * 1024,
        navigateFallback: null,
        navigateFallbackDenylist: [
          /^\/api/, 
          /^\/app/, 
          /^\/pagos/, 
          /^\/clientes/, 
          /^\/config/, 
          /^\/admin/, 
          /^\/auth/
        ],
        runtimeCaching: [
          {
            urlPattern: ({ url }) => {
              const apiPaths = ['/app/', '/pagos/', '/clientes/', '/config/', '/admin/', '/auth/', '/api/'];
              const isApi = apiPaths.some(path => url.pathname.startsWith(path));
              return !isApi && (
                url.origin === self.location.origin || 
                url.pathname.match(/\.(js|css|png|jpg|svg|woff2|json)$/)
              );
            },
            handler: 'NetworkFirst',
            options: {
              cacheName: 'assets-cache',
              expiration: {
                maxEntries: 100,
                maxAgeSeconds: 86400
              },
              networkTimeoutSeconds: 10
            }
          },
          {
            urlPattern: /^https:\/\/fonts\.googleapis\.com\/.*/,
            handler: 'CacheFirst',
            options: {
              cacheName: 'google-fonts-stylesheets',
              expiration: {
                maxEntries: 10,
                maxAgeSeconds: 60 * 60 * 24 * 30
              }
            }
          },
          {
            urlPattern: /^https:\/\/fonts\.gstatic\.com\/.*/,
            handler: 'CacheFirst',
            options: {
              cacheName: 'google-fonts-assets',
              expiration: {
                maxEntries: 30,
                maxAgeSeconds: 60 * 60 * 24 * 30
              }
            }
          }
        ]
      },
      // ✅ FIX: Desactivar Service Worker en desarrollo para evitar recargas infinitas
      // El SW solo se activa en build de producción (npm run build)
      devOptions: {
        enabled: false
      }
    })
  ],
  resolve: {
    alias: {
      '@': resolve(__dirname, 'src')
    }
  },
  server: {
    port: 5175,
    host: true
  },
  build: {
    rollupOptions: {
      external: []
    }
  }
})