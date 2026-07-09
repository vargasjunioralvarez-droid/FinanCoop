<template>
  <v-container class="success-container" fluid>
    <v-row justify="center" align="center" class="min-vh-100">
      <v-col cols="12" sm="8" md="6" lg="4">
        <v-card class="success-card" elevation="4" rounded="xl">
          <v-card-text class="text-center pa-4">
            <!-- Icono -->
            <div class="mb-3">
              <v-icon size="64" color="success">mdi-check-circle</v-icon>
            </div>

            <h2 class="text-h6 font-weight-bold text-success mb-1">
              ¡Registro Exitoso!
            </h2>

            <p class="text-caption text-medium-emphasis mb-3">
              Tu solicitud ha sido enviada para verificación
            </p>

            <!-- ✅ Mostrar PIN si está disponible -->
            <v-alert v-if="pinGenerado" type="info" class="mb-3" border="start" density="compact">
              <div class="text-caption font-weight-bold">📱 PIN de acceso:</div>
              <div class="text-h4 font-weight-bold text-primary">{{ pinGenerado }}</div>
              <div class="text-caption text-medium-emphasis">Usa este PIN para entrar a la app</div>
            </v-alert>

            <v-alert v-else type="warning" class="mb-3" border="start" density="compact">
              <div class="text-caption font-weight-bold">⏳ Esperando PIN</div>
              <div class="text-caption text-medium-emphasis">Revisa tu WhatsApp/SMS</div>
            </v-alert>

            <v-divider class="my-2" />

            <!-- Pasos -->
            <v-list density="compact" class="bg-transparent text-left">
              <v-list-item>
                <template v-slot:prepend>
                  <v-icon size="16" color="info">mdi-send</v-icon>
                </template>
                <v-list-item-title class="text-caption font-weight-medium">Recibirás un SMS/WhatsApp con tu PIN de acceso</v-list-item-title>
              </v-list-item>
              <v-list-item>
                <template v-slot:prepend>
                  <v-icon size="16" color="warning">mdi-clock</v-icon>
                </template>
                <v-list-item-title class="text-caption font-weight-medium">Verificación en 24-48 horas</v-list-item-title>
              </v-list-item>
            </v-list>

            <v-divider class="my-2" />

            <!-- Datos -->
            <div class="d-flex justify-space-between text-caption py-1">
              <span class="text-medium-emphasis">Tu cédula:</span>
              <span class="font-weight-bold">{{ cedula }}</span>
            </div>
            <div class="d-flex justify-space-between text-caption py-1">
              <span class="text-medium-emphasis">Estado:</span>
              <v-chip color="warning" size="x-small">
                <v-icon size="12" start>mdi-clock-outline</v-icon>
                En verificación
              </v-chip>
            </div>

            <v-divider class="my-2" />

            <v-btn color="primary" rounded="pill" block size="large" @click="irALogin" class="mt-2">
              <v-icon start size="18">mdi-login</v-icon>
              Ir al Login
            </v-btn>

            <p class="text-caption text-medium-emphasis mt-2">
              🔑 Usa tu cédula y el PIN que te enviamos
            </p>
          </v-card-text>
        </v-card>
      </v-col>
    </v-row>
  </v-container>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'

const route = useRoute()
const router = useRouter()
const cedula = route.params.cedula || ''
const pinGenerado = ref(null)

onMounted(() => {
  // Intentar obtener el PIN de localStorage
  const storedPin = localStorage.getItem('financoop_pin_temp')
  if (storedPin) {
    pinGenerado.value = storedPin
    localStorage.removeItem('financoop_pin_temp')
  }
})

const irALogin = () => {
  // Limpiar token residual
  localStorage.removeItem('financoop_token')
  router.push('/login')
}
</script>

<style scoped>
.success-container {
  min-height: 100vh;
  background: #f5f7fa;
  padding: 10px 0;
}

.success-card {
  background: white !important;
  border-radius: 20px !important;
}

:deep(.v-theme--dark) .success-container {
  background: #121212;
}

:deep(.v-theme--dark) .success-card {
  background: #1e1e1e !important;
}
</style>