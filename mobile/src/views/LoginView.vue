<template>
  <div class="login-wrapper">
    <!-- Fondo animado con gradiente y partículas -->
    <div class="login-bg">
      <div class="gradient-sphere sphere-1"></div>
      <div class="gradient-sphere sphere-2"></div>
      <div class="gradient-sphere sphere-3"></div>
    </div>

    <!-- Animación de partículas -->
    <div class="particles">
      <div v-for="i in 15" :key="i" class="particle" :style="{
        left: Math.random() * 100 + '%',
        top: Math.random() * 100 + '%',
        animationDuration: 3 + Math.random() * 5 + 's',
        animationDelay: Math.random() * 3 + 's',
        width: 4 + Math.random() * 6 + 'px',
        height: 4 + Math.random() * 6 + 'px'
      }"></div>
    </div>

    <div class="login-container">
      <v-card class="login-card" elevation="20" rounded="xl">
        <!-- Logo y título -->
        <div class="login-header">
          <div class="logo-wrapper">
            <div class="logo-icon">
              <v-img
                src="/icons/icon-512x512.png"
                width="70"
                height="70"
                class="logo-img"
                contain
              />
            </div>
          </div>
          <h1 class="app-title">FinanCoop</h1>
          <p class="app-subtitle">Cecosesola</p>
          
          <div class="divider-line">
            <span></span>
          </div>
          
          <p class="welcome-text">Bienvenido de vuelta</p>
        </div>

        <!-- Formulario -->
        <div class="login-body">
          <v-form @submit.prevent="handleLogin" class="login-form">
            <div class="input-group">
              <label class="input-label">
                <v-icon size="18" class="label-icon">mdi-card-account-details</v-icon>
                Número de Cédula
              </label>
              <v-text-field
                v-model="loginForm.cedula"
                placeholder="Ej: 12345678"
                variant="solo-filled"
                density="comfortable"
                flat
                rounded="lg"
                bg-color="#f8f9fa"
                class="custom-input"
                @keyup.enter="handleLogin"
              />
            </div>

            <div class="input-group">
              <label class="input-label">
                <v-icon size="18" class="label-icon">mdi-lock</v-icon>
                PIN de Acceso
              </label>
              <v-text-field
                v-model="loginForm.pin"
                placeholder="Ingresa tu PIN"
                type="password"
                variant="solo-filled"
                density="comfortable"
                maxlength="4"
                flat
                rounded="lg"
                bg-color="#f8f9fa"
                class="custom-input"
                @keyup.enter="handleLogin"
              />
            </div>

            <v-alert
              v-if="error"
              type="error"
              class="error-alert"
              density="compact"
              variant="tonal"
              rounded="lg"
            >
              <div class="d-flex align-center">
                <v-icon size="20" class="mr-2">mdi-alert-circle</v-icon>
                {{ error }}
              </div>
            </v-alert>

            <v-btn
              type="submit"
              color="primary"
              block
              size="x-large"
              :loading="cargando"
              class="login-btn"
              elevation="4"
              rounded="xl"
            >
              <v-icon v-if="!cargando" start size="22">mdi-login</v-icon>
              <span v-if="!cargando">Ingresar</span>
              <span v-else>Verificando...</span>
            </v-btn>

            <div class="divider-text">
              <span>o</span>
            </div>

            <v-btn
              color="success"
              block
              size="large"
              class="register-btn"
              elevation="0"
              rounded="xl"
              variant="tonal"
              @click="irARegistro"
            >
              <v-icon start size="20">mdi-account-plus</v-icon>
              Crear cuenta
            </v-btn>

            <div class="footer-text">
              <p>
                <v-icon size="16" class="text-grey">mdi-help-circle</v-icon>
                ¿No tienes PIN? Solicítalo en la Coop. mas Cercana
              </p>
            </div>

            <div class="info-badge">
              <v-icon size="14" color="#78909c">mdi-currency-usd</v-icon>
              <span>Deuda en USD • Pago en Bs al cambio del día</span>
            </div>
          </v-form>
        </div>
      </v-card>

      <!-- Versión -->
      <div class="version-text">
        <span>v2.0 • FinanCoop</span>
      </div>
    </div>
  </div>
</template>

<script setup>
import { useRouter } from 'vue-router'
import { useFinanCash } from '@/composables/useFinanCash'

const { loginForm, error, cargando, iniciarSesion } = useFinanCash()
const router = useRouter()

const handleLogin = async () => {
  console.log('🔑 Intentando login...')
  
  try {
    const success = await iniciarSesion()
    console.log('✅ Resultado login:', success)
    
    if (success) {
      console.log('✅ Login exitoso, navegando a /inicio...')
      await router.replace('/inicio')
    } else {
      console.log('❌ Login falló')
    }
  } catch (err) {
    console.error('❌ Error en login:', err)
  }
}

