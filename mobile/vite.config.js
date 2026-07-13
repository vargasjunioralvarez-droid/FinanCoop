import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import { VitePWA } from 'vite-plugin-pwa'
import { resolve } from 'path'

export default defineConfig({
  plugins: [
    vue(),
    VitePWA({
      registerType: 'autoUpdate',
      manifest: false, // Usaremos manifest.json separado
      workbox: {
        globPatterns: ['**/*.{js,css,html,ico,png,svg,woff2,json}'],
        maximumFileSizeToCacheInBytes: 5 * 1024 * 1024,
        // 🔥 FIX: NO cachear rutas de API
        navigateFallback: null,
        runtimeCaching: [
          {
            // 🔥 FIX: Cachear solo assets, NO API
            urlPattern: /^https:\/\/financoop\.onrender\.com\/(?!app\/|pagos\/|clientes\/|config\/|admin\/|auth\/).*/,
            handler: 'NetworkFirst',
            options: {
              cacheName: 'assets-cache',
              expiration: {
                maxEntries: 100,
                maxAgeSeconds: 86400 // 24 horas
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
                maxAgeSeconds: 60 * 60 * 24 * 30 // 30 días
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
                maxAgeSeconds: 60 * 60 * 24 * 30 // 30 días
              }
            }
          }
        ]
      },
      devOptions: {
        enabled: true,
        type: 'module'
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
    host: true,
    // 🔥 FIX: Configurar WebSocket correctamente para eliminar el error
    ws: {
      host: 'localhost',
      port: 5175,
      protocol: 'ws'
    },
    // 🔥 FIX: Configurar HMR para que use el mismo puerto
    hmr: {
      port: 5175,
      host: 'localhost',
      protocol: 'ws'
    }
  }
})