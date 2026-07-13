<template>
  <div class="register-wrapper">
    <div class="bg-gradient"></div>

    <div class="page-content">
      <v-card class="register-card glass-card" elevation="0">
        <v-card-text class="pa-4">
          <div class="text-center mb-3">
            <v-img src="/icons/icon-192x192.png" width="50" class="mx-auto mb-1" contain />
            <h1 class="register-title">FinanCoop</h1>
            <p class="register-sub">Regístrate para comenzar</p>
          </div>

          <v-divider style="border-color: rgba(255,255,255,0.06);" />

          <v-stepper v-model="paso" class="bg-transparent flat">
            <v-stepper-header>
              <v-stepper-item :complete="paso > 1" :value="1" color="#4facfe" size="small">
                <v-icon size="14">mdi-account</v-icon>
              </v-stepper-item>
              <v-divider />
              <v-stepper-item :complete="paso > 2" :value="2" color="#4facfe" size="small">
                <v-icon size="14">mdi-account-group</v-icon>
              </v-stepper-item>
              <v-divider />
              <v-stepper-item :complete="paso > 3" :value="3" color="#4facfe" size="small">
                <v-icon size="14">mdi-card-account-details</v-icon>
              </v-stepper-item>
              <v-divider />
              <v-stepper-item :value="4" color="#4facfe" size="small">
                <v-icon size="14">mdi-check</v-icon>
              </v-stepper-item>
            </v-stepper-header>

            <v-stepper-window v-model="paso" class="mt-3">
              <!-- Paso 1 -->
              <v-stepper-window-item :value="1">
                <v-text-field v-model="registro.nombre" label="Nombre completo *" variant="outlined" density="compact" prepend-inner-icon="mdi-account" :rules="[v => !!v || 'Requerido']" hide-details class="mb-2" />
                <v-text-field v-model="registro.cedula" label="Cédula *" variant="outlined" density="compact" prepend-inner-icon="mdi-card-account-details" :rules="[v => !!v || 'Requerido', v => v.length >= 6 || 'Mínimo 6 dígitos']" hide-details class="mb-2" />
                <div class="d-flex mb-2">
                  <v-select v-model="codigoPais" :items="codigosPaises" item-title="nombre" item-value="codigo" label="Código" variant="outlined" density="compact" hide-details class="codigo-pais" style="max-width: 120px;" />
                  <v-text-field v-model="registro.telefono" label="Teléfono *" variant="outlined" density="compact" prepend-inner-icon="mdi-phone" :rules="[v => !!v || 'Requerido']" hide-details class="telefono-input" placeholder="4121234567" />
                </div>
                <v-text-field v-model="registro.email" label="Email (opcional)" variant="outlined" density="compact" prepend-inner-icon="mdi-email" type="email" hide-details class="mb-2" />
                <v-textarea v-model="registro.direccion" label="Dirección completa *" variant="outlined" density="compact" rows="1" prepend-inner-icon="mdi-map-marker" :rules="[v => !!v || 'Requerido']" hide-details class="mb-2" placeholder="Calle, urbanización, ciudad" />
                <div class="d-flex justify-end mt-2">
                  <v-btn color="#4facfe" rounded="pill" size="small" @click="paso++" :disabled="!validarPaso(1)">Siguiente <v-icon end size="16">mdi-chevron-right</v-icon></v-btn>
                </div>
              </v-stepper-window-item>

              <!-- Paso 2 -->
              <v-stepper-window-item :value="2">
                <v-text-field v-model="registro.referencia_nombre" label="Nombre de referencia *" variant="outlined" density="compact" prepend-inner-icon="mdi-account" :rules="[v => !!v || 'Requerido']" hide-details class="mb-2" />
                <v-text-field v-model="registro.referencia_telefono" label="Teléfono de referencia *" variant="outlined" density="compact" prepend-inner-icon="mdi-phone" :rules="[v => !!v || 'Requerido']" hide-details class="mb-2" />
                <v-select v-model="registro.referencia_parentesco" :items="['Familiar', 'Amigo', 'Vecino', 'Compañero de trabajo', 'Otro']" label="Parentesco *" variant="outlined" density="compact" prepend-inner-icon="mdi-account-heart" :rules="[v => !!v || 'Requerido']" hide-details class="mb-2" />
                <div class="d-flex justify-space-between mt-2">
                  <v-btn variant="text" size="small" @click="paso--"><v-icon start size="16">mdi-chevron-left</v-icon>Atrás</v-btn>
                  <v-btn color="#4facfe" rounded="pill" size="small" @click="paso++" :disabled="!validarPaso(2)">Siguiente <v-icon end size="16">mdi-chevron-right</v-icon></v-btn>
                </div>
              </v-stepper-window-item>

              <!-- Paso 3 -->
              <v-stepper-window-item :value="3">
                <div class="text-center py-2">
                  <v-icon size="40" :color="fotoCedula ? '#4caf50' : 'rgba(255,255,255,0.1)'" class="mb-1">{{ fotoCedula ? 'mdi-check-circle' : 'mdi-camera' }}</v-icon>
                  <div v-if="!fotoCedula" class="text-caption text-medium-emphasis mb-2">Sube foto de tu cédula</div>
                  <div v-else class="text-caption text-success mb-2">✅ Foto cargada</div>
                  <v-btn :color="fotoCedula ? '#4caf50' : '#4facfe'" rounded="pill" size="small" @click="abrirSelectorArchivos">
                    <v-icon start size="16">{{ fotoCedula ? 'mdi-refresh' : 'mdi-file-upload' }}</v-icon>{{ fotoCedula ? 'Cambiar' : 'Seleccionar Archivo' }}
                  </v-btn>
                  <div v-if="fotoCedula" class="mt-2"><v-img :src="fotoCedula" max-height="100" contain class="rounded" /></div>
                </div>
                <div class="d-flex justify-space-between mt-2">
                  <v-btn variant="text" size="small" @click="paso--"><v-icon start size="16">mdi-chevron-left</v-icon>Atrás</v-btn>
                  <v-btn color="#4facfe" rounded="pill" size="small" @click="paso++" :disabled="!validarPaso(3)">Siguiente <v-icon end size="16">mdi-chevron-right</v-icon></v-btn>
                </div>
              </v-stepper-window-item>

              <!-- Paso 4 -->
              <v-stepper-window-item :value="4">
                <v-alert type="success" class="mb-2" density="compact">✅ Revisa tus datos</v-alert>
                <v-list density="compact" class="bg-transparent">
                  <v-list-item><v-list-item-title class="text-caption text-medium-emphasis">Nombre</v-list-item-title><v-list-item-subtitle class="text-body-2">{{ registro.nombre }}</v-list-item-subtitle></v-list-item>
                  <v-list-item><v-list-item-title class="text-caption text-medium-emphasis">Cédula</v-list-item-title><v-list-item-subtitle class="text-body-2">{{ registro.cedula }}</v-list-item-subtitle></v-list-item>
                  <v-list-item><v-list-item-title class="text-caption text-medium-emphasis">Teléfono</v-list-item-title><v-list-item-subtitle class="text-body-2">{{ telefonoCompleto }}</v-list-item-subtitle></v-list-item>
                  <v-list-item><v-list-item-title class="text-caption text-medium-emphasis">Dirección</v-list-item-title><v-list-item-subtitle class="text-body-2">{{ registro.direccion }}</v-list-item-subtitle></v-list-item>
                  <v-list-item><v-list-item-title class="text-caption text-medium-emphasis">Referencia</v-list-item-title><v-list-item-subtitle class="text-body-2">{{ registro.referencia_nombre }} ({{ registro.referencia_parentesco }})</v-list-item-subtitle></v-list-item>
                  <v-list-item v-if="fotoCedula"><v-list-item-title class="text-caption text-medium-emphasis">Cédula</v-list-item-title><v-list-item-subtitle class="text-success"><v-icon size="16" color="success">mdi-check-circle</v-icon>Foto cargada</v-list-item-subtitle></v-list-item>
                </v-list>
                <div class="d-flex justify-space-between mt-2">
                  <v-btn variant="text" size="small" @click="paso--"><v-icon start size="16">mdi-chevron-left</v-icon>Atrás</v-btn>
                  <v-btn color="#4caf50" rounded="pill" size="small" :loading="enviando" @click="enviarRegistro"><v-icon start size="16">mdi-send</v-icon>Enviar</v-btn>
                </div>
              </v-stepper-window-item>
            </v-stepper-window>
          </v-stepper>
        </v-card-text>
      </v-card>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, computed } from 'vue'
