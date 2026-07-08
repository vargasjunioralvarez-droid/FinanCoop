<template>
  <v-container class="pa-4 perfil-view">
    <!-- Header del perfil -->
    <v-card class="perfil-header mb-4" elevation="4">
      <v-card-text class="pa-4 text-center">
        <div class="position-relative d-inline-block">
          <v-avatar size="80" :color="colorNivel(usuario.nivel)" class="mb-2">
            <v-icon size="40" color="white">{{ iconoNivel(usuario.nivel) }}</v-icon>
          </v-avatar>
          <v-btn
            icon
            size="small"
            color="primary"
            class="edit-avatar-btn"
            @click="editando = true"
          >
            <v-icon size="16">mdi-pencil</v-icon>
          </v-btn>
        </div>
        <h2 class="text-h5 font-weight-bold">{{ usuario.nombre || 'Cliente' }}</h2>
        <div class="d-flex align-center justify-center mt-1">
          <v-chip :color="colorNivel(usuario.nivel)" size="small" variant="tonal" class="mr-2">
            <v-icon size="14" start>{{ iconoNivel(usuario.nivel) }}</v-icon>
            {{ usuario.nivel }}
          </v-chip>
          <span class="text-caption text-medium-emphasis">{{ usuario.score }} pts</span>
        </div>
      </v-card-text>
    </v-card>

    <!-- Datos personales -->
    <v-card class="mb-4" elevation="2">
      <v-card-title class="d-flex align-center py-3">
        <v-icon color="primary" class="mr-2">mdi-account</v-icon>
        Datos Personales
        <v-spacer />
        <v-btn
          :icon="editando ? 'mdi-check' : 'mdi-pencil'"
          variant="text"
          size="small"
          :color="editando ? 'success' : 'primary'"
          @click="toggleEdicion"
        />
      </v-card-title>

      <v-card-text class="pa-4">
        <v-form ref="formPerfil" :disabled="!editando">
          <v-text-field
            v-model="perfilForm.nombre"
            label="Nombre completo"
            prepend-inner-icon="mdi-account"
            variant="outlined"
            density="comfortable"
            class="mb-3"
            :rules="[v => !!v || 'Requerido']"
          />

          <v-text-field
            v-model="perfilForm.cedula"
            label="Cédula"
            prepend-inner-icon="mdi-card-account-details"
            variant="outlined"
            density="comfortable"
            class="mb-3"
            disabled
          />

          <v-text-field
            v-model="perfilForm.telefono"
            label="Teléfono"
            prepend-inner-icon="mdi-phone"
            variant="outlined"
            density="comfortable"
            class="mb-3"
            :rules="[v => !!v || 'Requerido']"
          />

          <v-text-field
            v-model="perfilForm.email"
            label="Email"
            prepend-inner-icon="mdi-email"
            variant="outlined"
            density="comfortable"
            class="mb-3"
            type="email"
          />

          <v-textarea
            v-model="perfilForm.direccion"
            label="Dirección"
            prepend-inner-icon="mdi-map-marker"
            variant="outlined"
            density="comfortable"
            class="mb-3"
            rows="2"
          />
        </v-form>
      </v-card-text>
    </v-card>

    <!-- Referencia personal -->
    <v-card class="mb-4" elevation="2">
      <v-card-title class="d-flex align-center py-3">
        <v-icon color="primary" class="mr-2">mdi-account-group</v-icon>
        Referencia Personal
      </v-card-title>

      <v-card-text class="pa-4">
        <v-form ref="formReferencia" :disabled="!editando">
          <v-text-field
            v-model="perfilForm.referencia_nombre"
            label="Nombre de referencia"
            prepend-inner-icon="mdi-account"
            variant="outlined"
            density="comfortable"
            class="mb-3"
          />

          <v-text-field
            v-model="perfilForm.referencia_telefono"
            label="Teléfono de referencia"
            prepend-inner-icon="mdi-phone"
            variant="outlined"
            density="comfortable"
            class="mb-3"
          />

          <v-select
            v-model="perfilForm.referencia_parentesco"
            label="Parentesco"
            :items="['Familiar', 'Amigo', 'Vecino', 'Compañero de trabajo', 'Otro']"
            prepend-inner-icon="mdi-account-heart"
            variant="outlined"
            density="comfortable"
          />
        </v-form>
      </v-card-text>
    </v-card>

    <!-- Foto de cédula -->
    <v-card class="mb-4" elevation="2">
      <v-card-title class="d-flex align-center py-3">
        <v-icon color="primary" class="mr-2">mdi-card-account-details</v-icon>
        Documento de Identidad
      </v-card-title>

      <v-card-text class="pa-4">
        <div v-if="!cedulaPreview" class="text-center py-4">
          <v-icon size="64" color="medium-emphasis" class="mb-2">mdi-camera</v-icon>
          <div class="text-body-2 text-medium-emphasis mb-3">
            Sube una foto de tu cédula de identidad
          </div>
          <v-btn
            color="primary"
            rounded="pill"
            @click="abrirCamara"
          >
            <v-icon start>mdi-camera</v-icon>
            Tomar Foto
          </v-btn>
        </div>

        <div v-else class="text-center">
          <v-img
            :src="cedulaPreview"
            max-height="200"
            contain
            class="rounded-lg mb-3"
          />
          <div class="d-flex justify-center gap-2">
            <v-btn color="error" variant="outlined" rounded="pill" @click="cedulaPreview = null">
              <v-icon start>mdi-delete</v-icon>
              Eliminar
            </v-btn>
            <v-btn color="success" rounded="pill" @click="guardarFotoCedula">
              <v-icon start>mdi-check</v-icon>
              Guardar
            </v-btn>
          </div>
        </div>

        <!-- Input oculto para cámara -->
        <input
          ref="inputCedula"
          type="file"
          accept="image/*"
          capture="environment"
          class="d-none"
          @change="onCedulaSeleccionada"
        />
      </v-card-text>
    </v-card>

    <!-- Configuración -->
    <v-card class="mb-4" elevation="2">
      <v-card-title class="d-flex align-center py-3">
        <v-icon color="primary" class="mr-2">mdi-cog</v-icon>
        Configuración
      </v-card-title>

      <v-list>
        <v-list-item @click="mostrarCambiarPin = true">
          <template v-slot:prepend>
            <v-icon color="primary">mdi-lock-reset</v-icon>
          </template>
          <v-list-item-title>Cambiar PIN</v-list-item-title>
          <template v-slot:append>
            <v-icon>mdi-chevron-right</v-icon>
          </template>
        </v-list-item>

        <v-list-item @click="mostrarNotificaciones = true">
          <template v-slot:prepend>
            <v-icon color="primary">mdi-bell</v-icon>
          </template>
          <v-list-item-title>Notificaciones</v-list-item-title>
          <template v-slot:append>
            <v-switch v-model="notificacionesActivas" hide-details density="compact" />
          </template>
        </v-list-item>

        <v-list-item>
          <template v-slot:prepend>
            <v-icon color="primary">mdi-theme-light-dark</v-icon>
          </template>
          <v-list-item-title>Tema oscuro</v-list-item-title>
          <template v-slot:append>
            <v-switch v-model="temaOscuro" hide-details density="compact" />
          </template>
        </v-list-item>
      </v-list>
    </v-card>

    <!-- Info de la app -->
    <v-card class="mb-4 info-card" variant="outlined">
      <v-card-text class="pa-4 text-center">
        <v-img src="/icons/icon-192x192.png" width="48" height="48" class="mx-auto mb-2" contain />
        <div class="text-body-2 font-weight-medium">FinanCoop v1.0</div>
        <div class="text-caption text-medium-emphasis">Cecosesola</div>
        <div class="text-caption text-medium-emphasis mt-1">
          Tu deuda en USD • Pagas en Bs
        </div>
      </v-card-text>
    </v-card>

    <v-btn block color="error" variant="outlined" rounded="pill" class="mb-6" @click="cerrarSesion">
      <v-icon start>mdi-logout</v-icon>
      Cerrar sesión
    </v-btn>
  </v-container>
