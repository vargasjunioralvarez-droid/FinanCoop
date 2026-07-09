<template>
  <div class="perfil-container">
    <!-- Header con gradiente -->
    <v-sheet class="perfil-header" elevation="0">
      <div class="header-content pa-4">
        <div class="text-center">
          <div class="avatar-section">
            <v-avatar size="80" :color="colorNivel(datosCliente?.cliente?.nivel || usuario.nivel)" class="avatar-main">
              <v-icon size="40" color="white">{{ iconoNivel(datosCliente?.cliente?.nivel || usuario.nivel) }}</v-icon>
            </v-avatar>
            <v-chip
              :color="colorNivel(datosCliente?.cliente?.nivel || usuario.nivel)"
              size="x-small"
              class="level-chip"
              text-color="white"
            >
              <v-icon size="12" start>{{ iconoNivel(datosCliente?.cliente?.nivel || usuario.nivel) }}</v-icon>
              {{ datosCliente?.cliente?.nivel || usuario.nivel || 'Nuevo' }}
            </v-chip>
          </div>

          <h2 class="text-h6 font-weight-bold text-white mt-2">
            {{ datosCliente?.cliente?.nombre || usuario.nombre || 'Cargando...' }}
          </h2>
          
          <div class="d-flex align-center justify-center gap-2 mt-1">
            <span class="text-white text-opacity-90 text-caption">
              <v-icon size="14" color="white" class="mr-1">mdi-star</v-icon>
              {{ datosCliente?.cliente?.score || usuario.score || 0 }} pts
            </span>
            <span class="text-white text-opacity-60">•</span>
            <span class="text-white text-opacity-70 text-caption">
              ID: {{ datosCliente?.cliente?.cedula || usuario.cedula || '---' }}
            </span>
          </div>

          <!-- Estado de verificación -->
          <v-chip
            v-if="datosCliente?.cliente?.aprobado === false"
            color="warning"
            size="x-small"
            class="mt-2"
          >
            <v-icon size="12" start>mdi-clock-outline</v-icon>
            En verificación
          </v-chip>
          <v-chip
            v-else-if="datosCliente?.cliente?.aprobado === true"
            color="success"
            size="x-small"
            class="mt-2"
          >
            <v-icon size="12" start>mdi-check-circle</v-icon>
            Verificado
          </v-chip>
        </div>
      </div>
    </v-sheet>

    <!-- Tarjetas rápidas -->
    <v-container class="mt-n4" fluid>
      <v-row dense no-gutters class="px-3">
        <v-col cols="4">
          <v-card class="stat-card mx-1" elevation="2" rounded="lg">
            <div class="pa-3 text-center">
              <div class="stat-number text-primary">{{ financiamientos?.length || 0 }}</div>
              <div class="stat-label text-caption">Compras</div>
            </div>
          </v-card>
        </v-col>
        <v-col cols="4">
          <v-card class="stat-card mx-1" elevation="2" rounded="lg">
            <div class="pa-3 text-center">
              <div class="stat-number text-success">${{ lineaUsada || '0' }}</div>
              <div class="stat-label text-caption">Usado</div>
            </div>
          </v-card>
        </v-col>
        <v-col cols="4">
          <v-card class="stat-card mx-1" elevation="2" rounded="lg">
            <div class="pa-3 text-center">
              <div class="stat-number text-warning">{{ nivelActual?.cuotas_max || 0 }}</div>
              <div class="stat-label text-caption">Cuotas max</div>
            </div>
          </v-card>
        </v-col>
      </v-row>
    </v-container>

    <!-- Datos Personales (SOLO LECTURA) -->
    <v-card class="mx-3 mt-3 section-card" elevation="0" rounded="lg">
      <div class="section-header px-4 py-2">
        <div class="d-flex align-center">
          <v-icon color="primary" size="20" class="mr-2">mdi-account</v-icon>
          <span class="text-subtitle-2 font-weight-medium">Datos Personales</span>
        </div>
        <v-chip size="x-small" color="success" variant="tonal">Verificado</v-chip>
      </div>
      <v-divider />
      
      <div class="pa-3">
        <div class="info-field">
          <div class="field-label">Nombre completo</div>
          <div class="field-value">{{ datosCliente?.cliente?.nombre || 'No registrado' }}</div>
        </div>

        <div class="info-field">
          <div class="field-label">Cédula</div>
          <div class="field-value">{{ datosCliente?.cliente?.cedula || 'No registrada' }}</div>
        </div>

        <div class="info-field">
          <div class="field-label">Teléfono</div>
          <div class="field-value">{{ datosCliente?.cliente?.telefono || 'No registrado' }}</div>
        </div>

        <div class="info-field">
          <div class="field-label">Email</div>
          <div class="field-value">{{ datosCliente?.cliente?.email || 'No registrado' }}</div>
        </div>

        <div class="info-field">
          <div class="field-label">Dirección</div>
          <div class="field-value">{{ datosCliente?.cliente?.direccion || 'No registrada' }}</div>
        </div>
      </div>
    </v-card>

    <!-- Referencia Personal (SOLO LECTURA) -->
    <v-card class="mx-3 mt-3 section-card" elevation="0" rounded="lg">
      <div class="section-header px-4 py-2">
        <div class="d-flex align-center">
          <v-icon color="primary" size="20" class="mr-2">mdi-account-group</v-icon>
          <span class="text-subtitle-2 font-weight-medium">Referencia Personal</span>
        </div>
      </div>
      <v-divider />
      
      <div class="pa-3">
        <div class="info-field">
          <div class="field-label">Nombre de referencia</div>
          <div class="field-value">{{ datosCliente?.cliente?.referencia_nombre || 'No registrada' }}</div>
        </div>

        <div class="info-field">
          <div class="field-label">Teléfono de referencia</div>
          <div class="field-value">{{ datosCliente?.cliente?.referencia_telefono || 'No registrado' }}</div>
        </div>

        <div class="info-field">
          <div class="field-label">Parentesco</div>
          <div class="field-value">{{ datosCliente?.cliente?.referencia_parentesco || 'No registrado' }}</div>
        </div>
      </div>
    </v-card>

    <!-- Documento (SOLO LECTURA) -->
    <v-card class="mx-3 mt-3 section-card" elevation="0" rounded="lg">
      <div class="section-header px-4 py-2">
        <div class="d-flex align-center">
          <v-icon color="primary" size="20" class="mr-2">mdi-card-account-details</v-icon>
          <span class="text-subtitle-2 font-weight-medium">Documento de Identidad</span>
        </div>
        <v-chip v-if="datosCliente?.cliente?.cedula_foto" size="x-small" color="success" variant="tonal">
          <v-icon size="12" start>mdi-check-circle</v-icon>
          Verificado
        </v-chip>
        <v-chip v-else size="x-small" color="warning" variant="tonal">
          <v-icon size="12" start>mdi-alert</v-icon>
          Pendiente
        </v-chip>
      </div>
      <v-divider />
      
      <div class="pa-4">
        <div v-if="datosCliente?.cliente?.cedula_foto" class="text-center">
          <v-img
            :src="datosCliente.cliente.cedula_foto"
            max-height="200"
            contain
            class="rounded-lg mb-2"
          />
          <div class="text-caption text-success">
            <v-icon size="14" start>mdi-check-circle</v-icon>
            Documento verificado
          </div>
        </div>
        <div v-else class="text-center py-4">
          <v-icon size="48" color="grey-lighten-2" class="mb-2">mdi-camera</v-icon>
          <div class="text-body-2 text-medium-emphasis">
            Aún no has subido tu cédula
          </div>
          <div class="text-caption text-medium-emphasis mt-1">
            Completa tu registro en la app
          </div>
        </div>
      </div>
    </v-card>

    <!-- Configuración -->
    <v-card class="mx-3 mt-3 section-card" elevation="0" rounded="lg">
      <div class="section-header px-4 py-2">
        <div class="d-flex align-center">
          <v-icon color="primary" size="20" class="mr-2">mdi-cog</v-icon>
          <span class="text-subtitle-2 font-weight-medium">Configuración</span>
        </div>
      </div>
      <v-divider />
      
      <div class="settings-list">
        <div class="setting-item" @click="cambiarPin = true">
          <div class="d-flex align-center">
            <v-icon color="primary" size="20" class="mr-3">mdi-lock-reset</v-icon>
            <span class="text-body-2">Cambiar PIN</span>
          </div>
          <v-icon size="20" color="grey">mdi-chevron-right</v-icon>
        </div>

        <v-divider />

        <div class="setting-item">
          <div class="d-flex align-center">
            <v-icon color="primary" size="20" class="mr-3">mdi-bell</v-icon>
            <span class="text-body-2">Notificaciones</span>
          </div>
          <v-switch
            v-model="notificacionesActivas"
            hide-details
            density="compact"
            color="primary"
          />
        </div>

        <v-divider />

        <div class="setting-item">
          <div class="d-flex align-center">
            <v-icon color="primary" size="20" class="mr-3">mdi-theme-light-dark</v-icon>
            <span class="text-body-2">Tema oscuro</span>
          </div>
          <v-switch
            v-model="temaOscuro"
            hide-details
            density="compact"
            color="primary"
          />
        </div>
      </div>
    </v-card>

    <!-- Info app -->
    <v-card class="mx-3 mt-3 app-info-card" elevation="0" rounded="lg">
      <div class="pa-4 text-center">
        <v-img src="/icons/icon-192x192.png" width="40" height="40" class="mx-auto mb-2" contain />
        <div class="text-body-2 font-weight-medium">FinanCoop v1.0</div>
        <div class="text-caption text-medium-emphasis">Cecosesola</div>
        <div class="text-caption text-medium-emphasis mt-1">
          Tu deuda en USD • Pagas en Bs
        </div>
      </div>
    </v-card>

    <!-- Cerrar sesión -->
    <div class="pa-3 mt-2">
      <v-btn
        block
        color="error"
        variant="tonal"
        rounded="pill"
        size="large"
        @click="cerrarSesion"
      >
        <v-icon start>mdi-logout</v-icon>
        Cerrar sesión
      </v-btn>
    </div>

    <div class="pb-6"></div>
  </div>
