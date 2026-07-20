<template>
  <v-container fluid class="pa-0 login-container">
    <!-- ✅ FONDO MODERNO CON ANIMACIÓN -->
    <div class="login-bg"></div>
    <div class="login-overlay"></div>
    
    <!-- ✅ PARTÍCULAS DECORATIVAS -->
    <div class="particles">
      <div v-for="i in 8" :key="i" class="particle" :style="`--i: ${i}; animation-delay: ${i * 0.5}s;`"></div>
    </div>

    <v-row align="center" justify="center" class="fill-height ma-0">
      <v-col cols="12" sm="8" md="5" lg="4" xl="3">
        <v-card class="login-card glass-card rounded-xl" elevation="0">
          <!-- ✅ LOGO Y TÍTULO -->
          <div class="login-header text-center">
            <div class="logo-wrapper pulse-animation">
              <v-icon size="48" color="#4facfe">mdi-finance</v-icon>
            </div>
            <h1 class="login-title text-white">FinanCoop</h1>
            <p class="login-sub" style="color: rgba(255,255,255,0.5);">Sistema de Administración</p>
          </div>

          <v-divider class="my-3" style="border-color: rgba(255,255,255,0.06);"></v-divider>

          <v-card-text class="pa-4">
            <v-form @submit.prevent="login" class="login-form">
              <!-- ✅ USUARIO -->
              <div class="field-wrapper">
                <label class="field-label text-white">
                  <v-icon size="16" class="label-icon">mdi-account</v-icon>
                  Usuario
                </label>
                <v-text-field
                  v-model="username"
                  placeholder="Ingresa tu usuario"
                  variant="outlined"
                  density="comfortable"
                  required
                  autocomplete="username"
                  class="custom-input"
                  bg-color="rgba(255,255,255,0.05)"
                />
              </div>

              <!-- ✅ CONTRASEÑA -->
              <div class="field-wrapper mt-3">
                <label class="field-label text-white">
                  <v-icon size="16" class="label-icon">mdi-lock</v-icon>
                  Contraseña
                </label>
                <v-text-field
                  v-model="password"
                  placeholder="Ingresa tu contraseña"
                  :type="showPassword ? 'text' : 'password'"
                  variant="outlined"
                  density="comfortable"
                  required
                  autocomplete="current-password"
                  class="custom-input"
                  bg-color="rgba(255,255,255,0.05)"
                >
                  <template v-slot:append-inner>
                    <v-icon
                      @click="showPassword = !showPassword"
                      :color="showPassword ? '#4facfe' : 'rgba(255,255,255,0.3)'"
                      style="cursor: pointer;"
                    >
                      {{ showPassword ? 'mdi-eye' : 'mdi-eye-off' }}
                    </v-icon>
                  </template>
                </v-text-field>
              </div>

              <!-- ✅ BOTÓN LOGIN -->
              <v-btn
                type="submit"
                color="#4facfe"
                block
                size="x-large"
                :loading="cargando"
                class="btn-login rounded-xl mt-4"
                elevation="0"
              >
                <span class="font-weight-bold" v-if="!cargando">
                  <v-icon start>mdi-login</v-icon>
                  Ingresar al Sistema
                </span>
                <span v-else>Verificando credenciales...</span>
              </v-btn>

              <!-- ✅ MENSAJE DE ERROR -->
              <div v-if="errorMsg" class="mt-3">
                <v-alert type="error" variant="tonal" class="rounded-xl" border="start">
                  <v-icon start>mdi-alert-circle</v-icon>
                  {{ errorMsg }}
                </v-alert>
              </div>
            </v-form>
          </v-card-text>

          <!-- ✅ FOOTER -->
          <v-card-actions class="justify-center pb-4">
            <span class="text-caption" style="color: rgba(255,255,255,0.3);">
              <v-icon size="14" color="rgba(255,255,255,0.2)">mdi-shield-check</v-icon>
              Acceso solo para personal autorizado
            </span>
          </v-card-actions>
        </v-card>

        <!-- ✅ VERSIÓN -->
        <div class="text-center mt-3">
          <span class="text-caption" style="color: rgba(255,255,255,0.15);">v4.0.0 — FinanCoop</span>
        </div>
      </v-col>
    </v-row>
  </v-container>
</template>

<script setup>
import { ref } from 'vue'
import { useAuthStore } from '@/stores/auth'

const auth = useAuthStore()
const username = ref('')
const password = ref('')
const cargando = ref(false)
const errorMsg = ref('')
const showPassword = ref(false)

const login = async () => {
  if (!username.value || !password.value) {
    errorMsg.value = 'Ingresa usuario y contraseña'
    return
  }

  errorMsg.value = ''
  cargando.value = true

  try {
    const data = await auth.login(username.value, password.value)
    
    // ✅ Redirección según rol
    const redirectMap = {
      admin_central: '/usuarios',
      admin_tienda: '/inicio',
      tienda: '/inicio',
      cajero: '/cajero'
    }
    
    const redirect = redirectMap[data.rol] || '/cajero'
    window.location.href = redirect
    
  } catch (error) {
    const mensaje = error.response?.data?.detail || 'Error de conexión con el servidor'
    errorMsg.value = mensaje
  } finally {
    cargando.value = false
  }
}
</script>

<style scoped>
/* ✅ CONTENEDOR PRINCIPAL */
.login-container {
  position: relative;
  min-height: 100vh;
  background: #0a0e1a;
}