import { useRouter } from 'vue-router'
import { useFinanCash } from '@/composables/useFinanCash'

const router = useRouter()
const { registrarCliente } = useFinanCash()

const paso = ref(1)
const enviando = ref(false)
const fotoCedula = ref(null)
const fotoFile = ref(null)
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
  { nombre: '🇺🇸 USA', codigo: '+1' }
]

const registro = reactive({
  nombre: '',
  cedula: '',
  telefono: '',
  email: '',
  direccion: '',
  referencia_nombre: '',
  referencia_telefono: '',
  referencia_parentesco: ''
})

const telefonoCompleto = computed(() => `${codigoPais.value}${registro.telefono}`)

const validarPaso = (p) => {
<<<<<<< Updated upstream
  if (p === 1) return registro.nombre && registro.cedula && registro.telefono && registro.direccion
  if (p === 2) return registro.referencia_nombre && registro.referencia_telefono && registro.referencia_parentesco
  if (p === 3) return !!fotoCedula.value
=======
  if (p === 1) {
    return registro.nombre && 
           registro.cedula && 
           /^\d+$/.test(registro.cedula) &&
           registro.telefono && 
           /^\d+$/.test(registro.telefono) &&
           registro.direccion
  }
  if (p === 2) {
    return registro.referencia_nombre && 
           registro.referencia_telefono && 
           /^\d+$/.test(registro.referencia_telefono) &&
           registro.referencia_parentesco
  }
  if (p === 3) {
    return !!fotoCedula.value
  }
>>>>>>> Stashed changes
  return true
}

