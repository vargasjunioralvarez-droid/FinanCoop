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

          <!-- Stepper custom -->
          <div class="stepper-custom">
            <div class="stepper-header">
              <div 
                v-for="n in 4" 
                :key="n" 
                class="step-item" 
                :class="{ active: paso === n, complete: paso > n }"
              >
                <div class="step-circle">
                  <v-icon size="14">{{ getStepIcon(n) }}</v-icon>
                </div>
                <div 
                  v-if="n < 4" 
                  class="step-line" 
                  :class="{ complete: paso > n }"
                ></div>
              </div>
            </div>
          </div>

          <!-- PASO 1 -->
          <div v-show="paso === 1" class="step-panel mt-3">
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
              inputmode="numeric"
            />
            
            <div class="phone-row mb-2">
              <div class="codigo-wrapper">
                <label class="codigo-label">Cod.</label>
                <select v-model="codigoPais" class="codigo-select">
                  <option v-for="c in codigosPaises" :key="c.codigo" :value="c.codigo">
                    {{ c.codigo }}
                  </option>
                </select>
              </div>
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
                inputmode="numeric"
                type="tel"
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
              <v-btn 
                color="#4facfe" 
                rounded="pill" 
                size="small" 
                @click="paso++" 
                :disabled="!validarPaso(1)"
              >
                Siguiente <v-icon end size="16">mdi-chevron-right</v-icon>
              </v-btn>
            </div>
          </div>

          <!-- PASO 2 -->
          <div v-show="paso === 2" class="step-panel mt-3">
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
            
            <div class="phone-row mb-2">
              <div class="codigo-wrapper">
                <label class="codigo-label">Cod.</label>
                <select v-model="codigoPaisReferencia" class="codigo-select">
                  <option v-for="c in codigosPaises" :key="c.codigo" :value="c.codigo">
                    {{ c.codigo }}
                  </option>
                </select>
              </div>
              <v-text-field 
                v-model="registro.referencia_telefono" 
                label="Teléfono de referencia *" 
                variant="outlined" 
                density="compact" 
                prepend-inner-icon="mdi-phone" 
                :rules="[v => !!v || 'Requerido']" 
                hide-details 
                class="telefono-input" 
                placeholder="4121234567"
                inputmode="numeric"
                type="tel"
              />
            </div>
            
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
                <v-icon start size="16">mdi-chevron-left</v-icon>Atrás
              </v-btn>
              <v-btn 
                color="#4facfe" 
                rounded="pill" 
                size="small" 
                @click="paso++" 
                :disabled="!validarPaso(2)"
              >
                Siguiente <v-icon end size="16">mdi-chevron-right</v-icon>
              </v-btn>
            </div>
          </div>

          <!-- PASO 3: Foto -->
          <div v-show="paso === 3" class="step-panel mt-3">
            <div class="text-center py-2">
              <v-icon 
                size="40" 
                :color="fotoCedula ? '#4caf50' : 'rgba(255,255,255,0.1)'" 
                class="mb-1"
              >
                {{ fotoCedula ? 'mdi-check-circle' : 'mdi-camera' }}
              </v-icon>
              <div v-if="!fotoCedula" class="text-caption text-medium-emphasis mb-2">
                Sube o toma foto de tu cédula
              </div>
              <div v-else class="text-caption text-success mb-2">✅ Foto cargada</div>
              
              <div class="d-flex gap-2 justify-center mb-2 flex-wrap">
                <v-btn 
                  color="#4facfe" 
                  rounded="pill" 
                  size="small" 
                  @click="abrirCamara"
                  class="mb-1"
                >
                  <v-icon start size="16">mdi-camera</v-icon>
                  Tomar foto
                </v-btn>
                <v-btn 
                  color="#6366f1" 
                  rounded="pill" 
                  size="small" 
                  @click="abrirGaleria"
                  class="mb-1"
                >
                  <v-icon start size="16">mdi-image</v-icon>
                  Galería
                </v-btn>
              </div>
              
              <div v-if="fotoCedula" class="mt-2">
                <v-img :src="fotoCedula" max-height="120" contain class="rounded" />
              </div>
            </div>
            <div class="d-flex justify-space-between mt-2">
              <v-btn variant="text" size="small" @click="paso--">
                <v-icon start size="16">mdi-chevron-left</v-icon>Atrás
              </v-btn>
              <v-btn 
                color="#4facfe" 
                rounded="pill" 
                size="small" 
                @click="paso++" 
                :disabled="!validarPaso(3)"
              >
                Siguiente <v-icon end size="16">mdi-chevron-right</v-icon>
              </v-btn>
            </div>
          </div>

          <!-- PASO 4: Revisión -->
          <div v-show="paso === 4" class="step-panel mt-3">
            <v-alert type="success" class="mb-2" density="compact">✅ Revisa tus datos</v-alert>
            <v-list density="compact" class="bg-transparent">
              <v-list-item>
                <v-list-item-title class="text-caption text-medium-emphasis">Nombre</v-list-item-title>
                <v-list-item-subtitle class="text-body-2">{{ registro.nombre }}</v-list-item-subtitle>
              </v-list-item>
              <v-list-item>
                <v-list-item-title class="text-caption text-medium-emphasis">Cédula</v-list-item-title>
                <v-list-item-subtitle class="text-body-2">{{ registro.cedula }}</v-list-item-subtitle>
              </v-list-item>
              <v-list-item>
                <v-list-item-title class="text-caption text-medium-emphasis">Teléfono</v-list-item-title>
                <v-list-item-subtitle class="text-body-2">{{ telefonoCompleto }}</v-list-item-subtitle>
              </v-list-item>
              <v-list-item>
                <v-list-item-title class="text-caption text-medium-emphasis">Dirección</v-list-item-title>
                <v-list-item-subtitle class="text-body-2">{{ registro.direccion }}</v-list-item-subtitle>
              </v-list-item>
              <v-list-item>
                <v-list-item-title class="text-caption text-medium-emphasis">Referencia</v-list-item-title>
                <v-list-item-subtitle class="text-body-2">
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
                <v-icon start size="16">mdi-chevron-left</v-icon>Atrás
              </v-btn>
              <v-btn 
                color="#4caf50" 
                rounded="pill" 
                size="small" 
                :loading="enviando" 
                @click="enviarRegistro"
              >
                <v-icon start size="16">mdi-send</v-icon>Enviar
              </v-btn>
            </div>
          </div>

          <!-- PANTALLA DE ÉXITO (sin PIN) -->
          <div v-if="registroExitoso" class="text-center py-4">
            <v-icon size="60" color="#4caf50" class="mb-2">mdi-check-circle</v-icon>
            <h2 class="text-h5 text-white mb-2">¡Registro Exitoso!</h2>
            <p class="text-body-2 text-medium-emphasis mb-4">
              Tu cuenta está en proceso de verificación.<br>
              Recibirás un SMS con tu PIN de acceso<br>
              cuando sea aprobada.
            </p>
            <v-btn 
              color="#4facfe" 
              rounded="pill" 
              @click="irAlLogin"
            >
              Entendido
            </v-btn>
          </div>

        </v-card-text>
      </v-card>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, computed } from 'vue'
