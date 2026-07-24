<template>
  <div class="perfil-wrapper">
    <div class="bg-gradient"></div>

    <div class="page-content">
      <!-- Header -->
      <v-sheet class="perfil-header" elevation="0">
        <div class="header-content pa-4">
          <div class="text-center">
            <div class="avatar-section">
              <v-avatar size="80" :color="colorNivel(usuario.nivel || 'nuevo')" class="avatar-main">
                <v-icon size="40" color="white">{{ iconoNivel(usuario.nivel || 'nuevo') }}</v-icon>
              </v-avatar>
              <v-chip :color="colorNivel(usuario.nivel || 'nuevo')" size="x-small" class="level-chip" text-color="white">
                <v-icon size="12" start>{{ iconoNivel(usuario.nivel || 'nuevo') }}</v-icon>
                {{ usuario.nivel || 'Nuevo' }}
              </v-chip>
            </div>

            <h2 class="perfil-name">{{ usuario.nombre || 'Cargando...' }}</h2>
            
            <div class="d-flex align-center justify-center gap-2 mt-1">
              <span class="perfil-score"><v-icon size="14" color="white" class="mr-1">mdi-star</v-icon>{{ usuario.score || 0 }} pts</span>
              <span class="perfil-divider">•</span>
              <span class="perfil-id">ID: {{ usuario.cedula || '---' }}</span>
            </div>

            <v-chip v-if="usuario.estado === 'pendiente'" color="warning" size="x-small" class="mt-2">
              <v-icon size="12" start>mdi-clock-outline</v-icon>En verificación
            </v-chip>
            <v-chip v-else color="success" size="x-small" class="mt-2">
              <v-icon size="12" start>mdi-check-circle</v-icon>Verificado
            </v-chip>
          </div>
        </div>
      </v-sheet>

      <!-- Stats -->
      <v-container class="mt-n4" fluid>
        <v-row dense no-gutters class="px-3">
          <v-col cols="4">
            <v-card class="stat-card glass-card" elevation="0">
              <div class="pa-3 text-center"><div class="stat-number text-primary">{{ financiamientos?.length || 0 }}</div><div class="stat-label">Compras</div></div>
            </v-card>
          </v-col>
          <v-col cols="4">
            <v-card class="stat-card glass-card" elevation="0">
              <div class="pa-3 text-center"><div class="stat-number text-success">${{ lineaUsada || '0' }}</div><div class="stat-label">Usado</div></div>
            </v-card>
          </v-col>
          <v-col cols="4">
            <v-card class="stat-card glass-card" elevation="0">
              <div class="pa-3 text-center"><div class="stat-number text-warning">{{ nivelActual?.cuotas_max || 0 }}</div><div class="stat-label">Cuotas max</div></div>
            </v-card>
          </v-col>
        </v-row>
      </v-container>

      <!-- Datos Personales -->
      <v-card class="section-card glass-card" elevation="0">
        <div class="section-header"><div class="d-flex align-center"><v-icon color="#4facfe" size="20" class="mr-2">mdi-account</v-icon><span>Datos Personales</span></div></div>
        <v-divider style="border-color: rgba(255,255,255,0.06);" />
        <div class="pa-3">
          <div class="info-field"><div class="field-label">Nombre completo</div><div class="field-value">{{ usuario.nombre || 'No registrado' }}</div></div>
          <div class="info-field"><div class="field-label">Cédula</div><div class="field-value">{{ usuario.cedula || 'No registrada' }}</div></div>
          <div class="info-field"><div class="field-label">Teléfono</div><div class="field-value">{{ usuario.telefono || 'No registrado' }}</div></div>
          <div class="info-field"><div class="field-label">Email</div><div class="field-value">{{ usuario.email || 'No registrado' }}</div></div>
          <div class="info-field"><div class="field-label">Dirección</div><div class="field-value">{{ usuario.direccion || 'No registrada' }}</div></div>
        </div>
      </v-card>

      <!-- Referencia -->
      <v-card class="section-card glass-card" elevation="0">
        <div class="section-header"><div class="d-flex align-center"><v-icon color="#4facfe" size="20" class="mr-2">mdi-account-group</v-icon><span>Referencia Personal</span></div></div>
        <v-divider style="border-color: rgba(255,255,255,0.06);" />
        <div class="pa-3">
          <div class="info-field"><div class="field-label">Nombre de referencia</div><div class="field-value">{{ usuario.referencia_nombre || 'No registrada' }}</div></div>
          <div class="info-field"><div class="field-label">Teléfono de referencia</div><div class="field-value">{{ usuario.referencia_telefono || 'No registrado' }}</div></div>
          <div class="info-field"><div class="field-label">Parentesco</div><div class="field-value">{{ usuario.referencia_parentesco || 'No registrado' }}</div></div>
        </div>
      </v-card>

      <!-- FOTO DE CÉDULA -->
      <v-card class="section-card glass-card" elevation="0">
        <div class="section-header"><div class="d-flex align-center"><v-icon color="#4facfe" size="20" class="mr-2">mdi-card-account-details</v-icon><span>Documento de Identidad</span></div></div>
        <v-divider style="border-color: rgba(255,255,255,0.06);" />
        <div class="pa-4">
          <div v-if="usuario.url_cedula" class="text-center">
            <v-img :src="usuario.url_cedula" max-height="250" contain class="rounded-lg mb-2 cursor-pointer" @click="verFotoAmpliada = true" />
            <div class="text-caption text-success"><v-icon size="14" start>mdi-check-circle</v-icon>Documento verificado</div>
          </div>
          <div v-else class="text-center py-4">
            <v-icon size="48" color="rgba(255,255,255,0.1)" class="mb-2">mdi-card-account-details-outline</v-icon>
            <div class="text-body-2" style="color: rgba(255,255,255,0.5);">No hay foto de cédula</div>
            <div class="text-caption mt-1" style="color: rgba(255,255,255,0.3);">Se subió durante el registro</div>
          </div>
        </div>
      </v-card>

      <!-- Configuración -->
      <v-card class="section-card glass-card" elevation="0">
        <div class="section-header"><div class="d-flex align-center"><v-icon color="#4facfe" size="20" class="mr-2">mdi-cog</v-icon><span>Configuración</span></div></div>
        <v-divider style="border-color: rgba(255,255,255,0.06);" />
        <div class="settings-list">
          
          <!-- 🆕 CONFIGURACIÓN DE HUELLA -->
          <div v-if="plataformaNativa" class="setting-item">
            <div class="d-flex align-center">
              <v-icon color="#4facfe" size="20" class="mr-3">mdi-fingerprint</v-icon>
              <div>
                <span>Inicio de sesión con huella</span>
                <div class="setting-description">Accede rápidamente sin PIN</div>
              </div>
            </div>
            <v-switch
              v-model="huellaActivada"
              color="#4facfe"
              hide-details
              density="compact"
              :loading="cargandoHuella"
              :disabled="!huellaSoportada"
              @update:model-value="onToggleHuella"
              inset
            />
          </div>

          <!-- Mensaje si no soporta huella -->
          <div v-if="plataformaNativa && !huellaSoportada" class="pa-3">
            <v-alert
              type="info"
              variant="tonal"
              density="compact"
              rounded="lg"
              class="text-caption"
            >
              <div class="d-flex align-center">
                <v-icon size="14" class="mr-2">mdi-information</v-icon>
                Configura tu huella en Ajustes del dispositivo
              </div>
            </v-alert>
          </div>

          <v-divider v-if="plataformaNativa" style="border-color: rgba(255,255,255,0.06);" />

          <!-- Cambiar PIN -->
          <div class="setting-item" @click="abrirCambiarPin">
            <div class="d-flex align-center"><v-icon color="#4facfe" size="20" class="mr-3">mdi-lock-reset</v-icon><span>Cambiar PIN</span></div>
            <v-icon size="20" color="rgba(255,255,255,0.2)">mdi-chevron-right</v-icon>
          </div>
        </div>
      </v-card>

      <!-- Cerrar sesión -->
      <v-btn block color="error" variant="tonal" rounded="pill" size="large" class="logout-btn" @click="cerrarSesion">
        <v-icon start>mdi-logout</v-icon>Cerrar sesión
      </v-btn>
    </div>

    <!-- DIALOG: Ver Foto Ampliada -->
    <v-dialog v-model="verFotoAmpliada" fullscreen>
      <v-card color="#0a0e1a">
        <v-card-title class="d-flex align-center">Foto de Cédula<v-spacer></v-spacer><v-btn icon="mdi-close" variant="text" @click="verFotoAmpliada = false" color="white"></v-btn></v-card-title>
        <v-card-text class="d-flex align-center justify-center" style="height: 80vh;">
          <v-img :src="usuario.url_cedula" max-height="80vh" contain></v-img>
        </v-card-text>
      </v-card>
    </v-dialog>

    <!-- DIALOG: Cambiar PIN -->
    <v-dialog v-model="dialogCambiarPin" max-width="400">
      <v-card class="glass-card">
        <v-card-title class="text-center pt-4">🔐 Cambiar PIN</v-card-title>
        <v-card-text>
          <v-text-field v-model="pinActual" label="PIN actual" type="password" maxlength="4" variant="outlined" density="compact" class="custom-field" bg-color="rgba(255,255,255,0.08)" placeholder="••••" />
          <v-text-field v-model="pinNuevo" label="PIN nuevo (4 dígitos)" type="password" maxlength="4" variant="outlined" density="compact" class="custom-field mt-2" bg-color="rgba(255,255,255,0.08)" placeholder="••••" />
          <v-text-field v-model="pinConfirmar" label="Confirmar PIN nuevo" type="password" maxlength="4" variant="outlined" density="compact" class="custom-field mt-2" bg-color="rgba(255,255,255,0.08)" placeholder="••••" />
          <v-alert v-if="errorPin" type="error" density="compact" class="mt-2">{{ errorPin }}</v-alert>
        </v-card-text>
        <v-card-actions class="pa-4">
          <v-btn @click="dialogCambiarPin = false" variant="text">Cancelar</v-btn>
          <v-spacer></v-spacer>
          <v-btn color="#4facfe" @click="guardarNuevoPin" :loading="cambiandoPin">Guardar</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useFinanCash } from '@/composables/useFinanCash'
