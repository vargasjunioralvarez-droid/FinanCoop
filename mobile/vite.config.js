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
        // 🔥 FIX: NO cachear rutas de API
        navigateFallback: null,
        runtimeCaching: [
          {
            // 🔥 FIX: Cachear solo assets, NO API
            urlPattern: /^https:\/\/financoop\.onrender\.com\/(?!app\/|pagos\/|clientes\/|config\/|admin\/).*/,
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
              cacheName: 'google-fonts-stylesheets'
            }
          }
        ]
      },
      devOptions: {
        enabled: true
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
    // 🔥 FIX: Configurar HMR para evitar errores WebSocket
    hmr: {
      port: 5175,
      host: 'localhost',
      protocol: 'ws'
    }
  }
})