</template>

<script setup>
import { ref, onMounted, watch, computed } from 'vue'
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
  cargarDatos
} = useFinanCash()

const cambiarPin = ref(false)
const notificacionesActivas = ref(true)
const temaOscuro = ref(false)

const cerrarSesion = () => {
  localStorage.removeItem('token')
  token.value = null
  router.push('/login')
}

watch(temaOscuro, (val) => {
  theme.global.name.value = val ? 'dark' : 'light'
  localStorage.setItem('temaOscuro', JSON.stringify(val))
})

onMounted(() => {
  const temaGuardado = localStorage.getItem('temaOscuro')
  if (temaGuardado) {
    temaOscuro.value = JSON.parse(temaGuardado)
  }
  
  // Cargar datos si no están cargados
  if (!datosCliente.value && token.value) {
    cargarDatos()
  }
})
</script>

<style scoped>
.perfil-container {
  background: #f5f7fa;
  min-height: 100vh;
  padding-bottom: env(safe-area-inset-bottom);
}

.perfil-header {
  background: linear-gradient(135deg, #1a237e 0%, #0d47a1 100%);
  border-radius: 0 0 30px 30px;
  position: relative;
}

.header-content {
  position: relative;
  z-index: 1;
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
  border: 2px solid white;
}

.stat-card {
  background: white !important;
  transition: transform 0.2s ease;
}

.stat-card:active {
  transform: scale(0.96);
}

.stat-number {
  font-size: 18px;
  font-weight: bold;
}

.stat-label {
  color: #757575;
  font-size: 11px;
}

.section-card {
  background: white !important;
  overflow: hidden;
  border: 1px solid rgba(0,0,0,0.04);
}

.section-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  background: rgba(26, 35, 126, 0.03);
}

