<template>
  <v-container class="register-container" fluid>
    <v-row justify="center" align="center" class="min-vh-100">
      <v-col cols="12" sm="8" md="6" lg="5">
        <v-card class="register-card" elevation="4" rounded="xl">
          <v-card-title class="text-center py-3">
            <v-img src="/icons/icon-192x192.png" width="50" class="mx-auto mb-1" contain />
            <h1 class="text-h6 font-weight-bold">FinanCoop</h1>
            <p class="text-caption text-medium-emphasis">Regístrate para comenzar</p>
          </v-card-title>

          <v-divider />

          <v-card-text class="pa-3">
            <v-stepper v-model="paso" class="bg-transparent" flat>
              <v-stepper-header>
                <v-stepper-item :complete="paso > 1" :value="1" color="primary" size="small">
                  <v-icon size="14">mdi-account</v-icon>
                </v-stepper-item>
                <v-divider />
                <v-stepper-item :complete="paso > 2" :value="2" color="primary" size="small">
                  <v-icon size="14">mdi-account-group</v-icon>
                </v-stepper-item>
                <v-divider />
                <v-stepper-item :complete="paso > 3" :value="3" color="primary" size="small">
                  <v-icon size="14">mdi-card-account-details</v-icon>
                </v-stepper-item>
                <v-divider />
                <v-stepper-item :value="4" color="primary" size="small">
                  <v-icon size="14">mdi-check</v-icon>
                </v-stepper-item>
              </v-stepper-header>

              <v-stepper-window v-model="paso" class="mt-2">
                <!-- PASO 1 -->
                <v-stepper-window-item :value="1">
                  <v-text-field
                    v-model="registro.nombre"
                    label="Nombre completo *"
                    variant="outlined"
                    density="compact"
                    prepend-inner-icon="mdi-account"
                    :rules="[v => !!v || 'Requerido']"
                    hide-details
                    class="mb-2"
                  />
                  <v-text-field
                    v-model="registro.cedula"
                    label="Cédula *"
                    variant="outlined"
                    density="compact"
                    prepend-inner-icon="mdi-card-account-details"
                    :rules="[v => !!v || 'Requerido', v => v.length >= 6 || 'Mínimo 6 dígitos']"
                    hide-details
                    class="mb-2"
                  />
                  <div class="d-flex mb-2">
                    <v-select
                      v-model="codigoPais"
                      :items="codigosPaises"
                      item-title="nombre"
                      item-value="codigo"
                      label="Código"
                      variant="outlined"
                      density="compact"
                      hide-details
                      class="codigo-pais"
                      style="max-width: 120px;"
                    />
                    <v-text-field
                      v-model="registro.telefono"
                      label="Teléfono *"
                      variant="outlined"
                      density="compact"
                      prepend-inner-icon="mdi-phone"
                      :rules="[v => !!v || 'Requerido']"
                      hide-details
                      class="telefono-input"
                      placeholder="4121234567"
                    />
                  </div>
                  <v-text-field
                    v-model="registro.email"
                    label="Email (opcional)"
                    variant="outlined"
                    density="compact"
                    prepend-inner-icon="mdi-email"
                    type="email"
                    hide-details
                    class="mb-2"
                  />
                  <v-textarea
                    v-model="registro.direccion"
                    label="Dirección completa *"
                    variant="outlined"
                    density="compact"
                    rows="1"
                    prepend-inner-icon="mdi-map-marker"
                    :rules="[v => !!v || 'Requerido']"
                    hide-details
                    class="mb-2"
                    placeholder="Calle, urbanización, ciudad"
                  />
                  <div class="d-flex justify-end mt-2">
                    <v-btn color="primary" rounded="pill" size="small" @click="paso++" :disabled="!validarPaso(1)">
                      Siguiente
                      <v-icon end size="16">mdi-chevron-right</v-icon>
                    </v-btn>
                  </div>
                </v-stepper-window-item>

                <!-- PASO 2 -->
                <v-stepper-window-item :value="2">
                  <v-text-field
                    v-model="registro.referencia_nombre"
                    label="Nombre de referencia *"
                    variant="outlined"
                    density="compact"
                    prepend-inner-icon="mdi-account"
                    :rules="[v => !!v || 'Requerido']"
                    hide-details
                    class="mb-2"
                  />
                  <v-text-field
                    v-model="registro.referencia_telefono"
                    label="Teléfono de referencia *"
                    variant="outlined"
                    density="compact"
                    prepend-inner-icon="mdi-phone"
                    :rules="[v => !!v || 'Requerido']"
                    hide-details
                    class="mb-2"
                  />
                  <v-select
                    v-model="registro.referencia_parentesco"
                    :items="['Familiar', 'Amigo', 'Vecino', 'Compañero de trabajo', 'Otro']"
                    label="Parentesco *"
                    variant="outlined"
                    density="compact"
                    prepend-inner-icon="mdi-account-heart"
                    :rules="[v => !!v || 'Requerido']"
                    hide-details
                    class="mb-2"
                  />
                  <div class="d-flex justify-space-between mt-2">
                    <v-btn variant="text" size="small" @click="paso--">
                      <v-icon start size="16">mdi-chevron-left</v-icon>
                      Atrás
                    </v-btn>
                    <v-btn color="primary" rounded="pill" size="small" @click="paso++" :disabled="!validarPaso(2)">
                      Siguiente
                      <v-icon end size="16">mdi-chevron-right</v-icon>
                    </v-btn>
                  </div>
                </v-stepper-window-item>

                <!-- PASO 3 -->
                <v-stepper-window-item :value="3">
                  <div class="text-center py-2">
                    <v-icon size="40" :color="fotoCedula ? 'success' : 'grey-lighten-2'" class="mb-1">
                      {{ fotoCedula ? 'mdi-check-circle' : 'mdi-camera' }}
                    </v-icon>
                    <div v-if="!fotoCedula" class="text-caption text-medium-emphasis mb-2">
                      Sube foto de tu cédula
                    </div>
                    <div v-else class="text-caption text-success mb-2">✅ Foto cargada</div>
                    
                    <v-btn :color="fotoCedula ? 'success' : 'primary'" rounded="pill" size="small" @click="mostrarOpcionesFoto">
                      <v-icon start size="16">{{ fotoCedula ? 'mdi-refresh' : 'mdi-camera' }}</v-icon>
                      {{ fotoCedula ? 'Cambiar' : 'Subir Foto' }}
                    </v-btn>

                    <div v-if="fotoCedula" class="mt-2">
                      <v-img :src="fotoCedula" max-height="100" contain class="rounded" />
                    </div>
                  </div>

                  <div class="d-flex justify-space-between mt-2">
                    <v-btn variant="text" size="small" @click="paso--">
                      <v-icon start size="16">mdi-chevron-left</v-icon>
                      Atrás
                    </v-btn>
                    <v-btn color="primary" rounded="pill" size="small" @click="paso++" :disabled="!validarPaso(3)">
                      Siguiente
                      <v-icon end size="16">mdi-chevron-right</v-icon>
                    </v-btn>
                  </div>
                </v-stepper-window-item>

                <!-- PASO 4 -->
                <v-stepper-window-item :value="4">
                  <v-alert type="success" class="mb-2" density="compact">
                    <span class="text-caption font-weight-medium">✅ Revisa tus datos</span>
                  </v-alert>

                  <v-list density="compact" class="bg-transparent">
                    <v-list-item>
                      <v-list-item-title class="text-caption text-medium-emphasis">Nombre</v-list-item-title>
                      <v-list-item-subtitle class="text-body-2 font-weight-medium">{{ registro.nombre }}</v-list-item-subtitle>
                    </v-list-item>
                    <v-list-item>
                      <v-list-item-title class="text-caption text-medium-emphasis">Cédula</v-list-item-title>
                      <v-list-item-subtitle class="text-body-2 font-weight-medium">{{ registro.cedula }}</v-list-item-subtitle>
                    </v-list-item>
                    <v-list-item>
                      <v-list-item-title class="text-caption text-medium-emphasis">Teléfono</v-list-item-title>
                      <v-list-item-subtitle class="text-body-2 font-weight-medium">{{ telefonoCompleto }}</v-list-item-subtitle>
                    </v-list-item>
                    <v-list-item>
                      <v-list-item-title class="text-caption text-medium-emphasis">Dirección</v-list-item-title>
                      <v-list-item-subtitle class="text-body-2 font-weight-medium">{{ registro.direccion }}</v-list-item-subtitle>
                    </v-list-item>
                    <v-list-item>
                      <v-list-item-title class="text-caption text-medium-emphasis">Referencia</v-list-item-title>
                      <v-list-item-subtitle class="text-body-2 font-weight-medium">
                        {{ registro.referencia_nombre }} ({{ registro.referencia_parentesco }})
                      </v-list-item-subtitle>
                    </v-list-item>
                    <v-list-item v-if="fotoCedula">
                      <v-list-item-title class="text-caption text-medium-emphasis">Cédula</v-list-item-title>
                      <v-list-item-subtitle class="text-success">
                        <v-icon size="16" color="success">mdi-check-circle</v-icon>
                        Foto cargada
                      </v-list-item-subtitle>
                    </v-list-item>
                  </v-list>

                  <div class="d-flex justify-space-between mt-2">
                    <v-btn variant="text" size="small" @click="paso--">
                      <v-icon start size="16">mdi-chevron-left</v-icon>
                      Atrás
                    </v-btn>
                    <v-btn color="success" rounded="pill" size="small" :loading="enviando" @click="enviarRegistro">
                      <v-icon start size="16">mdi-send</v-icon>
                      Enviar
                    </v-btn>
                  </div>
                </v-stepper-window-item>
              </v-stepper-window>
            </v-stepper>
          </v-card-text>
        </v-card>
      </v-col>
    </v-row>
  </v-container>
