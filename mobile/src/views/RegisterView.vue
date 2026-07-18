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
                <div v-for="n in 4" :key="n" class="step-item" :class="{ active: paso === n, complete: paso > n }">
                  <div class="step-circle">
                    <v-icon size="14">{{ getStepIcon(n) }}</v-icon>
                  </div>
                  <div v-if="n < 4" class="step-line" :class="{ complete: paso > n }"></div>
                </div>
              </div>
            </div>

            <!-- PASO 1: Datos Personales -->
            <div v-show="paso === 1" class="step-panel mt-3">
              <div class="field-wrapper mb-3">
                <label class="field-label">
                  <v-icon size="16" class="label-icon">mdi-account</v-icon>
                  Nombre completo *
                </label>
                <v-text-field v-model="registro.nombre" variant="outlined" density="compact" hide-details class="custom-field" placeholder="Ej: Juan Pérez" bg-color="rgba(255,255,255,0.06)" />
              </div>

              <div class="field-wrapper mb-3">
                <label class="field-label">
                  <v-icon size="16" class="label-icon">mdi-card-account-details</v-icon>
                  Cédula *
                </label>
                <v-text-field v-model="registro.cedula" variant="outlined" density="compact" hide-details class="custom-field" inputmode="numeric" placeholder="Ej: 12345678" bg-color="rgba(255,255,255,0.06)" />
              </div>
              
              <div class="field-wrapper mb-3">
                <label class="field-label">
                  <v-icon size="16" class="label-icon">mdi-phone</v-icon>
                  Teléfono *
                </label>
                <div class="phone-row">
                  <div class="codigo-wrapper">
                    <select v-model="codigoPais" class="codigo-select">
                      <option v-for="c in codigosPaises" :key="c.codigo" :value="c.codigo">{{ c.codigo }}</option>
                    </select>
                  </div>
                  <v-text-field v-model="registro.telefono" variant="outlined" density="compact" hide-details class="telefono-input custom-field" placeholder="Ej: 4121234567" inputmode="numeric" type="tel" bg-color="rgba(255,255,255,0.06)" />
                </div>
              </div>
              
              <div class="field-wrapper mb-3">
                <label class="field-label">
                  <v-icon size="16" class="label-icon">mdi-email</v-icon>
                  Email *
                </label>
                <v-text-field v-model="registro.email" variant="outlined" density="compact" type="email" hide-details class="custom-field" placeholder="Ej: correo@ejemplo.com" bg-color="rgba(255,255,255,0.06)" :error-messages="emailError" />
              </div>

              <div class="field-wrapper mb-3">
                <label class="field-label">
                  <v-icon size="16" class="label-icon">mdi-map-marker</v-icon>
                  Dirección completa *
                </label>
                <v-textarea v-model="registro.direccion" variant="outlined" density="compact" rows="1" hide-details class="custom-field" placeholder="Calle, urbanización, ciudad, estado" bg-color="rgba(255,255,255,0.06)" />
              </div>

              <div class="d-flex justify-end mt-2">
                <v-btn color="#4facfe" rounded="pill" size="small" @click="paso++" :disabled="!validarPaso(1)">
                  Siguiente <v-icon end size="16">mdi-chevron-right</v-icon>
                </v-btn>
              </div>
            </div>

            <!-- PASO 2: Referencia -->
            <div v-show="paso === 2" class="step-panel mt-3">
              <div class="field-wrapper mb-3">
                <label class="field-label">
                  <v-icon size="16" class="label-icon">mdi-account</v-icon>
                  Nombre de referencia *
                </label>
                <v-text-field v-model="registro.referencia_nombre" variant="outlined" density="compact" hide-details class="custom-field" placeholder="Ej: María García" bg-color="rgba(255,255,255,0.06)" />
              </div>
              
              <div class="field-wrapper mb-3">
                <label class="field-label">
                  <v-icon size="16" class="label-icon">mdi-phone</v-icon>
                  Teléfono de referencia *
                </label>
                <div class="phone-row">
                  <div class="codigo-wrapper">
                    <select v-model="codigoPaisReferencia" class="codigo-select">
                      <option v-for="c in codigosPaises" :key="c.codigo" :value="c.codigo">{{ c.codigo }}</option>
                    </select>
                  </div>
                  <v-text-field v-model="registro.referencia_telefono" variant="outlined" density="compact" hide-details class="telefono-input custom-field" placeholder="Ej: 4121234567" inputmode="numeric" type="tel" bg-color="rgba(255,255,255,0.06)" />
                </div>
              </div>
              
              <div class="field-wrapper mb-3">
                <label class="field-label">
                  <v-icon size="16" class="label-icon">mdi-account-heart</v-icon>
                  Parentesco *
                </label>
                <v-select v-model="registro.referencia_parentesco" :items="['Familiar', 'Amigo', 'Vecino', 'Compañero de trabajo', 'Otro']" variant="outlined" density="compact" hide-details class="custom-field" bg-color="rgba(255,255,255,0.06)" />
              </div>

              <div class="d-flex justify-space-between mt-2">
                <v-btn color="#4facfe" variant="tonal" rounded="pill" size="small" @click="paso--">
                  <v-icon start size="16">mdi-chevron-left</v-icon>Atrás
                </v-btn>
                <v-btn color="#4facfe" rounded="pill" size="small" @click="paso++" :disabled="!validarPaso(2)">
                  Siguiente <v-icon end size="16">mdi-chevron-right</v-icon>
                </v-btn>
              </div>
            </div>

            <!-- PASO 3: Foto de Cédula -->
            <div v-show="paso === 3" class="step-panel mt-3">
              <div class="foto-cedula-section">
                <div class="foto-icon-wrapper">
                  <v-icon size="56" :color="fotoCedula ? '#4caf50' : '#4facfe'">
                    {{ fotoCedula ? 'mdi-check-circle' : 'mdi-card-account-details' }}
                  </v-icon>
                </div>
                <h3 class="foto-title">Foto de tu Cédula de Identidad</h3>
                <p class="foto-subtitle" v-if="!fotoCedula">
                  Toma una foto clara de tu cédula por ambos lados. Asegúrate que se vean bien los datos.
                </p>
                <p class="foto-subtitle success-text" v-else>✅ Foto cargada correctamente</p>
                
                <div class="d-flex gap-2 justify-center mb-3 flex-wrap">
                  <v-btn color="#4facfe" rounded="pill" size="small" @click="abrirCamara" class="foto-btn">
                    <v-icon start size="16">mdi-camera</v-icon>Tomar foto
                  </v-btn>
                  <v-btn color="#6366f1" rounded="pill" size="small" @click="abrirGaleria" class="foto-btn">
                    <v-icon start size="16">mdi-image</v-icon>Galería
                  </v-btn>
                </div>
                
                <div v-if="fotoCedula" class="foto-preview">
                  <v-img :src="fotoCedula" max-height="180" contain class="rounded-lg" />
                </div>
                <div v-else class="foto-placeholder">
                  <v-icon size="64" color="rgba(255,255,255,0.1)">mdi-card-account-details-outline</v-icon>
                  <p class="text-caption mt-2" style="color: rgba(255,255,255,0.3);">Vista previa de la cédula</p>
                </div>
              </div>
              
              <div class="d-flex justify-space-between mt-3">
                <v-btn color="#4facfe" variant="tonal" rounded="pill" size="small" @click="paso--">
                  <v-icon start size="16">mdi-chevron-left</v-icon>Atrás
                </v-btn>
                <v-btn color="#4facfe" rounded="pill" size="small" @click="paso++" :disabled="!validarPaso(3)">
                  Siguiente <v-icon end size="16">mdi-chevron-right</v-icon>
                </v-btn>
              </div>
            </div>

            <!-- PASO 4: Revisión y Términos -->
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
                <v-list-item v-if="registro.email">
                  <v-list-item-title class="text-caption text-white" style="opacity: 0.6;">Email</v-list-item-title>
                  <v-list-item-subtitle class="text-body-2 text-white">{{ registro.email }}</v-list-item-subtitle>
                </v-list-item>
                <v-list-item>
                  <v-list-item-title class="text-caption text-white" style="opacity: 0.6;">Dirección</v-list-item-title>
                  <v-list-item-subtitle class="text-body-2 text-white">{{ registro.direccion }}</v-list-item-subtitle>
                </v-list-item>
                <v-list-item>
                  <v-list-item-title class="text-caption text-white" style="opacity: 0.6;">Referencia</v-list-item-title>
                  <v-list-item-subtitle class="text-body-2 text-white">{{ registro.referencia_nombre }} ({{ registro.referencia_parentesco }})</v-list-item-subtitle>
                </v-list-item>
                <v-list-item v-if="fotoCedula">
                  <v-list-item-title class="text-caption text-white" style="opacity: 0.6;">Cédula</v-list-item-title>
                  <v-list-item-subtitle class="text-success"><v-icon size="16" color="success">mdi-check-circle</v-icon>Foto cargada</v-list-item-subtitle>
                </v-list-item>
              </v-list>

              <!-- TÉRMINOS Y CONDICIONES -->
              <div class="terminos-section mt-3">
                <p class="text-caption font-weight-bold mb-2" style="color: #4facfe;">📋 Términos legales</p>
                
                <v-checkbox v-model="aceptoTerminos" color="#4facfe" hide-details density="compact" class="terminos-check">
                  <template v-slot:label>
                    <span class="text-caption text-white">Acepto los <a href="#" @click.prevent="verTerminos" style="color: #4facfe; text-decoration: underline;">Términos y Condiciones</a> del servicio</span>
                  </template>
                </v-checkbox>
                
                <v-checkbox v-model="aceptoDatos" color="#4facfe" hide-details density="compact" class="terminos-check mt-1">
                  <template v-slot:label>
                    <span class="text-caption text-white">Autorizo el tratamiento de mis <a href="#" @click.prevent="verPolitica" style="color: #4facfe; text-decoration: underline;">datos personales</a></span>
                  </template>
                </v-checkbox>
                
                <v-checkbox v-model="aceptoDeuda" color="#4facfe" hide-details density="compact" class="terminos-check mt-1">
                  <template v-slot:label>
                    <span class="text-caption text-white">Entiendo que la deuda es en <strong style="color: #4facfe;">USD</strong> y pago en <strong style="color: #4facfe;">Bs</strong> al cambio del día</span>
                  </template>
                </v-checkbox>
                
                <v-checkbox v-model="aceptoMora" color="#4facfe" hide-details density="compact" class="terminos-check mt-1">
                  <template v-slot:label>
                    <span class="text-caption text-white">Acepto el <strong style="color: #ffc107;">interés de mora</strong> en caso de atraso en los pagos</span>
                  </template>
                </v-checkbox>
              </div>
              
              <div v-if="errorEnvio" class="mt-2">
                <v-alert type="warning" density="compact" class="text-caption">
                  <v-icon start size="16">mdi-alert</v-icon>{{ errorEnvio }}
                </v-alert>
              </div>
              
              <div class="d-flex justify-space-between mt-3">
                <v-btn color="#4facfe" variant="tonal" rounded="pill" size="small" @click="paso--">
                  <v-icon start size="16">mdi-chevron-left</v-icon>Atrás
                </v-btn>
                <v-btn color="#4caf50" rounded="pill" size="small" @click="guardarRegistroLocal" :loading="guardandoLocal || enviandoRender" :disabled="guardandoLocal || enviandoRender || !puedeEnviar">
                  <v-icon start size="16">mdi-cloud-upload</v-icon>
                  {{ enviandoRender ? 'Enviando...' : 'Guardar Solicitud' }}
                </v-btn>
              </div>
            </div>
          </div>

          <!-- PANTALLA DE ÉXITO -->
          <div v-else class="text-center py-4">
            <div class="success-animation">
              <v-icon size="80" color="#4caf50" class="mb-3 success-icon">mdi-check-circle</v-icon>
            </div>
            <h2 class="text-h4 text-white mb-2 font-weight-bold">¡Solicitud Guardada!</h2>
            <v-divider class="my-3" style="border-color: rgba(255,255,255,0.06);" />
            <div class="info-messages text-left">
              <div class="info-item mb-3">
                <v-icon size="20" color="#4facfe" class="mr-2">mdi-account-check</v-icon>
                <span class="text-body-1 text-white font-weight-medium">Solicitud registrada correctamente</span>
                <p class="text-body-2 text-white mt-1 ml-7" style="opacity: 0.8;">Tu solicitud ha sido guardada y está pendiente de revisión.</p>
              </div>
              <div class="info-item mb-3">
                <v-icon size="20" color="#ffc107" class="mr-2">mdi-clock</v-icon>
                <span class="text-body-1 text-white font-weight-medium">En espera de aprobación</span>
                <p class="text-body-2 text-white mt-1 ml-7" style="opacity: 0.8;">Un administrador revisará tus datos y te aprobará en la plataforma.</p>
              </div>
              <div class="info-item">
                <v-icon size="20" color="#4caf50" class="mr-2">mdi-phone-message</v-icon>
                <span class="text-body-1 text-white font-weight-medium">Notificación por SMS</span>
                <p class="text-body-2 text-white mt-1 ml-7" style="opacity: 0.8;">Cuando seas aprobado, recibirás un SMS al número <strong class="text-white">{{ telefonoCompleto }}</strong> con tu PIN de acceso.</p>
              </div>
            </div>
            <v-divider class="my-4" style="border-color: rgba(255,255,255,0.06);" />
            <v-btn color="#4facfe" rounded="pill" size="x-large" @click="irAlLogin" block class="login-btn" height="56" elevation="4">
              <v-icon start size="24">mdi-login</v-icon>Volver al Login
            </v-btn>
            <p class="text-caption text-white mt-3" style="opacity: 0.6;">¿Ya tienes cuenta? Inicia sesión con tu PIN</p>
          </div>

        </v-card-text>
      </v-card>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, computed, watch } from 'vue'
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
const aceptoTerminos = ref(false)
const aceptoDatos = ref(false)
const aceptoDeuda = ref(false)
const aceptoMora = ref(false)
const emailError = ref('')

