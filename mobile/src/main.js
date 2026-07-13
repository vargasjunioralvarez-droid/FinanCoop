// mobile/src/main.js
import { createApp } from 'vue'
import App from './App.vue'
import vuetify from './plugins/vuetify'
import router from './router'

import '@mdi/font/css/materialdesignicons.css'

const app = createApp(App)
app.use(vuetify)
app.use(router)
app.mount('#app')

// 🔥 DESACTIVAR SERVICE WORKER PARA FORZAR NUEVOS DISEÑOS
if ('serviceWorker' in navigator) {
  // DESREGISTRAR CUALQUIER SERVICE WORKER EXISTENTE
  navigator.serviceWorker.getRegistrations().then(function(registrations) {
    for(let registration of registrations) {
      registration.unregister()
      console.log('✅ Service Worker desregistrado')
    }
  })
}

console.log('✅ App iniciada con Vue Router (SW desactivado)')