import { useBiometric } from '@/composables/useBiometric'
import { buildApiUrl } from '@/config'

const { 
  token, usuario, financiamientos, nivelActual, lineaUsada,
  colorNivel, iconoNivel, cargarDatos, cerrarSesion
} = useFinanCash()

const { 
  huellaSoportada, 
  huellaActivada, 
  plataformaNativa, 
  cargandoHuella, 
  verificarSoporte, 
  toggleHuella 
} = useBiometric()

const verFotoAmpliada = ref(false)
const dialogCambiarPin = ref(false)
const pinActual = ref('')
const pinNuevo = ref('')
const pinConfirmar = ref('')
const errorPin = ref('')
const cambiandoPin = ref(false)

// 🆕 Toggle huella desde el switch
const onToggleHuella = async (activar) => {
  const resultado = await toggleHuella(activar)
  
  if (resultado.success) {
    if (activar) {
      alert('✅ Inicio de sesión con huella activado')
    } else {
      console.log('🔒 Huella desactivada')
    }
  } else {
    huellaActivada.value = !activar
    alert('❌ ' + (resultado.error || 'Error al configurar huella'))
  }
}

const abrirCambiarPin = () => {
  pinActual.value = ''; pinNuevo.value = ''; pinConfirmar.value = ''; errorPin.value = ''
  dialogCambiarPin.value = true
}