const codigosPaises = [
  { codigo: '+58' }, { codigo: '+57' }, { codigo: '+593' }, { codigo: '+54' },
  { codigo: '+56' }, { codigo: '+51' }, { codigo: '+52' }, { codigo: '+34' }, { codigo: '+1' }
]

const registro = reactive({
  nombre: '', cedula: '', telefono: '', email: '', direccion: '',
  referencia_nombre: '', referencia_telefono: '', referencia_parentesco: ''
})

// Computed
const telefonoCompleto = computed(() => `${codigoPais.value}${registro.telefono}`)
const telefonoReferenciaCompleto = computed(() => `${codigoPaisReferencia.value}${registro.referencia_telefono}`)
const puedeEnviar = computed(() => aceptoTerminos.value && aceptoDatos.value && aceptoDeuda.value && aceptoMora.value)

// Validación de email
// ✅ CORRECTO
watch(() => registro.email, (val) => {
  if (!val || val.length === 0) {
    emailError.value = 'El email es obligatorio'
  } else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(val)) {
    emailError.value = 'Ingresa un email válido (ej: correo@ejemplo.com)'
  } else {
    emailError.value = ''
  }
})

const getStepIcon = (n) => {
  const icons = ['mdi-account', 'mdi-account-group', 'mdi-card-account-details', 'mdi-check']
  return icons[n - 1]
}