</template>

<script setup>
import { ref, reactive, computed, onMounted, watch } from 'vue'
import { useRouter } from 'vue-router'
import { useTheme } from 'vuetify'
import { useFinanCash } from '@/composables/useFinanCash'

const router = useRouter()
const theme = useTheme()
const { token } = useFinanCash()

// Refs
const formPerfil = ref(null)
const formReferencia = ref(null)
const inputCedula = ref(null)
const editando = ref(false)

// Estados
const cedulaPreview = ref(null)
const mostrarCambiarPin = ref(false)
const mostrarNotificaciones = ref(false)
const notificacionesActivas = ref(true)
const temaOscuro = ref(false)

// Datos del usuario (en producción vendrían de una store/API)
const usuario = reactive({
  nombre: 'Juan Pérez',
  nivel: 'Oro',
  score: 1250,
  cedula: 'V-12345678'
})

// Formulario de perfil
const perfilForm = reactive({
  nombre: 'Juan Pérez',
  cedula: 'V-12345678',
  telefono: '0412-1234567',
  email: 'juan@email.com',
  direccion: 'Calle Principal, Edificio A, Apt 4',
  referencia_nombre: 'María Pérez',
  referencia_telefono: '0414-7654321',
  referencia_parentesco: 'Familiar'
})

