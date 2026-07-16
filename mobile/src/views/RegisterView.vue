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

          <!-- FORMULARIO DE REGISTRO -->
          <div v-if="!registroExitoso">
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
              <div class="field-wrapper mb-3">
                <label class="field-label">
                  <v-icon size="16" class="label-icon">mdi-account</v-icon>
                  Nombre completo *
                </label>
                <v-text-field 
                  v-model="registro.nombre" 
                  variant="outlined" 
                  density="compact" 
                  hide-details 
                  class="custom-field" 
                  placeholder="Ej: Juan Pérez"
                  bg-color="rgba(255,255,255,0.04)"
                />
              </div>

              <div class="field-wrapper mb-3">
                <label class="field-label">
                  <v-icon size="16" class="label-icon">mdi-card-account-details</v-icon>
                  Cédula *
                </label>
                <v-text-field 
                  v-model="registro.cedula" 
                  variant="outlined" 
                  density="compact" 
                  hide-details 
                  class="custom-field" 
                  inputmode="numeric"
                  placeholder="Ej: 12345678"
                  bg-color="rgba(255,255,255,0.04)"
                />
              </div>
              
              <div class="field-wrapper mb-3">
                <label class="field-label">
                  <v-icon size="16" class="label-icon">mdi-phone</v-icon>
                  Teléfono *
                </label>
                <div class="phone-row">
                  <div class="codigo-wrapper">
                    <select v-model="codigoPais" class="codigo-select">
                      <option v-for="c in codigosPaises" :key="c.codigo" :value="c.codigo">
                        {{ c.codigo }}
                      </option>
                    </select>
                  </div>
                  <v-text-field 
                    v-model="registro.telefono" 
                    variant="outlined" 
                    density="compact" 
                    hide-details 
                    class="telefono-input custom-field" 
                    placeholder="Ej: 4121234567"
                    inputmode="numeric"
                    type="tel"
                    bg-color="rgba(255,255,255,0.04)"
                  />
                </div>
              </div>
              
              <div class="field-wrapper mb-3">
                <label class="field-label">
                  <v-icon size="16" class="label-icon">mdi-email</v-icon>
                  Email (opcional)
                </label>
                <v-text-field 
                  v-model="registro.email" 
                  variant="outlined" 
                  density="compact" 
                  type="email" 
                  hide-details 
                  class="custom-field" 
                  placeholder="Ej: correo@ejemplo.com"
                  bg-color="rgba(255,255,255,0.04)"
                />
              </div>

              <div class="field-wrapper mb-3">
                <label class="field-label">
                  <v-icon size="16" class="label-icon">mdi-map-marker</v-icon>
                  Dirección completa *
                </label>
                <v-textarea 
                  v-model="registro.direccion" 
                  variant="outlined" 
                  density="compact" 
                  rows="1" 
                  hide-details 
                  class="custom-field" 
                  placeholder="Calle, urbanización, ciudad, estado"
                  bg-color="rgba(255,255,255,0.04)"
                />
              </div>

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
              <div class="field-wrapper mb-3">
                <label class="field-label">
                  <v-icon size="16" class="label-icon">mdi-account</v-icon>
                  Nombre de referencia *
                </label>
                <v-text-field 
                  v-model="registro.referencia_nombre" 
                  variant="outlined" 
                  density="compact" 
                  hide-details 
                  class="custom-field" 
                  placeholder="Ej: María García"
                  bg-color="rgba(255,255,255,0.04)"
                />
              </div>
              
              <div class="field-wrapper mb-3">
                <label class="field-label">
                  <v-icon size="16" class="label-icon">mdi-phone</v-icon>
                  Teléfono de referencia *
                </label>
                <div class="phone-row">
                  <div class="codigo-wrapper">
                    <select v-model="codigoPaisReferencia" class="codigo-select">
                      <option v-for="c in codigosPaises" :key="c.codigo" :value="c.codigo">
                        {{ c.codigo }}
                      </option>
                    </select>
                  </div>
                  <v-text-field 
                    v-model="registro.referencia_telefono" 
                    variant="outlined" 
                    density="compact" 
                    hide-details 
                    class="telefono-input custom-field" 
                    placeholder="Ej: 4121234567"
                    inputmode="numeric"
                    type="tel"
                    bg-color="rgba(255,255,255,0.04)"
                  />
                </div>
              </div>
              
              <div class="field-wrapper mb-3">
                <label class="field-label">
                  <v-icon size="16" class="label-icon">mdi-account-heart</v-icon>
                  Parentesco *
                </label>
                <v-select 
                  v-model="registro.referencia_parentesco" 
                  :items="['Familiar', 'Amigo', 'Vecino', 'Compañero de trabajo', 'Otro']" 
                  variant="outlined" 
                  density="compact" 
                  hide-details 
                  class="custom-field" 
                  placeholder="Selecciona..."
                  bg-color="rgba(255,255,255,0.04)"
                />
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
                  :color="fotoCedula ? '#4caf50' : 'rgba(255,255,255,0.3)'" 
                  class="mb-1"
                >
                  {{ fotoCedula ? 'mdi-check-circle' : 'mdi-camera' }}
                </v-icon>
                <div v-if="!fotoCedula" class="text-caption text-white mb-2" style="opacity: 0.7;">
                  Sube o toma foto de tu cédula
                </div>
                <div v-else class="text-caption text-white mb-2" style="color: #4caf50 !important;">✅ Foto cargada</div>
                
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
                  <v-list-item-title class="text-caption text-white" style="opacity: 0.6;">Nombre</v-list-item-title>
                  <v-list-item-subtitle class="text-body-2 text-white">{{ registro.nombre }}</v-list-item-subtitle>
                </v-list-item>
                <v-list-item>
                  <v-list-item-title class="text-caption text-white" style="opacity: 0.6;">Cédula</v-list-item-title>
                  <v-list-item-subtitle class="text-body-2 text-white">{{ registro.cedula }}</v-list-item-subtitle>
                </v-list-item>
                <v-list-item>
                  <v-list-item-title class="text-caption text-white" style="opacity: 0.6;">Teléfono</v-list-item-title>
                  <v-list-item-subtitle class="text-body-2 text-white">{{ telefonoCompleto }}</v-list-item-subtitle>
                </v-list-item>
                <v-list-item>
                  <v-list-item-title class="text-caption text-white" style="opacity: 0.6;">Dirección</v-list-item-title>
                  <v-list-item-subtitle class="text-body-2 text-white">{{ registro.direccion }}</v-list-item-subtitle>
                </v-list-item>
                <v-list-item>
                  <v-list-item-title class="text-caption text-white" style="opacity: 0.6;">Referencia</v-list-item-title>
                  <v-list-item-subtitle class="text-body-2 text-white">
                    {{ registro.referencia_nombre }} ({{ registro.referencia_parentesco }})
                  </v-list-item-subtitle>
                </v-list-item>
                <v-list-item v-if="fotoCedula">
                  <v-list-item-title class="text-caption text-white" style="opacity: 0.6;">Cédula</v-list-item-title>
                  <v-list-item-subtitle class="text-success">
                    <v-icon size="16" color="success">mdi-check-circle</v-icon>
                    Foto cargada
                  </v-list-item-subtitle>
                </v-list-item>
              </v-list>
              
              <!-- Mensaje de error si falló el envío -->
              <div v-if="errorEnvio" class="mt-2">
                <v-alert type="warning" density="compact" class="text-caption">
                  <v-icon start size="16">mdi-alert</v-icon>
                  {{ errorEnvio }}
                </v-alert>
              </div>
              
              <div class="d-flex justify-space-between mt-2">
                <v-btn variant="text" size="small" @click="paso--">
                  <v-icon start size="16">mdi-chevron-left</v-icon>Atrás
                </v-btn>
                <v-btn 
                  color="#4caf50" 
                  rounded="pill" 
                  size="small" 
                  @click="guardarRegistroLocal" 
                  :loading="guardandoLocal || enviandoRender"
                  :disabled="guardandoLocal || enviandoRender"
                >
                  <v-icon start size="16">mdi-cloud-upload</v-icon>
                  {{ enviandoRender ? 'Enviando a servidor...' : 'Guardar Solicitud' }}
                </v-btn>
              </div>
            </div>
          </div>

          <!-- ✅ PANTALLA DE ÉXITO (SOLICITUD ENVIADA) - CON COLORES CORREGIDOS -->
          <div v-else class="text-center py-4">
            <div class="success-animation">
              <v-icon size="80" color="#4caf50" class="mb-3 success-icon">
                mdi-check-circle
              </v-icon>
            </div>
            
            <h2 class="text-h4 text-white mb-2 font-weight-bold">
              ¡Solicitud Guardada!
            </h2>
            
            <v-divider class="my-3" style="border-color: rgba(255,255,255,0.06);" />
            
            <div class="info-messages text-left">
              <div class="info-item mb-3">
                <v-icon size="20" color="#4facfe" class="mr-2">mdi-account-check</v-icon>
                <span class="text-body-1 text-white font-weight-medium">
                  Solicitud registrada correctamente
                </span>
                <p class="text-body-2 text-white mt-1 ml-7" style="opacity: 0.8;">
                  Tu solicitud ha sido guardada y está pendiente de revisión.
                </p>
              </div>
              
              <div class="info-item mb-3">
                <v-icon size="20" color="#ffc107" class="mr-2">mdi-clock</v-icon>
                <span class="text-body-1 text-white font-weight-medium">
                  En espera de aprobación
                </span>
                <p class="text-body-2 text-white mt-1 ml-7" style="opacity: 0.8;">
                  Un administrador revisará tus datos y te aprobará en la plataforma.
                </p>
              </div>
              
              <div class="info-item">
                <v-icon size="20" color="#4caf50" class="mr-2">mdi-phone-message</v-icon>
                <span class="text-body-1 text-white font-weight-medium">
                  Notificación por SMS
                </span>
                <p class="text-body-2 text-white mt-1 ml-7" style="opacity: 0.8;">
                  Cuando seas aprobado, recibirás un SMS al número 
                  <strong class="text-white">{{ telefonoCompleto }}</strong> con tu PIN de acceso.
                </p>
              </div>
            </div>
            
            <v-divider class="my-4" style="border-color: rgba(255,255,255,0.06);" />
            
            <v-btn 
              color="#4facfe" 
              rounded="pill" 
              size="x-large"
              @click="irAlLogin"
              block
              class="login-btn"
              height="56"
              elevation="4"
            >
              <v-icon start size="24">mdi-login</v-icon>
              Volver al Login
            </v-btn>
            
            <p class="text-caption text-white mt-3" style="opacity: 0.6;">
              ¿Ya tienes cuenta? Inicia sesión con tu PIN
            </p>
          </div>

        </v-card-text>
      </v-card>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onBeforeUnmount } from 'vue'
