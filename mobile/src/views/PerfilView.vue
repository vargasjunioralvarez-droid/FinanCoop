<template>
  <div class="perfil-wrapper">
    <div class="bg-gradient"></div>

    <div class="page-content">
      <!-- Header -->
      <v-sheet class="perfil-header" elevation="0">
        <div class="header-content pa-4">
          <div class="text-center">
            <div class="avatar-section">
              <v-avatar size="80" :color="colorNivel(datosCliente?.cliente?.nivel || usuario.nivel)" class="avatar-main">
                <v-icon size="40" color="white">{{ iconoNivel(datosCliente?.cliente?.nivel || usuario.nivel) }}</v-icon>
              </v-avatar>
              <v-chip :color="colorNivel(datosCliente?.cliente?.nivel || usuario.nivel)" size="x-small" class="level-chip" text-color="white">
                <v-icon size="12" start>{{ iconoNivel(datosCliente?.cliente?.nivel || usuario.nivel) }}</v-icon>
                {{ datosCliente?.cliente?.nivel || usuario.nivel || 'Nuevo' }}
              </v-chip>
            </div>

            <h2 class="perfil-name">{{ datosCliente?.cliente?.nombre || usuario.nombre || 'Cargando...' }}</h2>
            
            <div class="d-flex align-center justify-center gap-2 mt-1">
              <span class="perfil-score">
                <v-icon size="14" color="white" class="mr-1">mdi-star</v-icon>
                {{ datosCliente?.cliente?.score || usuario.score || 0 }} pts
              </span>
              <span class="perfil-divider">•</span>
              <span class="perfil-id">ID: {{ datosCliente?.cliente?.cedula || usuario.cedula || '---' }}</span>
            </div>

            <v-chip v-if="datosCliente?.cliente?.aprobado === false" color="warning" size="x-small" class="mt-2">
              <v-icon size="12" start>mdi-clock-outline</v-icon>
              En verificación
            </v-chip>
            <v-chip v-else-if="datosCliente?.cliente?.aprobado === true" color="success" size="x-small" class="mt-2">
              <v-icon size="12" start>mdi-check-circle</v-icon>
              Verificado
            </v-chip>
          </div>
        </div>
      </v-sheet>

      <!-- Stats -->
      <v-container class="mt-n4" fluid>
        <v-row dense no-gutters class="px-3">
          <v-col cols="4">
            <v-card class="stat-card glass-card" elevation="0">
              <div class="pa-3 text-center">
                <div class="stat-number text-primary">{{ financiamientos?.length || 0 }}</div>
                <div class="stat-label">Compras</div>
              </div>
            </v-card>
          </v-col>
          <v-col cols="4">
            <v-card class="stat-card glass-card" elevation="0">
              <div class="pa-3 text-center">
                <div class="stat-number text-success">${{ lineaUsada || '0' }}</div>
                <div class="stat-label">Usado</div>
              </div>
            </v-card>
          </v-col>
          <v-col cols="4">
            <v-card class="stat-card glass-card" elevation="0">
              <div class="pa-3 text-center">
                <div class="stat-number text-warning">{{ nivelActual?.cuotas_max || 0 }}</div>
                <div class="stat-label">Cuotas max</div>
              </div>
            </v-card>
          </v-col>
        </v-row>
      </v-container>

      <!-- Datos -->
      <v-card class="section-card glass-card" elevation="0">
        <div class="section-header">
          <div class="d-flex align-center">
            <v-icon color="#4facfe" size="20" class="mr-2">mdi-account</v-icon>
            <span>Datos Personales</span>
          </div>
          <v-chip size="x-small" color="success" variant="tonal">Verificado</v-chip>
        </div>
        <v-divider style="border-color: rgba(255,255,255,0.06);" />
        <div class="pa-3">
          <div class="info-field"><div class="field-label">Nombre completo</div><div class="field-value">{{ datosCliente?.cliente?.nombre || 'No registrado' }}</div></div>
          <div class="info-field"><div class="field-label">Cédula</div><div class="field-value">{{ datosCliente?.cliente?.cedula || 'No registrada' }}</div></div>
          <div class="info-field"><div class="field-label">Teléfono</div><div class="field-value">{{ datosCliente?.cliente?.telefono || 'No registrado' }}</div></div>
          <div class="info-field"><div class="field-label">Email</div><div class="field-value">{{ datosCliente?.cliente?.email || 'No registrado' }}</div></div>
          <div class="info-field"><div class="field-label">Dirección</div><div class="field-value">{{ datosCliente?.cliente?.direccion || 'No registrada' }}</div></div>
        </div>
      </v-card>

      <!-- Referencia -->
      <v-card class="section-card glass-card" elevation="0">
        <div class="section-header">
          <div class="d-flex align-center">
            <v-icon color="#4facfe" size="20" class="mr-2">mdi-account-group</v-icon>
            <span>Referencia Personal</span>
          </div>
        </div>
        <v-divider style="border-color: rgba(255,255,255,0.06);" />
        <div class="pa-3">
          <div class="info-field"><div class="field-label">Nombre de referencia</div><div class="field-value">{{ datosCliente?.cliente?.referencia_nombre || 'No registrada' }}</div></div>
          <div class="info-field"><div class="field-label">Teléfono de referencia</div><div class="field-value">{{ datosCliente?.cliente?.referencia_telefono || 'No registrado' }}</div></div>
          <div class="info-field"><div class="field-label">Parentesco</div><div class="field-value">{{ datosCliente?.cliente?.referencia_parentesco || 'No registrado' }}</div></div>
        </div>
      </v-card>

      <!-- Documento -->
      <v-card class="section-card glass-card" elevation="0">
        <div class="section-header">
          <div class="d-flex align-center">
            <v-icon color="#4facfe" size="20" class="mr-2">mdi-card-account-details</v-icon>
            <span>Documento de Identidad</span>
          </div>
          <v-chip v-if="datosCliente?.cliente?.cedula_foto" size="x-small" color="success" variant="tonal">
            <v-icon size="12" start>mdi-check-circle</v-icon>Verificado
          </v-chip>
          <v-chip v-else size="x-small" color="warning" variant="tonal">
            <v-icon size="12" start>mdi-alert</v-icon>Pendiente
          </v-chip>
        </div>
        <v-divider style="border-color: rgba(255,255,255,0.06);" />
        <div class="pa-4">
          <div v-if="datosCliente?.cliente?.cedula_foto" class="text-center">
            <v-img :src="datosCliente.cliente.cedula_foto" max-height="200" contain class="rounded-lg mb-2" />
            <div class="text-caption text-success"><v-icon size="14" start>mdi-check-circle</v-icon>Documento verificado</div>
          </div>
          <div v-else class="text-center py-4">
            <v-icon size="48" color="rgba(255,255,255,0.1)" class="mb-2">mdi-camera</v-icon>
            <div class="text-body-2 text-medium-emphasis">Aún no has subido tu cédula</div>
            <div class="text-caption text-medium-emphasis mt-1">Completa tu registro en la app</div>
          </div>
        </div>
      </v-card>

      <!-- Configuración -->
      <v-card class="section-card glass-card" elevation="0">
        <div class="section-header">
          <div class="d-flex align-center">
            <v-icon color="#4facfe" size="20" class="mr-2">mdi-cog</v-icon>
            <span>Configuración</span>
          </div>
        </div>
        <v-divider style="border-color: rgba(255,255,255,0.06);" />
        <div class="settings-list">
          <div class="setting-item" @click="cambiarPin = true">
            <div class="d-flex align-center"><v-icon color="#4facfe" size="20" class="mr-3">mdi-lock-reset</v-icon><span>Cambiar PIN</span></div>
            <v-icon size="20" color="rgba(255,255,255,0.2)">mdi-chevron-right</v-icon>
          </div>
          <v-divider style="border-color: rgba(255,255,255,0.06);" />
          <div class="setting-item">
            <div class="d-flex align-center"><v-icon color="#4facfe" size="20" class="mr-3">mdi-bell</v-icon><span>Notificaciones</span></div>
            <v-switch v-model="notificacionesActivas" hide-details density="compact" color="#4facfe" />
          </div>
          <v-divider style="border-color: rgba(255,255,255,0.06);" />
          <div class="setting-item">
            <div class="d-flex align-center"><v-icon color="#4facfe" size="20" class="mr-3">mdi-theme-light-dark</v-icon><span>Tema oscuro</span></div>
            <v-switch v-model="temaOscuro" hide-details density="compact" color="#4facfe" />
          </div>
        </div>
      </v-card>

      <!-- Info app -->
      <v-card class="app-info glass-card" elevation="0">
        <div class="pa-4 text-center">
          <v-img src="/icons/icon-192x192.png" width="40" height="40" class="mx-auto mb-2" contain />
          <div class="app-version">FinanCoop v1.0</div>
          <div class="app-sub">Cecosesola</div>
          <div class="app-desc">Tu deuda en USD • Pagas en Bs</div>
        </div>
      </v-card>

      <!-- Cerrar sesión -->
      <v-btn block color="error" variant="tonal" rounded="pill" size="large" class="logout-btn" @click="cerrarSesion">
        <v-icon start>mdi-logout</v-icon>Cerrar sesión
      </v-btn>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, watch } from 'vue'