</template>

<script setup>
import { ref, reactive, computed } from 'vue'
import { useRouter } from 'vue-router'
import { useFinanCash } from '@/composables/useFinanCash'

// ✅ IMPORTAMOS CAPACITOR CAMERA
import { Camera, CameraResultType, CameraSource } from '@capacitor/camera'

const router = useRouter()
const { registrarCliente } = useFinanCash()

const paso = ref(1)
const enviando = ref(false)
const fotoCedula = ref(null)
const codigoPais = ref('+58')

const codigosPaises = [
  { nombre: '🇻🇪 Venezuela', codigo: '+58' },
  { nombre: '🇨🇴 Colombia', codigo: '+57' },
  { nombre: '🇪🇨 Ecuador', codigo: '+593' },
  { nombre: '🇦🇷 Argentina', codigo: '+54' },
  { nombre: '🇨🇱 Chile', codigo: '+56' },
  { nombre: '🇵🇪 Perú', codigo: '+51' },
  { nombre: '🇲🇽 México', codigo: '+52' },
  { nombre: '🇪🇸 España', codigo: '+34' },
  { nombre: '🇺🇸 USA', codigo: '+1' },
  { nombre: '🇵🇦 Panamá', codigo: '+507' },
  { nombre: '🇩🇴 República Dominicana', codigo: '+1' },
  { nombre: '🇨🇷 Costa Rica', codigo: '+506' },
  { nombre: '🇬🇹 Guatemala', codigo: '+502' },
  { nombre: '🇸🇻 El Salvador', codigo: '+503' },
  { nombre: '🇭🇳 Honduras', codigo: '+504' },
  { nombre: '🇳🇮 Nicaragua', codigo: '+505' }
]