const guardarNuevoPin = async () => {
  errorPin.value = ''
  if (!pinActual.value || pinActual.value.length < 4) { errorPin.value = 'Ingresa tu PIN actual'; return }
  if (!pinNuevo.value || pinNuevo.value.length < 4) { errorPin.value = 'Ingresa un PIN nuevo de 4 dígitos'; return }
  if (pinNuevo.value !== pinConfirmar.value) { errorPin.value = 'Los PINs no coinciden'; return }
  if (pinActual.value === pinNuevo.value) { errorPin.value = 'El PIN nuevo debe ser diferente'; return }

  cambiandoPin.value = true
  try {
    const tokenStr = localStorage.getItem('financoop_token')
    const response = await fetch(buildApiUrl('/app/cambiar-pin'), {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${tokenStr}` },
      body: JSON.stringify({ pin_actual: pinActual.value, pin_nuevo: pinNuevo.value })
    })
    const data = await response.json()
    if (!response.ok) throw new Error(data.detail || 'Error al cambiar PIN')
    dialogCambiarPin.value = false
    pinActual.value = ''; pinNuevo.value = ''; pinConfirmar.value = ''
    alert('✅ PIN actualizado correctamente')
  } catch (e) { errorPin.value = e.message || 'Error al cambiar PIN' }
  finally { cambiandoPin.value = false }
}

onMounted(async () => {
  await verificarSoporte()
  if (!usuario.value?.nombre && token.value) cargarDatos()
})
</script>

<style scoped>
.perfil-wrapper { min-height: 100vh; background: #0a0e1a; position: relative; }
.bg-gradient { position: fixed; top: 0; left: 0; right: 0; bottom: 0; background: radial-gradient(ellipse at 20% 50%, rgba(79,172,254,0.08), transparent 70%), radial-gradient(ellipse at 80% 50%, rgba(99,102,241,0.08), transparent 70%); z-index: 0; }
.page-content { position: relative; z-index: 1; padding: 0 16px 80px; }
.glass-card { background: rgba(255,255,255,0.04) !important; backdrop-filter: blur(12px) !important; -webkit-backdrop-filter: blur(12px) !important; border: 1px solid rgba(255,255,255,0.06); border-radius: 16px !important; }
.perfil-header { background: linear-gradient(135deg, #1a237e 0%, #0d47a1 100%); border-radius: 0 0 30px 30px; margin: 0 -16px 16px; padding: 0 16px; }
.header-content { position: relative; z-index: 1; padding: 24px 0 20px; }
.avatar-section { position: relative; display: inline-block; }
.avatar-main { border: 3px solid rgba(255,255,255,0.4); box-shadow: 0 8px 32px rgba(0,0,0,0.2); }
.level-chip { position: absolute; bottom: -4px; right: -4px; font-weight: bold; padding: 0 8px; border: 2px solid #0d47a1; }
.perfil-name { font-size: 20px; font-weight: 700; color: #ffffff; margin-top: 8px; }
.perfil-score { font-size: 12px; color: rgba(255,255,255,0.7); }
.perfil-divider { color: rgba(255,255,255,0.3); }
.perfil-id { font-size: 12px; color: rgba(255,255,255,0.5); }
.stat-card { transition: transform 0.2s ease; }
.stat-card:active { transform: scale(0.96); }
.stat-number { font-size: 20px; font-weight: 700; }
.stat-number.text-primary { color: #4facfe; }
.stat-number.text-success { color: #4caf50; }
.stat-number.text-warning { color: #ffd54f; }
.stat-label { font-size: 11px; color: rgba(255,255,255,0.4); }
.section-card { margin-bottom: 12px; overflow: hidden; }
.section-header { display: flex; align-items: center; justify-content: space-between; padding: 10px 16px; background: rgba(79,172,254,0.04); }
.section-header span { font-size: 13px; font-weight: 600; color: #ffffff; }
.info-field { padding: 6px 0; border-bottom: 1px solid rgba(255,255,255,0.04); }
.info-field:last-child { border-bottom: none; }
.field-label { font-size: 10px; color: rgba(255,255,255,0.4); text-transform: uppercase; letter-spacing: 0.5px; }
.field-value { font-size: 15px; font-weight: 600; color: #ffffff; opacity: 1; }
.settings-list { padding: 4px 0; }
.setting-item { display: flex; align-items: center; justify-content: space-between; padding: 10px 16px; cursor: pointer; color: rgba(255,255,255,0.85); }
.setting-item:hover { background: rgba(255,255,255,0.04); }
.setting-item span { font-size: 14px; font-weight: 500; }
.setting-description { font-size: 11px; color: rgba(255,255,255,0.4); margin-top: 2px; }
.logout-btn { background: rgba(239,68,68,0.1) !important; color: #f87171 !important; border: 1px solid rgba(239,68,68,0.15); margin-top: 8px; }
.cursor-pointer { cursor: pointer; }
.custom-field :deep(.v-field) { border-radius: 12px !important; border: 1px solid rgba(255,255,255,0.2) !important; }
.custom-field :deep(.v-field__input) { color: #ffffff !important; padding-top: 8px !important; padding-bottom: 8px !important; }
.custom-field :deep(.v-field__input::placeholder) { color: rgba(255,255,255,0.7) !important; font-weight: 500 !important; opacity: 1 !important; }
.custom-field :deep(.v-label) { color: rgba(255,255,255,0.6) !important; }
</style>