import { useRouter } from 'vue-router'
import { Camera, CameraResultType, CameraSource } from '@capacitor/camera'

const router = useRouter()

const paso = ref(1)
const enviando = ref(false)
const registroExitoso = ref(false)
const fotoCedula = ref(null)
const fotoFile = ref(null)
const codigoPais = ref('+58')
const codigoPaisReferencia = ref('+58')

const API_URL = 'https://financoop.onrender.com'

const codigosPaises = [
  { codigo: '+58' },
  { codigo: '+57' },
  { codigo: '+593' },
  { codigo: '+54' },
  { codigo: '+56' },
  { codigo: '+51' },
  { codigo: '+52' },
  { codigo: '+34' },
  { codigo: '+1' }
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
const telefonoReferenciaCompleto = computed(() => `${codigoPaisReferencia.value}${registro.referencia_telefono}`)

const getStepIcon = (n) => {
  const icons = ['mdi-account', 'mdi-account-group', 'mdi-card-account-details', 'mdi-check']
  return icons[n - 1]
}

const validarPaso = (p) => {
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
  return true
}

const abrirCamara = async () => {
  try {
    const image = await Camera.getPhoto({
      quality: 90,
      allowEditing: false,
      resultType: CameraResultType.DataUrl,
      source: CameraSource.Camera
    })
    fotoCedula.value = image.dataUrl
    const res = await fetch(image.dataUrl)
    const blob = await res.blob()
    fotoFile.value = new File([blob], 'cedula.jpg', { type: 'image/jpeg' })
  } catch (err) {
    console.log('Cámara cancelada:', err)
  }
}

const abrirGaleria = async () => {
  try {
    const image = await Camera.getPhoto({
      quality: 90,
      allowEditing: false,
      resultType: CameraResultType.DataUrl,
      source: CameraSource.Photos
    })
    fotoCedula.value = image.dataUrl
    const res = await fetch(image.dataUrl)
    const blob = await res.blob()
    fotoFile.value = new File([blob], 'cedula.jpg', { type: 'image/jpeg' })
  } catch (err) {
    console.log('Galería cancelada:', err)
  }
}

const enviarRegistro = async () => {
  if (!validarPaso(1) || !validarPaso(2) || !validarPaso(3)) {
    alert('Por favor completa todos los campos obligatorios')
    return
  }
  enviando.value = true
  try {
    const datosCliente = {
      nombre: registro.nombre.trim(),
      cedula: registro.cedula.trim(),
      telefono: telefonoCompleto.value,
      email: (registro.email || '').trim(),
      direccion: registro.direccion.trim(),
      referencia_nombre: registro.referencia_nombre.trim(),
      referencia_telefono: telefonoReferenciaCompleto.value,
      referencia_parentesco: registro.referencia_parentesco.trim()
    }

    const response = await fetch(`${API_URL}/clientes`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(datosCliente)
    })

    const data = await response.json()

    if (!response.ok || data.error) {
      throw new Error(data.error || 'Error al registrar')
    }

    console.log('✅ Cliente registrado:', data)

    // Subir foto si existe
    if (fotoFile.value && data.id) {
      try {
        const fotoFormData = new FormData()
        fotoFormData.append('cedula_foto', fotoFile.value)
        await fetch(`${API_URL}/clientes/${data.id}/foto`, {
          method: 'POST',
          body: fotoFormData
        })
      } catch (fotoErr) {
        console.warn('⚠️ Foto:', fotoErr)
      }
    }

    // ✅ MOSTRAR PANTALLA DE ÉXITO (sin PIN)
    registroExitoso.value = true

  } catch (err) {
    alert('Error al registrar. Intenta de nuevo.\n\n' + err.message)
  } finally {
    enviando.value = false
  }
}

