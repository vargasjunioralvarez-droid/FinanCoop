<template>
  <v-container class="fill-height login-bg d-flex align-center justify-center">
    <div class="login-decoration">
      <div class="circle circle-1"></div>
      <div class="circle circle-2"></div>
      <div class="circle circle-3"></div>
    </div>

    <v-card max-width="380" width="100%" class="login-card pa-0" elevation="12">
      <div class="login-header text-center py-8">
        <div class="app-icon-wrapper">
          <v-img
            src="/icons/icon-512x512.png"
            width="72"
            height="72"
            class="app-logo"
            contain
          />
        </div>
        <h1 class="text-h4 mt-4 font-weight-bold text-white">FinanCoop</h1>
        <p class="text-body-2 text-white text-opacity-70 mt-1">Cecosesola</p>
      </div>

      <v-card-text class="pa-6 pt-8">
        <v-text-field
          v-model="loginForm.cedula"
          label="Cédula"
          prepend-inner-icon="mdi-card-account-details"
          variant="outlined"
          density="comfortable"
          class="mb-4"
          bg-color="surface"
          @keyup.enter="handleLogin"
          hide-details
        />

        <v-text-field
          v-model="loginForm.pin"
          label="PIN"
          type="password"
          prepend-inner-icon="mdi-lock"
          maxlength="4"
          variant="outlined"
          density="comfortable"
          class="mb-6"
          bg-color="surface"
          @keyup.enter="handleLogin"
          hide-details
        />

        <v-alert v-if="error" type="error" class="mb-4" density="compact" variant="tonal">
          {{ error }}
        </v-alert>

        <v-btn 
          color="primary" 
          @click="handleLogin" 
          block 
          size="x-large"
          :loading="cargando"
          elevation="4"
          class="login-btn"
          rounded="pill"
        >
          <v-icon start>mdi-login</v-icon>
          Ingresar
        </v-btn>

        <div class="text-center mt-6">
          <p class="text-caption text-grey">
            ¿No tienes PIN? Solicítalo en tu tienda afiliada
          </p>
        </div>

        <div class="text-center mt-4 text-caption text-medium-emphasis">
          Tu deuda se mantiene en USD • Pagas en Bs al tipo de cambio del día
        </div>
      </v-card-text>
    </v-card>
  </v-container>
</template>

<script setup>
import { useFinanCash } from '@/composables/useFinanCash'

const { loginForm, error, cargando, iniciarSesion } = useFinanCash()

const emit = defineEmits(['login-success'])

const handleLogin = async () => {
  const success = await iniciarSesion()
  if (success) emit('login-success')
}
</script>

<style scoped>
.login-bg {
  background: linear-gradient(135deg, #1565c0 0%, #0d47a1 50%, #1a237e 100%);
  position: relative;
  overflow: hidden;
  min-height: 100vh;
}

.login-decoration {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  overflow: hidden;
}

.circle {
  position: absolute;
  border-radius: 50%;
  background: rgba(255,255,255,0.05);
}

.circle-1 {
  width: 300px;
  height: 300px;
  top: -100px;
  right: -100px;
}

.circle-2 {
  width: 200px;
  height: 200px;
  bottom: -50px;
  left: -50px;
}

.circle-3 {
  width: 150px;
  height: 150px;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
}

.login-card {
  border-radius: 24px;
  overflow: hidden;
  z-index: 1;
}

.login-header {
  background: linear-gradient(135deg, #1976d2, #1565c0);
  position: relative;
}

.app-icon-wrapper {
  width: 100px;
  height: 100px;
  border-radius: 28px;
  background: rgba(255,255,255,0.15);
  backdrop-filter: blur(10px);
  display: flex;
  align-items: center;
  justify-content: center;
  margin: 0 auto;
  border: 2px solid rgba(255,255,255,0.3);
  overflow: hidden;
}

.app-logo {
  border-radius: 12px;
}

.login-btn {
  border-radius: 12px;
  font-weight: 600;
  letter-spacing: 0.5px;
}
</style>