const abrirSelectorArchivos = () => {
  const input = document.createElement('input')
  input.type = 'file'
  input.accept = 'image/*'
  input.onchange = (e) => {
    const file = e.target.files[0]
    if (file) {
      const reader = new FileReader()
<<<<<<< Updated upstream
      reader.onload = (ev) => { fotoCedula.value = ev.target.result; fotoFile.value = file }
=======
      reader.onload = (ev) => { 
        fotoCedula.value = ev.target.result
        fotoFile.value = file
      }
>>>>>>> Stashed changes
      reader.readAsDataURL(file)
    }
  }
  input.click()
}

const enviarRegistro = async () => {
<<<<<<< Updated upstream
=======
  errorMsg.value = ''
  
  // Validar campos
>>>>>>> Stashed changes
  if (!validarPaso(1) || !validarPaso(2) || !validarPaso(3)) {
    alert('Por favor completa todos los campos obligatorios')
    return
  }
  enviando.value = true
  try {
<<<<<<< Updated upstream
    const formData = new FormData()
    formData.append('nombre', registro.nombre.trim())
    formData.append('cedula', registro.cedula.trim())
    formData.append('telefono', telefonoCompleto.value)
    formData.append('email', (registro.email || '').trim())
    formData.append('direccion', registro.direccion.trim())
    formData.append('referencia_nombre', registro.referencia_nombre.trim())
    formData.append('referencia_telefono', registro.referencia_telefono.trim())
    formData.append('referencia_parentesco', registro.referencia_parentesco.trim())
    if (fotoFile.value) formData.append('cedula_foto', fotoFile.value)
    const result = await registrarCliente(formData)
    if (result.success) {
      if (result.pin) localStorage.setItem('financoop_pin_temp', result.pin)
      router.push('/registro-exitoso/' + encodeURIComponent(registro.cedula))
    } else {
      alert('Error: ' + (result.error || 'No se pudo registrar'))
    }
=======
    // Datos en JSON
    const datosCliente = {
      nombre: registro.nombre.trim(),
      cedula: registro.cedula.trim(),
      telefono: telefonoCompleto.value,
      email: (registro.email || '').trim(),
      direccion: registro.direccion.trim(),
      referencia_nombre: registro.referencia_nombre.trim(),
      referencia_telefono: registro.referencia_telefono.trim(),
      referencia_parentesco: registro.referencia_parentesco.trim()
    }

    console.log('📦 Enviando datos:', datosCliente)

    const token = localStorage.getItem('token') || ''
    
    const response = await fetch('http://localhost:8000/clientes', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': token ? `Bearer ${token}` : ''
      },
      body: JSON.stringify(datosCliente)
    })

    const data = await response.json()

    if (!response.ok) {
      let errorMsgText = 'Error al registrar'
      if (data.detail) {
        if (Array.isArray(data.detail)) {
          errorMsgText = data.detail.map(e => `${e.loc.join('.')}: ${e.msg}`).join('\n')
        } else if (typeof data.detail === 'string') {
          errorMsgText = data.detail
        } else {
          errorMsgText = JSON.stringify(data.detail)
        }
      }
      throw new Error(errorMsgText)
    }

    console.log('✅ Cliente registrado:', data)
    
    // Guardar PIN si existe
    if (data.pin) {
      localStorage.setItem('financoop_pin_temp', data.pin)
    }
    
    // Si hay foto, subirla después
    if (fotoFile.value && data.id) {
      try {
        const fotoFormData = new FormData()
        fotoFormData.append('cedula_foto', fotoFile.value)
        
        await fetch(`http://localhost:8000/clientes/${data.id}/foto`, {
          method: 'POST',
          headers: {
            'Authorization': token ? `Bearer ${token}` : ''
          },
          body: fotoFormData
        })
        console.log('📸 Foto subida exitosamente')
      } catch (fotoErr) {
        console.warn('⚠️ No se pudo subir la foto:', fotoErr)
      }
    }
    
    // Redirigir a éxito
    router.push(`/registro-exitoso/${encodeURIComponent(registro.cedula)}`)