import { useRouter } from 'vue-router'
import { Camera, CameraResultType, CameraSource } from '@capacitor/camera'

const router = useRouter()

// Estados
const paso = ref(1)
const guardandoLocal = ref(false)
const enviandoRender = ref(false)
const registroExitoso = ref(false)
const fotoCedula = ref(null)
const fotoFile = ref(null)
const errorEnvio = ref(null)
const codigoPais = ref('+58')
const codigoPaisReferencia = ref('+58')

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

// Computed
const telefonoCompleto = computed(() => `${codigoPais.value}${registro.telefono}`)
const telefonoReferenciaCompleto = computed(() => `${codigoPaisReferencia.value}${registro.referencia_telefono}`)

// Funciones
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

// ============================================================
// ✅ FUNCIÓN PRINCIPAL: ENVIAR A RENDER + GUARDAR LOCAL
// ============================================================
const guardarRegistroLocal = async () => {
  if (!validarPaso(1) || !validarPaso(2) || !validarPaso(3)) {
    alert('Por favor completa todos los campos obligatorios')
    return
  }

  guardandoLocal.value = true
  enviandoRender.value = true
  errorEnvio.value = null
  
  try {
    // ✅ 1. CREAR FORM DATA
    const formData = new FormData()
    formData.append('nombre', registro.nombre.trim())
    formData.append('cedula', registro.cedula.trim())
    formData.append('telefono', telefonoCompleto.value)
    formData.append('email', (registro.email || '').trim())
    formData.append('direccion', registro.direccion.trim())
    formData.append('referencia_nombre', registro.referencia_nombre.trim())
    formData.append('referencia_telefono', telefonoReferenciaCompleto.value)
    formData.append('referencia_parentesco', registro.referencia_parentesco.trim())
    
    // ✅ 2. AGREGAR FOTO - Intentar como File primero, si no como base64
    let fotoEnviada = false
    
    if (fotoFile.value && fotoFile.value instanceof File) {
      formData.append('cedula_foto', fotoFile.value)
      console.log('📸 Foto agregada como File:', fotoFile.value.name, fotoFile.value.size)
      fotoEnviada = true
    } else if (fotoCedula.value && fotoCedula.value.startsWith('data:')) {
      // Si tenemos dataUrl pero no File, enviar como base64
      formData.append('cedula_foto_base64', fotoCedula.value)
      console.log('📸 Foto agregada como base64')
      fotoEnviada = true
    }
    
    if (!fotoEnviada) {
      console.warn('⚠️ No se pudo preparar la foto para envío')
    }

    console.log('🌐 Enviando a Render:', 'https://financoop.onrender.com/clientes')
    console.log('📤 Datos:', {
      nombre: registro.nombre.trim(),
      cedula: registro.cedula.trim(),
      telefono: telefonoCompleto.value,
      tiene_foto: fotoEnviada
    })

    // ✅ 3. ENVIAR A RENDER
    const response = await fetch('https://financoop.onrender.com/clientes', {
      method: 'POST',
      body: formData
    })

    console.log('📡 Status:', response.status)

    // ✅ 4. LEER RESPUESTA
    let data
    const contentType = response.headers.get('content-type')
    if (contentType && contentType.includes('application/json')) {
      data = await response.json()
    } else {
      const text = await response.text()
      console.log('📥 Respuesta texto:', text)
      data = { error: text || `HTTP ${response.status}` }
    }

    console.log('📥 Respuesta completa:', JSON.stringify(data, null, 2))

    // ✅ 5. VERIFICAR ÉXITO
    if (response.ok && data.success !== false) {
      console.log('✅ Registro exitoso en Render')
      console.log('✅ URL cédula:', data.cliente?.url_cedula || 'No disponible')
      
      // Guardar en localStorage como backup
      const solicitud = {
        nombre: registro.nombre.trim(),
        cedula: registro.cedula.trim(),
        telefono: telefonoCompleto.value,
        email: (registro.email || '').trim(),
        direccion: registro.direccion.trim(),
        referencia_nombre: registro.referencia_nombre.trim(),
        referencia_telefono: telefonoReferenciaCompleto.value,
        referencia_parentesco: registro.referencia_parentesco.trim(),
        tiene_foto: !!fotoCedula.value,
        url_cedula: data.cliente?.url_cedula || null,
        fecha_solicitud: new Date().toISOString(),
        estado: 'PENDIENTE',
        enviado_a_render: true,
        render_id: data.id || null
      }

      const solicitudesGuardadas = JSON.parse(localStorage.getItem('solicitudes_clientes') || '[]')
      solicitudesGuardadas.push(solicitud)
      localStorage.setItem('solicitudes_clientes', JSON.stringify(solicitudesGuardadas))

      registroExitoso.value = true
      
    } else {
      // ❌ FALLÓ ENVÍO A RENDER - Guardar localmente
      console.warn('⚠️ Falló envío a Render:', data.error || 'Error desconocido')
      
      const solicitud = {
        nombre: registro.nombre.trim(),
        cedula: registro.cedula.trim(),
        telefono: telefonoCompleto.value,
        email: (registro.email || '').trim(),
        direccion: registro.direccion.trim(),
        referencia_nombre: registro.referencia_nombre.trim(),
        referencia_telefono: telefonoReferenciaCompleto.value,
        referencia_parentesco: registro.referencia_parentesco.trim(),
        tiene_foto: !!fotoCedula.value,
        url_cedula: null,
        fecha_solicitud: new Date().toISOString(),
        estado: 'PENDIENTE',
        enviado_a_render: false,
        error: data.error || 'Error desconocido'
      }

      const solicitudesGuardadas = JSON.parse(localStorage.getItem('solicitudes_clientes') || '[]')
      solicitudesGuardadas.push(solicitud)
      localStorage.setItem('solicitudes_clientes', JSON.stringify(solicitudesGuardadas))

      registroExitoso.value = true
      errorEnvio.value = data.error || 'No se pudo conectar con el servidor, pero tu solicitud quedó guardada localmente.'
    }
    
  } catch (error) {
    console.error('❌ Error de red:', error)
    
    // 🔥 GUARDAR LOCALMENTE EN CASO DE ERROR DE RED
    const solicitud = {
      nombre: registro.nombre.trim(),
      cedula: registro.cedula.trim(),
      telefono: telefonoCompleto.value,
      email: (registro.email || '').trim(),
      direccion: registro.direccion.trim(),
      referencia_nombre: registro.referencia_nombre.trim(),
      referencia_telefono: telefonoReferenciaCompleto.value,
      referencia_parentesco: registro.referencia_parentesco.trim(),
      tiene_foto: !!fotoCedula.value,
      url_cedula: null,
      fecha_solicitud: new Date().toISOString(),
      estado: 'PENDIENTE',
      enviado_a_render: false,
      error: error.message || 'Error de conexión'
    }

    const solicitudesGuardadas = JSON.parse(localStorage.getItem('solicitudes_clientes') || '[]')
    solicitudesGuardadas.push(solicitud)
    localStorage.setItem('solicitudes_clientes', JSON.stringify(solicitudesGuardadas))

    registroExitoso.value = true
    errorEnvio.value = 'Error de conexión. Tu solicitud quedó guardada localmente.'
    
  } finally {
    guardandoLocal.value = false
    enviandoRender.value = false
  }
}