// Niveles y sus colores/íconos
const niveles = {
  'Bronce': { color: 'brown', icono: 'mdi-medal' },
  'Plata': { color: 'grey', icono: 'mdi-medal' },
  'Oro': { color: 'amber', icono: 'mdi-trophy' },
  'Platino': { color: 'cyan', icono: 'mdi-crown' },
  'Diamante': { color: 'purple', icono: 'mdi-diamond-stone' }
}

// Computed
const colorNivel = (nivel) => {
  return niveles[nivel]?.color || 'grey'
}

const iconoNivel = (nivel) => {
  return niveles[nivel]?.icono || 'mdi-account'
}

// Métodos
const toggleEdicion = async () => {
  if (editando.value) {
    // Guardar cambios
    const validPerfil = await formPerfil.value?.validate()
    const validRef = await formReferencia.value?.validate()

    if (validPerfil?.valid && validRef?.valid) {
      Object.assign(usuario, {
        nombre: perfilForm.nombre
      })
      editando.value = false
    }
  } else {
    editando.value = true
  }
}

const abrirCamara = () => {
  inputCedula.value?.click()
}

const onCedulaSeleccionada = (event) => {
  const file = event.target.files[0]
  if (file) {
    const reader = new FileReader()
    reader.onload = (e) => {
      cedulaPreview.value = e.target.result
    }
    reader.readAsDataURL(file)
  }
}

const guardarFotoCedula = async () => {
  console.log('Guardando foto de cédula...')
}

const cerrarSesion = () => {
  localStorage.removeItem('token')
  token.value = null
  router.push('/login')
}

// Watchers
watch(temaOscuro, (val) => {
  theme.global.name.value = val ? 'dark' : 'light'
})

// Ciclo de vida
onMounted(() => {
  const temaGuardado = localStorage.getItem('temaOscuro')
  if (temaGuardado) {
    temaOscuro.value = JSON.parse(temaGuardado)
  }
})
</script>

<style scoped>
.perfil-view {
  max-width: 600px;
  margin: 0 auto;
}

.edit-avatar-btn {
  position: absolute;
  bottom: 0;
  right: 0;
  transform: translate(25%, 25%);
}

.perfil-header {
  background: linear-gradient(135deg, var(--v-primary-base) 0%, var(--v-primary-darken-1) 100%);
}

.perfil-header :deep(.v-card-text) {
  color: white;
}

.info-card {
  opacity: 0.8;
}

.gap-2 {
  gap: 8px;
}
</style>