/* ✅ FONDO CON GRADIENTES */
.login-bg {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: radial-gradient(ellipse at 20% 50%, rgba(79, 172, 254, 0.15), transparent 70%),
              radial-gradient(ellipse at 80% 50%, rgba(99, 102, 241, 0.1), transparent 70%);
  z-index: 0;
}

.login-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: radial-gradient(ellipse at center, transparent 30%, rgba(10, 14, 26, 0.6));
  z-index: 0;
}

/* ✅ PARTÍCULAS DECORATIVAS */
.particles {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  z-index: 0;
  overflow: hidden;
  pointer-events: none;
}

.particle {
  position: absolute;
  width: 4px;
  height: 4px;
  background: rgba(79, 172, 254, 0.3);
  border-radius: 50%;
  animation: float-particle 8s infinite;
}

.particle:nth-child(1) { top: 10%; left: 5%; animation-duration: 10s; }
.particle:nth-child(2) { top: 20%; left: 90%; animation-duration: 12s; }
.particle:nth-child(3) { top: 60%; left: 10%; animation-duration: 8s; }
.particle:nth-child(4) { top: 80%; left: 85%; animation-duration: 14s; }
.particle:nth-child(5) { top: 40%; left: 95%; animation-duration: 9s; }
.particle:nth-child(6) { top: 70%; left: 5%; animation-duration: 11s; }
.particle:nth-child(7) { top: 15%; left: 50%; animation-duration: 13s; }
.particle:nth-child(8) { top: 90%; left: 50%; animation-duration: 7s; }

@keyframes float-particle {
  0%, 100% { transform: translate(0, 0) scale(1); opacity: 0.3; }
  25% { transform: translate(20px, -30px) scale(1.5); opacity: 0.6; }
  50% { transform: translate(-10px, -50px) scale(0.8); opacity: 0.4; }
  75% { transform: translate(30px, -20px) scale(1.2); opacity: 0.7; }
}

/* ✅ GLASS CARD */
.glass-card {
  background: rgba(255, 255, 255, 0.04) !important;
  backdrop-filter: blur(24px) !important;
  -webkit-backdrop-filter: blur(24px) !important;
  border: 1px solid rgba(255, 255, 255, 0.06) !important;
}

.login-card {
  position: relative;
  z-index: 1;
  padding: 8px;
}

/* ✅ LOGO Y TÍTULO */
.login-header {
  padding: 16px 0 8px;
}

.logo-wrapper {
  width: 72px;
  height: 72px;
  margin: 0 auto;
  background: rgba(79, 172, 254, 0.1);
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  border: 2px solid rgba(79, 172, 254, 0.2);
}

.pulse-animation {
  animation: pulse-logo 2s ease-in-out infinite;
}

@keyframes pulse-logo {
  0%, 100% { transform: scale(1); }
  50% { transform: scale(1.05); }
}

.login-title {
  font-size: 28px;
  font-weight: 800;
  margin-top: 8px;
  background: linear-gradient(135deg, #4facfe, #6366f1);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.login-sub {
  font-size: 14px;
  margin-top: -4px;
}

/* ✅ CAMPOS DE FORMULARIO */
.field-wrapper {
  margin-bottom: 4px;
}

.field-label {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 13px;
  font-weight: 600;
  margin-bottom: 4px;
  padding-left: 4px;
  letter-spacing: 0.3px;
  opacity: 0.8;
}

.label-icon {
  color: #4facfe !important;
  opacity: 0.7;
}

.custom-input :deep(.v-field) {
  border-radius: 12px !important;
  border: 1px solid rgba(255, 255, 255, 0.1) !important;
  transition: all 0.3s ease !important;
}

.custom-input :deep(.v-field:hover) {
  border-color: rgba(255, 255, 255, 0.2) !important;
}

.custom-input :deep(.v-field--focused) {
  border-color: #4facfe !important;
  box-shadow: 0 0 0 3px rgba(79, 172, 254, 0.15) !important;
}

.custom-input :deep(.v-field__input) {
  color: #ffffff !important;
  padding-top: 8px !important;
  padding-bottom: 8px !important;
}

.custom-input :deep(.v-field__input::placeholder) {
  color: rgba(255, 255, 255, 0.3) !important;
  font-weight: 400 !important;
  font-size: 14px !important;
  opacity: 1 !important;
}

.custom-input :deep(.v-field__prepend-inner > .v-icon) {
  color: rgba(255, 255, 255, 0.3) !important;
}

/* ✅ BOTÓN LOGIN */
.btn-login {
  background: linear-gradient(135deg, #4facfe 0%, #6366f1 100%) !important;
  color: white !important;
  font-weight: 700 !important;
  font-size: 16px !important;
  letter-spacing: 0.5px !important;
  text-transform: none !important;
  transition: all 0.3s ease !important;
  height: 52px !important;
}

.btn-login:hover {
  transform: translateY(-3px) !important;
  box-shadow: 0 8px 32px rgba(79, 172, 254, 0.4) !important;
}

.btn-login:active {
  transform: scale(0.97) !important;
}

/* ✅ RESPONSIVE */
@media (max-width: 600px) {
  .login-title {
    font-size: 24px;
  }
  
  .logo-wrapper {
    width: 60px;
    height: 60px;
  }
  
  .logo-wrapper .v-icon {
    font-size: 36px !important;
  }
  
  .login-card {
    margin: 16px;
  }
}
</style>