const validarPaso = (p) => {
  if (p === 1) {
    const emailValido = registro.email && /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(registro.email)
    return registro.nombre && registro.cedula && /^\d+$/.test(registro.cedula) &&
           registro.telefono && /^\d+$/.test(registro.telefono) && registro.direccion && emailValido
  }
  if (p === 2) {
    return registro.referencia_nombre && registro.referencia_telefono && /^\d+$/.test(registro.referencia_telefono) && registro.referencia_parentesco
  }
  if (p === 3) return !!fotoCedula.value
  return true
}

const abrirCamara = async () => {
  try {
    const image = await Camera.getPhoto({ quality: 90, allowEditing: false, resultType: CameraResultType.DataUrl, source: CameraSource.Camera })
    fotoCedula.value = image.dataUrl
    const res = await fetch(image.dataUrl); const blob = await res.blob()
    fotoFile.value = new File([blob], 'cedula.jpg', { type: 'image/jpeg' })
  } catch (err) { console.log('Cámara cancelada:', err) }
}

const abrirGaleria = async () => {
  try {
    const image = await Camera.getPhoto({ quality: 90, allowEditing: false, resultType: CameraResultType.DataUrl, source: CameraSource.Photos })
    fotoCedula.value = image.dataUrl
    const res = await fetch(image.dataUrl); const blob = await res.blob()
    fotoFile.value = new File([blob], 'cedula.jpg', { type: 'image/jpeg' })
  } catch (err) { console.log('Galería cancelada:', err) }
}