.info-field {
  padding: 8px 0;
  border-bottom: 1px solid rgba(0,0,0,0.04);
}

.info-field:last-child {
  border-bottom: none;
}

.field-label {
  font-size: 11px;
  color: #757575;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  font-weight: 500;
}

.field-value {
  font-size: 15px;
  font-weight: 500;
  color: #1a1a1a;
  padding: 2px 0;
}

.settings-list {
  background: white;
}

.setting-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 10px 16px;
  cursor: pointer;
  transition: background 0.2s;
}

.setting-item:active {
  background: rgba(0,0,0,0.04);
}

.app-info-card {
  background: white !important;
  border: 1px solid rgba(0,0,0,0.04);
}

.gap-2 {
  gap: 8px;
}

:deep(.v-theme--dark) .perfil-container {
  background: #121212;
}

:deep(.v-theme--dark) .section-card,
:deep(.v-theme--dark) .stat-card,
:deep(.v-theme--dark) .settings-list,
:deep(.v-theme--dark) .app-info-card {
  background: #1e1e1e !important;
  border-color: rgba(255,255,255,0.06);
}

:deep(.v-theme--dark) .section-header {
  background: rgba(255,255,255,0.03);
}

:deep(.v-theme--dark) .field-value {
  color: #e0e0e0;
}

:deep(.v-theme--dark) .stat-label {
  color: #9e9e9e;
}

:deep(.v-theme--dark) .field-label {
  color: #9e9e9e;
}

:deep(.v-theme--dark) .info-field {
  border-color: rgba(255,255,255,0.06);
}
</style>