import { useRouter } from 'vue-router'
import { useTheme } from 'vuetify'
import { useFinanCash } from '@/composables/useFinanCash'

const router = useRouter()
const theme = useTheme()

const { 
  token, 
  datosCliente,
  usuario,
  financiamientos,
  nivelActual,
  lineaUsada,
  colorNivel,
  iconoNivel,
  cargarDatos,
  cerrarSesion
} = useFinanCash()

const cambiarPin = ref(false)
const notificacionesActivas = ref(true)
const temaOscuro = ref(false)

watch(temaOscuro, (val) => {
  theme.global.name.value = val ? 'dark' : 'light'
  localStorage.setItem('temaOscuro', JSON.stringify(val))
})

onMounted(() => {
  const temaGuardado = localStorage.getItem('temaOscuro')
  if (temaGuardado) temaOscuro.value = JSON.parse(temaGuardado)
  if (!datosCliente.value && token.value) cargarDatos()
})
</script>

<style scoped>
.perfil-wrapper {
  min-height: 100vh;
  background: #0a0e1a;
  position: relative;
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
  padding: 0 16px 80px;
}

.glass-card {
  background: rgba(255,255,255,0.04) !important;
  backdrop-filter: blur(12px) !important;
  -webkit-backdrop-filter: blur(12px) !important;
  border: 1px solid rgba(255,255,255,0.06);
  border-radius: 16px !important;
}