const irAlLogin = () => {
  router.push('/login')
}

onBeforeUnmount(() => {
  // No hay intervalos que limpiar
})
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
  color: rgba(255,255,255,0.6);
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

/* ============ LABELS EXTERNOS (NO FLOTANTES) ============ */
.field-wrapper {
  margin-bottom: 16px;
}

.field-label {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 13px;
  font-weight: 600;
  color: rgba(255,255,255,0.85);
  margin-bottom: 6px;
  padding-left: 4px;
  letter-spacing: 0.3px;
}

.label-icon {
  color: #4facfe !important;
  opacity: 0.8;
}

/* ============ CAMPOS SIN LABEL FLOTANTE ============ */
.custom-field :deep(.v-field) {
  border-radius: 12px !important;
  border: 1px solid rgba(255,255,255,0.12) !important;
}

.custom-field :deep(.v-field:hover) {
  border-color: rgba(255,255,255,0.25) !important;
}

.custom-field :deep(.v-field--focused) {
  border-color: #4facfe !important;
  box-shadow: 0 0 0 3px rgba(79, 172, 254, 0.15) !important;
}

/* 🔥 ELIMINAR LABEL FLOTANTE DE VUETIFY */
.custom-field :deep(.v-label) {
  display: none !important;
}

/* Texto del input */
.custom-field :deep(.v-field__input) {
  color: #ffffff !important;
  padding-top: 8px !important;
  padding-bottom: 8px !important;
}