const registro = reactive({
  nombre: '',
  cedula: '',
  telefono: '',
  email: '',
  direccion: '',
  referencia_nombre: '',
  referencia_telefono: '',
  referencia_parentesco: '',
  cedula_foto: null
})

const telefonoCompleto = computed(() => {
  if (!registro.telefono) return ''
  return `${codigoPais.value}${registro.telefono}`
})

const validarPaso = (paso) => {
  switch(paso) {
    case 1: 
      return registro.nombre && 
             registro.cedula && 
             registro.telefono && 
             registro.direccion
    case 2: 
      return registro.referencia_nombre && 
             registro.referencia_telefono && 
             registro.referencia_parentesco
    case 3: 
      return !!fotoCedula.value
    default: 
      return true
  }
}

// ✅ FUNCIÓN PRINCIPAL: Muestra opciones y usa Capacitor Camera
const mostrarOpcionesFoto = async () => {
  try {
    const image = await Camera.getPhoto({
      quality: 80,
      allowEditing: false,
      resultType: CameraResultType.Uri,
      source: CameraSource.Prompt, // 📌 ESTO ES CLAVE: da a elegir entre cámara y galería
      width: 800,
      height: 800
    })
    
    if (image && image.webPath) {
      const response = await fetch(image.webPath)
      const blob = await response.blob()
      const file = new File([blob], 'cedula.jpg', { type: 'image/jpeg' })
      
      const reader = new FileReader()
      reader.onload = (ev) => {
        fotoCedula.value = ev.target.result
        registro.cedula_foto = file
        console.log('📸 Foto seleccionada con Capacitor')
      }
      reader.readAsDataURL(file)
    }
  } catch (error) {
    console.error('Error al tomar foto:', error)
    // Fallback si Capacitor no funciona
    tomarFotoTradicional()
  }
}