const irAlLogin = () => {
  router.push('/login')
}
</script>

<style scoped>
.register-wrapper {
  min-height: 100vh;
  background: #0a0e1a;
  position: relative;
  display: flex;
  align-items: flex-start;
  justify-content: center;
  padding-top: 20px;
  padding-bottom: 40px;
}

.bg-gradient {
  position: fixed;
  top: 0; left: 0; right: 0; bottom: 0;
  background: radial-gradient(ellipse at 20% 50%, rgba(79, 172, 254, 0.08), transparent 70%),
              radial-gradient(ellipse at 80% 50%, rgba(99, 102, 241, 0.08), transparent 70%);
  z-index: 0;
}

.page-content {
  position: relative;
  z-index: 1;
  width: 100%;
  max-width: 480px;
  padding: 16px;
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

/* Stepper */
.stepper-custom { padding: 8px 0; }
.stepper-header {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0;
}
.step-item { display: flex; align-items: center; }
.step-circle {
  width: 32px; height: 32px;
  border-radius: 50%;
  background: rgba(255,255,255,0.06);
  border: 2px solid rgba(255,255,255,0.15);
  display: flex;
  align-items: center;
  justify-content: center;
  color: rgba(255,255,255,0.4);
  transition: all 0.3s ease;
  flex-shrink: 0;
}
.step-item.active .step-circle {
  background: rgba(79, 172, 254, 0.15);
  border-color: #4facfe;
  color: #4facfe;
  box-shadow: 0 0 12px rgba(79, 172, 254, 0.3);
}
.step-item.complete .step-circle {
  background: rgba(76, 175, 80, 0.15);
  border-color: #4caf50;
  color: #4caf50;
}
.step-line {
  width: 24px; height: 2px;
  background: rgba(255,255,255,0.1);
  margin: 0 4px;
  transition: all 0.3s ease;
}
.step-line.complete { background: #4caf50; }

/* Contenido */
.step-panel { animation: fadeIn 0.3s ease; }
@keyframes fadeIn {
  from { opacity: 0; transform: translateY(8px); }
  to { opacity: 1; transform: translateY(0); }
}

/* Teléfono */
.phone-row {
  display: flex;
  gap: 6px;
  align-items: flex-end;
}
.codigo-wrapper {
  display: flex;
  flex-direction: column;
  flex-shrink: 0;
  width: 65px;
}
.codigo-label {
  font-size: 10px;
  color: rgba(255,255,255,0.4);
  margin-bottom: 2px;
  padding-left: 4px;
}
.codigo-select {
  width: 100%;
  height: 36px;
  background: rgba(255,255,255,0.04);
  border: 1px solid rgba(255,255,255,0.15);
  border-radius: 10px;
  color: #ffffff;
  font-size: 13px;
  padding: 0 4px;
  outline: none;
}
.codigo-select:focus {
  border-color: #4facfe;
  box-shadow: 0 0 0 2px rgba(79, 172, 254, 0.15);
}
.codigo-select option {
  background: #1a1f2e;
  color: #ffffff;
}
.telefono-input {
  flex: 1;
  min-width: 0;
}
.telefono-input :deep(.v-field) {
  border-radius: 12px !important;
  background: rgba(255,255,255,0.04) !important;
}

/* Campos */
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

.gap-2 { gap: 8px; }
.flex-wrap { flex-wrap: wrap; }

/* Responsive */
@media (max-width: 360px) {
  .page-content { padding: 12px; }
  .glass-card { border-radius: 16px !important; }
  .register-title { font-size: 20px; }
  .step-line { width: 16px; }
  .codigo-wrapper { width: 58px; }
  .codigo-select { font-size: 12px; height: 34px; }
}
@media (max-width: 320px) {
  .step-circle { width: 28px; height: 28px; }
  .step-line { width: 12px; }
  .codigo-wrapper { width: 55px; }
}
</style>