.perfil-header {
  background: linear-gradient(135deg, #1a237e 0%, #0d47a1 100%);
  border-radius: 0 0 30px 30px;
  margin: 0 -16px 16px;
  padding: 0 16px;
}

.header-content {
  position: relative;
  z-index: 1;
  padding: 24px 0 20px;
}

.avatar-section {
  position: relative;
  display: inline-block;
}

.avatar-main {
  border: 3px solid rgba(255,255,255,0.4);
  box-shadow: 0 8px 32px rgba(0,0,0,0.2);
}

.level-chip {
  position: absolute;
  bottom: -4px;
  right: -4px;
  font-weight: bold;
  padding: 0 8px;
  border: 2px solid #0d47a1;
}

.perfil-name {
  font-size: 20px;
  font-weight: 700;
  color: #ffffff;
  margin-top: 8px;
}

.perfil-score {
  font-size: 12px;
  color: rgba(255,255,255,0.7);
}

.perfil-divider {
  color: rgba(255,255,255,0.3);
}

.perfil-id {
  font-size: 12px;
  color: rgba(255,255,255,0.5);
}

.stat-card {
  transition: transform 0.2s ease;
}

.stat-card:active {
  transform: scale(0.96);
}

.stat-number {
  font-size: 20px;
  font-weight: 700;
}

.stat-number.text-primary { color: #4facfe; }
.stat-number.text-success { color: #4caf50; }
.stat-number.text-warning { color: #ffd54f; }

.stat-label {
  font-size: 11px;
  color: rgba(255,255,255,0.4);
}

.section-card {
  margin-bottom: 12px;
  overflow: hidden;
}

.section-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 10px 16px;
  background: rgba(79, 172, 254, 0.04);
}

.section-header span {
  font-size: 13px;
  font-weight: 600;
  color: #ffffff;
}

.info-field {
  padding: 6px 0;
  border-bottom: 1px solid rgba(255,255,255,0.04);
}

.info-field:last-child {
  border-bottom: none;
}

.field-label {
  font-size: 10px;
  color: rgba(255,255,255,0.3);
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.field-value {
  font-size: 14px;
  font-weight: 500;
  color: #ffffff;
}

.settings-list {
  padding: 4px 0;
}

.setting-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 10px 16px;
  cursor: pointer;
  transition: background 0.2s;
  color: rgba(255,255,255,0.7);
}

.setting-item:hover {
  background: rgba(255,255,255,0.04);
}

.setting-item span {
  font-size: 13px;
}

.app-info {
  margin-bottom: 16px;
}

.app-version {
  font-size: 14px;
  font-weight: 600;
  color: #ffffff;
}

.app-sub {
  font-size: 12px;
  color: rgba(255,255,255,0.3);
}

.app-desc {
  font-size: 11px;
  color: rgba(255,255,255,0.2);
  margin-top: 4px;
}

.logout-btn {
  background: rgba(239, 68, 68, 0.1) !important;
  color: #f87171 !important;
  border: 1px solid rgba(239, 68, 68, 0.15);
  margin-top: 8px;
}

.logout-btn:hover {
  background: rgba(239, 68, 68, 0.15) !important;
}
</style>