const verTerminos = () => {
  alert(`TÉRMINOS Y CONDICIONES - FinanCoop

📋 CONDICIONES DEL SERVICIO:
1. El financiamiento otorgado está sujeto a verificación de datos personales, referencias y capacidad de pago.
2. La deuda se mantiene en DÓLARES ESTADOUNIDENSES (USD) como moneda de referencia.
3. Los pagos se realizan en BOLÍVARES (Bs) al tipo de cambio vigente del día del pago.
4. El incumplimiento en los pagos generará intereses de mora según el nivel de crédito asignado.

⚖️ CONSECUENCIAS LEGALES POR INCUMPLIMIENTO:
5. El retraso mayor a 60 días será reportado a las centrales de riesgo crediticio.
6. FinanCoop se reserva el derecho de iniciar acciones legales por la vía civil para el cobro de deudas vencidas.
7. Los costos legales y honorarios de abogados por gestión de cobranza serán asumidos por el deudor.
8. El contrato de financiamiento constituye título ejecutivo según el Código de Comercio vigente.

✅ DECLARACIÓN DEL SOLICITANTE:
9. Declaro que los datos proporcionados son verídicos y autorizo su verificación.
10. Acepto que FinanCoop se reserva el derecho de admisión y puede rechazar mi solicitud sin expresión de causa.
11. Autorizo a FinanCoop a contactarme por SMS, WhatsApp o llamada telefónica para gestión de cobranza.`)
}

