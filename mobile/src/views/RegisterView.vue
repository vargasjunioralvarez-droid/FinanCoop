<script setup>
import { ref, reactive, computed, onBeforeUnmount } from 'vue'
import { useRouter } from 'vue-router'
import { Camera, CameraResultType, CameraSource } from '@capacitor/camera'

const router = useRouter()

// Estados
const paso = ref(1)
const guardandoLocal = ref(false)
const registroExitoso = ref(false)
const fotoCedula = ref(null)
const fotoFile = ref(null)
const codigoPais = ref('+58')
const codigoPaisReferencia = ref('+58')
const errorEnvio = ref(null)
const enviandoRender = ref(false)

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
// ✅ NUEVA FUNCIÓN: ENVIAR A RENDER + GUARDAR LOCAL
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
    
    // ✅ 2. AGREGAR FOTO
    if (fotoFile.value) {
      formData.append('cedula_foto', fotoFile.value)
    }

    console.log('🌐 Enviando a Render:', 'https://financoop.onrender.com/clientes')
    console.log('📤 Datos:', {
      nombre: registro.nombre.trim(),
      cedula: registro.cedula.trim(),
      telefono: telefonoCompleto.value,
      tiene_foto: !!fotoFile.value
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

    console.log('📥 Respuesta:', data)

    // ✅ 5. VERIFICAR ÉXITO
    if (response.ok && data.success !== false) {
      console.log('✅ Registro exitoso en Render')
      
      // Guardar en localStorage como backup
      const solicitud = {
        ...registro,
        telefono: telefonoCompleto.value,
        referencia_telefono: telefonoReferenciaCompleto.value,
        tiene_foto: !!fotoCedula.value,
        fecha_solicitud: new Date().toISOString(),
        estado: 'PENDIENTE',
        enviado_a_render: true,
        render_id: data.id || null,
        render_respuesta: data
      }

      const solicitudesGuardadas = JSON.parse(localStorage.getItem('solicitudes_clientes') || '[]')
      solicitudesGuardadas.push(solicitud)
      localStorage.setItem('solicitudes_clientes', JSON.stringify(solicitudesGuardadas))

      registroExitoso.value = true
      
    } else {
      // ❌ FALLÓ ENVÍO A RENDER - Guardar localmente
      console.warn('⚠️ Falló envío a Render:', data.error || 'Error desconocido')
      
      const solicitud = {
        ...registro,
        telefono: telefonoCompleto.value,
        referencia_telefono: telefonoReferenciaCompleto.value,
        tiene_foto: !!fotoCedula.value,
        fecha_solicitud: new Date().toISOString(),
        estado: 'PENDIENTE',
        enviado_a_render: false,
        error: data.error || 'Error desconocido'
      }

      const solicitudesGuardadas = JSON.parse(localStorage.getItem('solicitudes_clientes') || '[]')
      solicitudesGuardadas.push(solicitud)
      localStorage.setItem('solicitudes_clientes', JSON.stringify(solicitudesGuardadas))

      // Mostrar éxito igual (porque quedó guardado local)
      registroExitoso.value = true
      errorEnvio.value = data.error || 'No se pudo conectar con el servidor, pero tu solicitud quedó guardada localmente.'
    }
    
  } catch (error) {
    console.error('❌ Error de red:', error)
    
    // 🔥 GUARDAR LOCALMENTE EN CASO DE ERROR DE RED
    const solicitud = {
      ...registro,
      telefono: telefonoCompleto.value,
      referencia_telefono: telefonoReferenciaCompleto.value,
      tiene_foto: !!fotoCedula.value,
      fecha_solicitud: new Date().toISOString(),
      estado: 'PENDIENTE',
      enviado_a_render: false,
      error: error.message || 'Error de conexión'
    }

    const solicitudesGuardadas = JSON.parse(localStorage.getItem('solicitudes_clientes') || '[]')
    solicitudesGuardadas.push(solicitud)
    localStorage.setItem('solicitudes_clientes', JSON.stringify(solicitudesGuardadas))

    registroExitoso.value = true
    errorEnvio.value = 'Error de conexión. Tu solicitud quedó guardada localmente y será enviada cuando tengas internet.'
    
  } finally {
    guardandoLocal.value = false
    enviandoRender.value = false
  }
}

const irAlLogin = () => {
  router.push('/login')
}

onBeforeUnmount(() => {
  // Limpiar
})
</script>

<!-- Resto del template igual pero con indicador de envío -->