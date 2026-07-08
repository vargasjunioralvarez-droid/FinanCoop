import { createApp } from 'vue'
import App from './App.vue'
import vuetify from './plugins/vuetify'
import router from './router'

import '@mdi/font/css/materialdesignicons.css'

const app = createApp(App)
app.use(vuetify)
app.use(router)
app.mount('#app')

// ✅ Registrar Service Worker
if ('serviceWorker' in navigator) {
  window.addEventListener('load', () => {
    navigator.serviceWorker.register('/service-worker.js')
      .then(registration => {
        console.log('✅ SW registrado:', registration.scope)
      })
      .catch(error => {
        console.log('❌ Error SW:', error)
      })
  })
}

console.log('✅ App iniciada con Vue Router')