const verPolitica = () => {
  alert(`POLÍTICA DE PRIVACIDAD - FinanCoop

🔒 USO DE DATOS PERSONALES:
Sus datos personales (nombre, cédula, teléfono, dirección, referencias) serán utilizados ÚNICAMENTE para:
- Verificación de identidad y capacidad de pago
- Gestión y seguimiento de créditos
- Notificaciones de pago y vencimientos
- Reportes a centrales de riesgo (en caso de mora)

🛡️ PROTECCIÓN DE DATOS:
- No compartimos, vendemos ni cedemos sus datos a terceros con fines comerciales
- Sus datos se almacenan con cifrado y medidas de seguridad
- Usted tiene derecho a solicitar la rectificación o eliminación de sus datos

📞 CONTACTO:
Para cualquier consulta sobre sus datos, comuníquese con su cooperativa más cercana.`)
}


const guardarRegistroLocal = async () => {
  if (!validarPaso(1) || !validarPaso(2) || !validarPaso(3)) {
    alert('Por favor completa todos los campos obligatorios'); return
  }

  guardandoLocal.value = true; enviandoRender.value = true; errorEnvio.value = null
  
  try {
    const formData = new FormData()
    formData.append('nombre', registro.nombre.trim())
    formData.append('cedula', registro.cedula.trim())
    formData.append('telefono', telefonoCompleto.value)
    formData.append('email', (registro.email || '').trim())
    formData.append('direccion', registro.direccion.trim())
    formData.append('referencia_nombre', registro.referencia_nombre.trim())
    formData.append('referencia_telefono', telefonoReferenciaCompleto.value)
    formData.append('referencia_parentesco', registro.referencia_parentesco.trim())
    
    if (fotoFile.value && fotoFile.value instanceof File) {
      formData.append('cedula_foto', fotoFile.value)
    } else if (fotoCedula.value && fotoCedula.value.startsWith('data:')) {
      formData.append('cedula_foto_base64', fotoCedula.value)
    }

    const response = await fetch('https://financoop.onrender.com/api/v1/clientes', { method: 'POST', body: formData })
    let data
    const contentType = response.headers.get('content-type')
    if (contentType && contentType.includes('application/json')) {
      data = await response.json()
    } else {
      data = { error: await response.text() }
    }

    if (response.ok && data.success !== false) {
      const solicitud = {
        nombre: registro.nombre.trim(), cedula: registro.cedula.trim(), telefono: telefonoCompleto.value,
        email: (registro.email || '').trim(), direccion: registro.direccion.trim(),
        referencia_nombre: registro.referencia_nombre.trim(), referencia_telefono: telefonoReferenciaCompleto.value,
        referencia_parentesco: registro.referencia_parentesco.trim(), tiene_foto: !!fotoCedula.value,
        url_cedula: data.cliente?.url_cedula || null, fecha_solicitud: new Date().toISOString(),
        estado: 'PENDIENTE', enviado_a_render: true, render_id: data.id || null
      }
      const solicitudesGuardadas = JSON.parse(localStorage.getItem('solicitudes_clientes') || '[]')
      solicitudesGuardadas.push(solicitud)
      localStorage.setItem('solicitudes_clientes', JSON.stringify(solicitudesGuardadas))
      registroExitoso.value = true
    } else {
      const solicitud = {
        nombre: registro.nombre.trim(), cedula: registro.cedula.trim(), telefono: telefonoCompleto.value,
        email: (registro.email || '').trim(), direccion: registro.direccion.trim(),
        referencia_nombre: registro.referencia_nombre.trim(), referencia_telefono: telefonoReferenciaCompleto.value,
        referencia_parentesco: registro.referencia_parentesco.trim(), tiene_foto: !!fotoCedula.value,
        url_cedula: null, fecha_solicitud: new Date().toISOString(), estado: 'PENDIENTE',
        enviado_a_render: false, error: data.error || 'Error desconocido'
      }
      const solicitudesGuardadas = JSON.parse(localStorage.getItem('solicitudes_clientes') || '[]')
      solicitudesGuardadas.push(solicitud)
      localStorage.setItem('solicitudes_clientes', JSON.stringify(solicitudesGuardadas))
      registroExitoso.value = true
      errorEnvio.value = 'No se pudo conectar con el servidor, pero tu solicitud quedó guardada localmente.'
    }
  } catch (error) {
    const solicitud = {
      nombre: registro.nombre.trim(), cedula: registro.cedula.trim(), telefono: telefonoCompleto.value,
      email: (registro.email || '').trim(), direccion: registro.direccion.trim(),
      referencia_nombre: registro.referencia_nombre.trim(), referencia_telefono: telefonoReferenciaCompleto.value,
      referencia_parentesco: registro.referencia_parentesco.trim(), tiene_foto: !!fotoCedula.value,
      url_cedula: null, fecha_solicitud: new Date().toISOString(), estado: 'PENDIENTE',
      enviado_a_render: false, error: error.message || 'Error de conexión'
    }
    const solicitudesGuardadas = JSON.parse(localStorage.getItem('solicitudes_clientes') || '[]')
    solicitudesGuardadas.push(solicitud)
    localStorage.setItem('solicitudes_clientes', JSON.stringify(solicitudesGuardadas))
    registroExitoso.value = true
    errorEnvio.value = 'Error de conexión. Tu solicitud quedó guardada localmente.'
  } finally {
    guardandoLocal.value = false; enviandoRender.value = false
  }
}