/* Placeholder visible */
.custom-field :deep(.v-field__input::placeholder) {
  color: rgba(255,255,255,0.35) !important;
  font-weight: 400 !important;
  font-size: 14px !important;
  opacity: 1 !important;
}

/* Iconos dentro del campo */
.custom-field :deep(.v-field__prepend-inner > .v-icon) {
  color: rgba(255,255,255,0.4) !important;
  opacity: 1 !important;
}

/* Teléfono */
.phone-row {
  display: flex;
  gap: 6px;
  align-items: flex-start;
}
.codigo-wrapper {
  display: flex;
  flex-direction: column;
  flex-shrink: 0;
  width: 65px;
  padding-top: 0;
}
.codigo-select {
  width: 100%;
  height: 36px;
  background: rgba(255,255,255,0.04);
  border: 1px solid rgba(255,255,255,0.12);
  border-radius: 10px;
  color: #ffffff;
  font-size: 13px;
  padding: 0 4px;
  outline: none;
  margin-top: 0;
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

.gap-2 { gap: 8px; }
.flex-wrap { flex-wrap: wrap; }

/* ✅ ESTILOS DE LA PANTALLA DE ÉXITO */
.success-animation {
  animation: scaleIn 0.6s ease;
}

@keyframes scaleIn {
  0% { transform: scale(0); opacity: 0; }
  50% { transform: scale(1.2); }
  100% { transform: scale(1); opacity: 1; }
}

.success-icon {
  animation: pulse 2s infinite;
}

@keyframes pulse {
  0% { transform: scale(1); }
  50% { transform: scale(1.05); }
  100% { transform: scale(1); }
}

.info-messages {
  background: rgba(255, 255, 255, 0.03);
  border-radius: 16px;
  padding: 16px;
  border: 1px solid rgba(255, 255, 255, 0.05);
}

.info-item {
  padding: 4px 0;
}

.info-item p {
  margin-bottom: 0;
  line-height: 1.4;
}

/* ============ CORRECCIÓN DE COLORES ============ */
.info-messages .text-body-1,
.info-messages .text-body-2,
.info-messages .text-caption {
  color: #ffffff !important;
}

.info-messages .text-medium-emphasis {
  color: rgba(255, 255, 255, 0.8) !important;
}

.info-messages .text-white {
  color: #ffffff !important;
}

.info-messages strong {
  color: #ffffff !important;
}

/* 🔥 Botón de login */
.login-btn {
  background: linear-gradient(135deg, #4facfe 0%, #6366f1 100%) !important;
  color: white !important;
  font-weight: 700 !important;
  font-size: 16px !important;
  letter-spacing: 0.5px;
  text-transform: none !important;
  transition: all 0.3s ease !important;
  border-radius: 50px !important;
}

.login-btn:hover {
  transform: translateY(-3px) !important;
  box-shadow: 0 12px 40px rgba(79, 172, 254, 0.5) !important;
}

.login-btn:active {
  transform: scale(0.97) !important;
}

/* Responsive */
@media (max-width: 360px) {
  .page-content { padding: 12px; }
  .glass-card { border-radius: 16px !important; }
  .register-title { font-size: 20px; }
  .step-line { width: 16px; }
  .codigo-wrapper { width: 58px; }
  .codigo-select { font-size: 12px; height: 34px; }
  .info-messages { padding: 12px; }
  .field-label { font-size: 12px; }
}

@media (max-width: 320px) {
  .step-circle { width: 28px; height: 28px; }
  .step-line { width: 12px; }
  .codigo-wrapper { width: 55px; }
}
</style>