>>>>>>> Stashed changes
  } catch (err) {
    alert('Error al registrar. Intenta de nuevo.\n\n' + err.message)
  } finally {
    enviando.value = false
  }
}
</script>

<style scoped>
.register-wrapper {
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
  max-width: 480px;
  padding: 20px;
}

.glass-card {
  background: rgba(255,255,255,0.04) !important;
  backdrop-filter: blur(20px) !important;
  -webkit-backdrop-filter: blur(20px) !important;
  border: 1px solid rgba(255,255,255,0.06);
  border-radius: 24px !important;
}

.register-title {
  font-size: 22px;
  font-weight: 700;
  color: #ffffff;
}

.register-sub {
  font-size: 13px;
  color: rgba(255,255,255,0.4);
}

.flat {
  background: transparent !important;
}

.codigo-pais {
  flex-shrink: 0;
  margin-right: 8px;
}

.codigo-pais :deep(.v-field) {
  border-radius: 8px 0 0 8px !important;
  background: rgba(255,255,255,0.04) !important;
}

.telefono-input {
  flex: 1;
}

.telefono-input :deep(.v-field) {
  border-radius: 0 8px 8px 0 !important;
  background: rgba(255,255,255,0.04) !important;
}

:deep(.v-stepper) {
  background: transparent !important;
}

:deep(.v-stepper-item) {
  color: rgba(255,255,255,0.3) !important;
}

:deep(.v-stepper-item--selected) {
  color: #4facfe !important;
}

:deep(.v-stepper-item--complete) {
  color: #4caf50 !important;
}

:deep(.v-stepper-divider) {
  border-color: rgba(255,255,255,0.06) !important;
}

:deep(.v-text-field .v-field),
:deep(.v-textarea .v-field),
:deep(.v-select .v-field) {
  background: rgba(255,255,255,0.04) !important;
  border-radius: 12px !important;
}

:deep(.v-text-field .v-field__input),
:deep(.v-textarea .v-field__input) {
  color: #ffffff !important;
}

:deep(.v-text-field .v-field__input::placeholder),
:deep(.v-textarea .v-field__input::placeholder) {
  color: rgba(255,255,255,0.2) !important;
}

:deep(.v-text-field .v-icon),
:deep(.v-textarea .v-icon),
:deep(.v-select .v-icon) {
  color: rgba(255,255,255,0.3) !important;
}

:deep(.v-field--focused) {
  box-shadow: 0 0 0 2px rgba(79, 172, 254, 0.15) !important;
}

:deep(.v-stepper-window) {
  margin: 0 !important;
  padding: 0 !important;
}

:deep(.v-stepper-window-item) {
  padding: 0 !important;
}
</style>