const irAlLogin = () => router.push('/login')
</script>

<style scoped>
.register-wrapper { min-height: 100vh; background: #0a0e1a; position: relative; display: flex; align-items: flex-start; justify-content: center; padding-top: 20px; padding-bottom: 40px; }
.bg-gradient { position: fixed; top: 0; left: 0; right: 0; bottom: 0; background: radial-gradient(ellipse at 20% 50%, rgba(79,172,254,0.08), transparent 70%), radial-gradient(ellipse at 80% 50%, rgba(99,102,241,0.08), transparent 70%); z-index: 0; }
.page-content { position: relative; z-index: 1; width: 100%; max-width: 480px; padding: 16px; }
.glass-card { background: rgba(255,255,255,0.04) !important; backdrop-filter: blur(20px) !important; -webkit-backdrop-filter: blur(20px) !important; border: 1px solid rgba(255,255,255,0.06); border-radius: 24px !important; }
.register-title { font-size: 22px; font-weight: 700; color: #ffffff; }
.register-sub { font-size: 13px; color: rgba(255,255,255,0.6); }
.stepper-custom { padding: 8px 0; }
.stepper-header { display: flex; align-items: center; justify-content: center; gap: 0; }
.step-item { display: flex; align-items: center; }
.step-circle { width: 32px; height: 32px; border-radius: 50%; background: rgba(255,255,255,0.06); border: 2px solid rgba(255,255,255,0.15); display: flex; align-items: center; justify-content: center; color: rgba(255,255,255,0.4); transition: all 0.3s ease; flex-shrink: 0; }
.step-item.active .step-circle { background: rgba(79,172,254,0.15); border-color: #4facfe; color: #4facfe; box-shadow: 0 0 12px rgba(79,172,254,0.3); }
.step-item.complete .step-circle { background: rgba(76,175,80,0.15); border-color: #4caf50; color: #4caf50; }
.step-line { width: 24px; height: 2px; background: rgba(255,255,255,0.1); margin: 0 4px; transition: all 0.3s ease; }
.step-line.complete { background: #4caf50; }
.step-panel { animation: fadeIn 0.3s ease; }
@keyframes fadeIn { from { opacity: 0; transform: translateY(8px); } to { opacity: 1; transform: translateY(0); } }
.field-wrapper { margin-bottom: 16px; }
.field-label { display: flex; align-items: center; gap: 6px; font-size: 13px; font-weight: 600; color: rgba(255,255,255,0.85); margin-bottom: 6px; padding-left: 4px; letter-spacing: 0.3px; }
.label-icon { color: #4facfe !important; opacity: 0.8; }
.custom-field :deep(.v-field) { border-radius: 12px !important; border: 1px solid rgba(255,255,255,0.15) !important; }
.custom-field :deep(.v-field:hover) { border-color: rgba(255,255,255,0.3) !important; }
.custom-field :deep(.v-field--focused) { border-color: #4facfe !important; box-shadow: 0 0 0 3px rgba(79,172,254,0.15) !important; }
.custom-field :deep(.v-label) { display: none !important; }
.custom-field :deep(.v-field__input) { color: #ffffff !important; padding-top: 8px !important; padding-bottom: 8px !important; }
.custom-field :deep(.v-field__input::placeholder) { color: rgba(255,255,255,0.5) !important; font-weight: 400 !important; font-size: 14px !important; opacity: 1 !important; }
.custom-field :deep(.v-field__prepend-inner > .v-icon) { color: rgba(255,255,255,0.4) !important; opacity: 1 !important; }
.phone-row { display: flex; gap: 6px; align-items: flex-start; }
.codigo-wrapper { display: flex; flex-direction: column; flex-shrink: 0; width: 65px; padding-top: 0; }
.codigo-select { width: 100%; height: 36px; background: rgba(255,255,255,0.06); border: 1px solid rgba(255,255,255,0.15); border-radius: 10px; color: #ffffff; font-size: 13px; padding: 0 4px; outline: none; margin-top: 0; }
.codigo-select:focus { border-color: #4facfe; box-shadow: 0 0 0 2px rgba(79,172,254,0.15); }
.codigo-select option { background: #1a1f2e; color: #ffffff; }
.telefono-input { flex: 1; min-width: 0; }
.gap-2 { gap: 8px; }
.flex-wrap { flex-wrap: wrap; }

/* Foto de cédula */
.foto-cedula-section { text-align: center; padding: 8px 0; }
.foto-icon-wrapper { margin-bottom: 8px; }
.foto-title { font-size: 16px; font-weight: 600; color: #ffffff; margin-bottom: 4px; }
.foto-subtitle { font-size: 12px; color: rgba(255,255,255,0.5); margin-bottom: 12px; }
.success-text { color: #4caf50 !important; }
.foto-btn { font-weight: 500; }
.foto-preview { border-radius: 12px; overflow: hidden; border: 2px solid rgba(76,175,80,0.3); }
.foto-placeholder { padding: 30px; background: rgba(255,255,255,0.02); border-radius: 12px; border: 2px dashed rgba(255,255,255,0.1); }

/* Términos */
.terminos-section { background: rgba(255,255,255,0.03); border-radius: 12px; padding: 12px; border: 1px solid rgba(255,255,255,0.06); }
.terminos-check :deep(.v-label) { font-size: 12px; opacity: 0.85; }

/* Éxito */
.success-animation { animation: scaleIn 0.6s ease; }
@keyframes scaleIn { 0% { transform: scale(0); opacity: 0; } 50% { transform: scale(1.2); } 100% { transform: scale(1); opacity: 1; } }
.success-icon { animation: pulse 2s infinite; }
@keyframes pulse { 0% { transform: scale(1); } 50% { transform: scale(1.05); } 100% { transform: scale(1); } }
.info-messages { background: rgba(255,255,255,0.03); border-radius: 16px; padding: 16px; border: 1px solid rgba(255,255,255,0.05); }
.info-item { padding: 4px 0; }
.info-item p { margin-bottom: 0; line-height: 1.4; }
.login-btn { background: linear-gradient(135deg, #4facfe 0%, #6366f1 100%) !important; color: white !important; font-weight: 700 !important; font-size: 16px !important; letter-spacing: 0.5px; text-transform: none !important; transition: all 0.3s ease !important; border-radius: 50px !important; }
.login-btn:hover { transform: translateY(-3px) !important; box-shadow: 0 12px 40px rgba(79,172,254,0.5) !important; }
.login-btn:active { transform: scale(0.97) !important; }

@media (max-width: 360px) {
  .page-content { padding: 12px; }
  .glass-card { border-radius: 16px !important; }
  .register-title { font-size: 20px; }
  .step-line { width: 16px; }
  .codigo-wrapper { width: 58px; }
  .codigo-select { font-size: 12px; height: 34px; }
}
</style>