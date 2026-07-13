<template>
  <div class="success-wrapper">
    <div class="bg-gradient"></div>

    <div class="page-content">
      <v-card class="success-card glass-card" elevation="0">
        <v-card-text class="pa-4 text-center">
          <v-icon size="64" color="#4caf50" class="mb-3">mdi-check-circle</v-icon>
          <h2 class="success-title">¡Registro Exitoso!</h2>
          <p class="success-sub">Tu solicitud ha sido enviada para verificación</p>

          <v-alert v-if="pinGenerado" type="info" class="pin-alert" border="start" density="compact">
            <div class="pin-label">📱 PIN de acceso:</div>
            <div class="pin-value">{{ pinGenerado }}</div>
            <div class="pin-hint">Usa este PIN para entrar a la app</div>
          </v-alert>
          <v-alert v-else type="warning" class="pin-alert" border="start" density="compact">
            <div class="pin-label">⏳ Esperando PIN</div>
            <div class="pin-hint">Revisa tu WhatsApp/SMS</div>
          </v-alert>

          <v-divider style="border-color: rgba(255,255,255,0.06);" />

          <v-list density="compact" class="bg-transparent text-left">
            <v-list-item>
              <v-list-item-title>📨 Recibirás un SMS/WhatsApp con tu PIN de acceso</v-list-item-title>
            </v-list-item>
            <v-list-item>
              <v-list-item-title>⏳ Verificación en 24-48 horas</v-list-item-title>
            </v-list-item>
          </v-list>

          <v-divider style="border-color: rgba(255,255,255,0.06);" />

          <div class="info-row"><span>Tu cédula:</span><span>{{ cedula }}</span></div>
          <div class="info-row"><span>Estado:</span><v-chip color="warning" size="x-small"><v-icon size="12" start>mdi-clock-outline</v-icon>En verificación</v-chip></div>

          <v-divider style="border-color: rgba(255,255,255,0.06);" />

          <v-btn color="#4facfe" rounded="pill" block size="large" class="login-btn" @click="irALogin">
            <v-icon start size="18">mdi-login</v-icon>Ir al Login
          </v-btn>

          <p class="login-hint">🔑 Usa tu cédula y el PIN que te enviamos</p>
        </v-card-text>
      </v-card>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'

const route = useRoute()
const router = useRouter()
const cedula = route.params.cedula || ''
const pinGenerado = ref(null)

onMounted(() => {
  const storedPin = localStorage.getItem('financoop_pin_temp')
  if (storedPin) {
    pinGenerado.value = storedPin
    localStorage.removeItem('financoop_pin_temp')
  }
})

const irALogin = () => {
  localStorage.removeItem('financoop_token')
  router.push('/login')
}
</script>

<style scoped>
.success-wrapper {
  min-height: 100vh;
  background: #0a0e1a;
  position: relative;
  display: flex;
  align-items: center;
  justify-content: center;
}

.bg-gradient {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: radial-gradient(ellipse at 20% 50%, rgba(79, 172, 254, 0.08), transparent 70%),
              radial-gradient(ellipse at 80% 50%, rgba(99, 102, 241, 0.08), transparent 70%);
  z-index: 0;
}

.page-content {
  position: relative;
  z-index: 1;
  width: 100%;
  max-width: 420px;
  padding: 20px;
}

.glass-card {
  background: rgba(255,255,255,0.04) !important;
  backdrop-filter: blur(20px) !important;
  -webkit-backdrop-filter: blur(20px) !important;
  border: 1px solid rgba(255,255,255,0.06);
  border-radius: 24px !important;
}

.success-title {
  font-size: 22px;
  font-weight: 700;
  color: #4caf50;
}

.success-sub {
  font-size: 14px;
  color: rgba(255,255,255,0.4);
  margin-bottom: 16px;
}

.pin-alert {
  background: rgba(79, 172, 254, 0.05) !important;
  border-color: rgba(79, 172, 254, 0.15) !important;
  border-radius: 12px !important;
  margin-bottom: 16px;
}

.pin-label {
  font-size: 12px;
  font-weight: 600;
  color: rgba(255,255,255,0.5);
}

.pin-value {
  font-size: 28px;
  font-weight: 700;
  color: #4facfe;
}

.pin-hint {
  font-size: 11px;
  color: rgba(255,255,255,0.3);
}

.info-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 0;
  font-size: 13px;
  color: rgba(255,255,255,0.6);
}

.info-row span:first-child {
  color: rgba(255,255,255,0.3);
}

.login-btn {
  background: linear-gradient(135deg, #4facfe, #6366f1) !important;
  font-weight: 700;
  height: 50px;
}

.login-hint {
  font-size: 12px;
  color: rgba(255,255,255,0.2);
  margin-top: 12px;
}
</style>