// ✅ FALLBACK: Método tradicional por si Capacitor falla
const tomarFotoTradicional = () => {
  const input = document.createElement('input')
  input.type = 'file'
  input.accept = 'image/*'
  input.onchange = (e) => {
    const file = e.target.files[0]
    if (file) {
      const reader = new FileReader()
      reader.onload = (ev) => {
        fotoCedula.value = ev.target.result
        registro.cedula_foto = file
        console.log('📸 Foto seleccionada (fallback):', file.name)
      }
      reader.readAsDataURL(file)
    }
  }
  input.click()
}

const enviarRegistro = async () => {
  if (!validarPaso(1) || !validarPaso(2) || !validarPaso(3)) {
    alert('Por favor completa todos los campos obligatorios')
    return
  }

  enviando.value = true
  
  try {
    const telefonoCompletoValue = `${codigoPais.value}${registro.telefono}`
    
    const formData = new FormData()
    formData.append('nombre', registro.nombre.trim())
    formData.append('cedula', registro.cedula.trim())
    formData.append('telefono', telefonoCompletoValue)
    formData.append('email', (registro.email || '').trim())
    formData.append('direccion', registro.direccion.trim())
    formData.append('referencia_nombre', registro.referencia_nombre.trim())
    formData.append('referencia_telefono', registro.referencia_telefono.trim())
    formData.append('referencia_parentesco', registro.referencia_parentesco.trim())
    
    if (registro.cedula_foto) {
      formData.append('cedula_foto', registro.cedula_foto)
    }
    
    const result = await registrarCliente(formData)
    
    if (result.success) {
      if (result.pin) {
        localStorage.setItem('financoop_pin_temp', result.pin)
      }
      router.push('/registro-exitoso/' + encodeURIComponent(registro.cedula))
    } else {
      alert('Error: ' + (result.error || 'No se pudo registrar'))
    }
  } catch (err) {
    console.error('❌ Error en registro:', err)
    alert('Error al registrar. Intenta de nuevo.')
  } finally {
    enviando.value = false
  }
}
</script>

<style scoped>
.register-container {
  min-height: 100vh;
  background: #f5f7fa;
  padding: 10px 0;
}

.register-card {
  background: white !important;
  border-radius: 20px !important;
}

.codigo-pais {
  flex-shrink: 0;
  margin-right: 8px;
}

.codigo-pais :deep(.v-field) {
  border-radius: 8px 0 0 8px !important;
}

.telefono-input {
  flex: 1;
}

.telefono-input :deep(.v-field) {
  border-radius: 0 8px 8px 0 !important;
}

:deep(.v-theme--dark) .register-container {
  background: #121212;
}

:deep(.v-theme--dark) .register-card {
  background: #1e1e1e !important;
}
</style>