const irARegistro = () => {
  router.push('/registro')
}
</script>

<style scoped>
/* ============ CONTENEDOR PRINCIPAL ============ */
.login-wrapper {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  position: relative;
  background: #0a0e1a;
  padding: 20px;
}

/* ============ FONDO ANIMADO ============ */
.login-bg {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  overflow: hidden;
  z-index: 0;
  background: linear-gradient(135deg, #0a0e1a 0%, #1a1a2e 30%, #16213e 60%, #0f3460 100%);
}

.gradient-sphere {
  position: absolute;
  border-radius: 50%;
  filter: blur(80px);
  opacity: 0.3;
  animation: floatSphere 20s ease-in-out infinite alternate;
}

.sphere-1 {
  width: 400px;
  height: 400px;
  top: -200px;
  right: -100px;
  background: radial-gradient(circle, #4facfe, #00f2fe);
  animation-delay: 0s;
}

.sphere-2 {
  width: 350px;
  height: 350px;
  bottom: -150px;
  left: -100px;
  background: radial-gradient(circle, #a855f7, #6366f1);
  animation-delay: -5s;
}

.sphere-3 {
  width: 200px;
  height: 200px;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  background: radial-gradient(circle, #f472b6, #ec4899);
  animation-delay: -10s;
  opacity: 0.15;
}

@keyframes floatSphere {
  0% { transform: translate(0, 0) scale(1); }
  50% { transform: translate(30px, -30px) scale(1.1); }
  100% { transform: translate(-20px, 20px) scale(0.9); }
}

/* ============ PARTÍCULAS ============ */
.particles {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  z-index: 0;
  pointer-events: none;
  overflow: hidden;
}

.particle {
  position: absolute;
  background: rgba(255,255,255,0.15);
  border-radius: 50%;
  animation: floatParticle linear infinite;
  pointer-events: none;
}

@keyframes floatParticle {
  0% {
    transform: translateY(0) rotate(0deg);
    opacity: 0;
  }
  10% { opacity: 1; }
  90% { opacity: 1; }
  100% {
    transform: translateY(-100vh) rotate(720deg);
    opacity: 0;
  }
}

/* ============ CARD DE LOGIN ============ */
.login-container {
  position: relative;
  z-index: 1;
  width: 100%;
  max-width: 420px;
}

.login-card {
  background: rgba(255,255,255,0.05) !important;
  backdrop-filter: blur(20px) !important;
  -webkit-backdrop-filter: blur(20px) !important;
  border: 1px solid rgba(255,255,255,0.08);
  overflow: hidden;
  padding: 8px;
}

/* ============ HEADER ============ */
.login-header {
  text-align: center;
  padding: 32px 24px 24px;
  position: relative;
}

.logo-wrapper {
  display: flex;
  justify-content: center;
  margin-bottom: 16px;
}

.logo-icon {
  width: 80px;
  height: 80px;
  border-radius: 24px;
  background: linear-gradient(135deg, rgba(79, 172, 254, 0.2), rgba(0, 242, 254, 0.1));
  border: 2px solid rgba(79, 172, 254, 0.2);
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 12px;
  animation: pulseGlow 3s ease-in-out infinite;
}

@keyframes pulseGlow {
  0%, 100% { box-shadow: 0 0 20px rgba(79, 172, 254, 0.1); }
  50% { box-shadow: 0 0 40px rgba(79, 172, 254, 0.2); }
}

.logo-img {
  border-radius: 12px;
}

.app-title {
  font-size: 28px;
  font-weight: 700;
  color: #ffffff;
  letter-spacing: -0.5px;
  margin: 0;
  background: linear-gradient(135deg, #ffffff, #94a3b8);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.app-subtitle {
  font-size: 13px;
  color: rgba(255,255,255,0.5);
  letter-spacing: 3px;
  text-transform: uppercase;
  margin: 4px 0 0;
}

.divider-line {
  width: 40px;
  height: 2px;
  background: linear-gradient(90deg, transparent, rgba(79, 172, 254, 0.5), transparent);
  margin: 16px auto 12px;
}

.welcome-text {
  font-size: 14px;
  color: rgba(255,255,255,0.6);
  margin: 0;
}

/* ============ BODY ============ */
.login-body {
  padding: 0 20px 28px;
}

.login-form {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.input-group {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.input-label {
  font-size: 12px;
  font-weight: 600;
  color: rgba(255,255,255,0.7);
  display: flex;
  align-items: center;
  gap: 6px;
  letter-spacing: 0.3px;
  text-transform: uppercase;
}

.label-icon {
  color: rgba(79, 172, 254, 0.6);
}

.custom-input {
  background: rgba(255,255,255,0.04) !important;
  border-radius: 12px !important;
  transition: all 0.3s ease;
}

.custom-input :deep(.v-field) {
  background: rgba(255,255,255,0.04) !important;
  border-radius: 12px !important;
  transition: all 0.3s ease;
}

.custom-input :deep(.v-field:hover) {
  background: rgba(255,255,255,0.08) !important;
}

.custom-input :deep(.v-field--focused) {
  background: rgba(255,255,255,0.06) !important;
  box-shadow: 0 0 0 2px rgba(79, 172, 254, 0.15);
}

.custom-input :deep(.v-field__input) {
  color: #ffffff !important;
  padding: 8px 16px !important;
}

.custom-input :deep(.v-field__input::placeholder) {
  color: rgba(255,255,255,0.3) !important;
}

.custom-input :deep(.v-icon) {
  color: rgba(255,255,255,0.3) !important;
}

/* ============ BOTONES ============ */
.login-btn {
  background: linear-gradient(135deg, #4facfe, #6366f1) !important;
  border: none !important;
  font-weight: 700;
  font-size: 16px;
  letter-spacing: 0.5px;
  height: 56px;
  transition: all 0.3s ease;
  position: relative;
  overflow: hidden;
}

.login-btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 30px rgba(79, 172, 254, 0.4) !important;
}

.login-btn:active {
  transform: scale(0.98);
}

.register-btn {
  background: rgba(255,255,255,0.06) !important;
  color: #ffffff !important;
  font-weight: 600;
  height: 48px;
  border: 1px solid rgba(255,255,255,0.08);
  transition: all 0.3s ease;
}

.register-btn:hover {
  background: rgba(255,255,255,0.1) !important;
  border-color: rgba(255,255,255,0.15);
}

/* ============ DIVISOR ============ */
.divider-text {
  display: flex;
  align-items: center;
  text-align: center;
  margin: 4px 0;
}

.divider-text::before,
.divider-text::after {
  content: '';
  flex: 1;
  border-bottom: 1px solid rgba(255,255,255,0.06);
}

.divider-text span {
  color: rgba(255,255,255,0.3);
  font-size: 12px;
  padding: 0 16px;
  text-transform: uppercase;
  letter-spacing: 1px;
}

/* ============ ERROR ============ */
.error-alert {
  background: rgba(239, 68, 68, 0.1) !important;
  border: 1px solid rgba(239, 68, 68, 0.15);
  color: #f87171 !important;
  border-radius: 12px !important;
  padding: 8px 12px !important;
}

/* ============ FOOTER ============ */
.footer-text {
  text-align: center;
  margin-top: 4px;
}

.footer-text p {
  font-size: 12px;
  color: rgba(255,255,255,0.35);
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 4px;
}

.footer-text .v-icon {
  color: rgba(255,255,255,0.25);
}

.info-badge {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  padding: 8px 16px;
  background: rgba(255,255,255,0.03);
  border-radius: 20px;
  font-size: 10px;
  color: rgba(255,255,255,0.3);
  margin-top: 4px;
  border: 1px solid rgba(255,255,255,0.04);
}

.version-text {
  text-align: center;
  margin-top: 20px;
  font-size: 11px;
  color: rgba(255,255,255,0.15);
  letter-spacing: 1px;
}

/* ============ RESPONSIVE ============ */
@media (max-width: 480px) {
  .login-wrapper {
    padding: 12px;
  }
  
  .login-header {
    padding: 24px 16px 16px;
  }
  
  .login-body {
    padding: 0 16px 20px;
  }
  
  .logo-icon {
    width: 64px;
    height: 64px;
    padding: 10px;
  }
  
  .app-title {
    font-size: 24px;
  }
  
  .login-btn {
    height: 50px;
    font-size: 15px;
  }
  
  .register-btn {
    height: 44px;
    font-size: 13px;
  }
}

@media (max-height: 700px) {
  .login-header {
    padding: 16px 16px 12px;
  }
  
  .logo-icon {
    width: 56px;
    height: 56px;
    padding: 8px;
    margin-bottom: 8px;
  }
  
  .app-title {
    font-size: 20px;
  }
  
  .divider-line {
    margin: 8px auto;
  }
  
  .welcome-text {
    font-size: 12px;
  }
  
  .login-body {
    padding: 0 16px 16px;
    gap: 12px;
  }
  
  .login-form {
    gap: 12px;
  }
  
  .login-btn {
    height: 44px;
  }
  
  .register-btn {
    height: 40px;
    font-size: 12px;
  }
}

/* ============ TEMA OSCURO (opcional) ============ */
@media (prefers-color-scheme: dark) {
  .login-card {
    background: rgba(10, 14, 26, 0.8) !important;
  }
}
</style>