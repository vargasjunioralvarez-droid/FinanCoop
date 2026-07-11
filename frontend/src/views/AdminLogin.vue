<template>
  <v-container class="fill-height" fluid>
    <v-row align="center" justify="center">
      <v-col cols="12" sm="8" md="4">
        <v-card class="elevation-12">
          <v-card-title class="text-center py-4">
            <h1 class="text-h5">🔐 FinanCoop</h1>
            <p class="text-caption text-medium-emphasis">Inicia sesión con tus credenciales</p>
          </v-card-title>
          
          <v-card-text>
            <v-tabs v-model="tipoLogin" color="primary" centered>
              <v-tab value="cliente">Cliente</v-tab>
              <v-tab value="admin">Administrador</v-tab>
            </v-tabs>

            <v-window v-model="tipoLogin" class="mt-4">
              <!-- ✅ LOGIN DE CLIENTE -->
              <v-window-item value="cliente">
                <v-form @submit.prevent="loginCliente">
                  <v-text-field
                    v-model="cedula"
                    label="Cédula"
                    prepend-inner-icon="mdi-card-account-details"
                    variant="outlined"
                    density="comfortable"
                    required
                  />
                  <v-text-field
                    v-model="pin"
                    label="PIN"
                    type="password"
                    prepend-inner-icon="mdi-lock"
                    variant="outlined"
                    density="comfortable"
                    required
                  />
                  <v-btn
                    type="submit"
                    color="primary"
                    block
                    size="large"
                    :loading="cargandoCliente"
                    class="mt-2"
                  >
                    Ingresar como Cliente
                  </v-btn>
                </v-form>
              </v-window-item>

              <!-- ✅ LOGIN DE ADMINISTRADOR -->
              <v-window-item value="admin">
                <v-form @submit.prevent="loginAdmin">
                  <v-text-field
                    v-model="username"
                    label="Usuario"
                    prepend-inner-icon="mdi-account"
                    variant="outlined"
                    density="comfortable"
                    required
                  />
                  <v-text-field
                    v-model="password"
                    label="Contraseña"
                    type="password"
                    prepend-inner-icon="mdi-lock"
                    variant="outlined"
                    density="comfortable"
                    required
                  />
                  <v-btn
                    type="submit"
                    color="primary"
                    block
                    size="large"
                    :loading="cargandoAdmin"
                    class="mt-2"
                  >
                    Ingresar como Administrador
                  </v-btn>
                </v-form>
              </v-window-item>
            </v-window>
          </v-card-text>
          
          <v-card-actions class="justify-center">
            <v-btn to="/registro" variant="text" size="small">¿No tienes cuenta? Regístrate</v-btn>
          </v-card-actions>
        </v-card>
      </v-col>
    </v-row>
  </v-container>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'

const router = useRouter()

// Estado del formulario
const tipoLogin = ref('cliente')

// Cliente
const cedula = ref('')
const pin = ref('')
const cargandoCliente = ref(false)

// Admin
const username = ref('')
const password = ref('')
const cargandoAdmin = ref(false)

// ============================================================
// ✅ LOGIN DE CLIENTE - CON LOGS DETALLADOS
// ============================================================
const loginCliente = async () => {
  console.log('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━')
  console.log('🚀 [LOGIN CLIENTE] INICIANDO PROCESO')
  console.log('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━')
  
  if (!cedula.value || !pin.value) {
    console.warn('⚠️ [LOGIN CLIENTE] Campos vacíos')
    alert('Ingresa cédula y PIN')
    return
  }

  cargandoCliente.value = true
  console.log('📤 [LOGIN CLIENTE] Cédula enviada:', cedula.value)
  console.log('📤 [LOGIN CLIENTE] PIN enviado:', '*'.repeat(pin.value.length))

  try {
    const url = 'https://financoop.onrender.com/app/login'
    const body = JSON.stringify({ cedula: cedula.value, pin: pin.value })
    
    console.log('🌐 [LOGIN CLIENTE] URL:', url)
    console.log('🌐 [LOGIN CLIENTE] Headers:', { 'Content-Type': 'application/json' })
    console.log('🌐 [LOGIN CLIENTE] Body:', body)

    const response = await fetch(url, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: body
    })

    console.log('📥 [LOGIN CLIENTE] Status HTTP:', response.status, response.statusText)
    console.log('📥 [LOGIN CLIENTE] Response OK?:', response.ok)

    const data = await response.json()
    console.log('📥 [LOGIN CLIENTE] Respuesta completa:', JSON.stringify(data, null, 2))
    console.log('📥 [LOGIN CLIENTE] Claves en respuesta:', Object.keys(data))

    // Verificar si existe token (puede ser token o access_token)
    const token = data.token || data.access_token
    console.log('🔑 [LOGIN CLIENTE] ¿Existe token?:', !!token)
    
    if (token) {
      console.log('✅ [LOGIN CLIENTE] Token encontrado:', token.substring(0, 30) + '...')
      console.log('💾 [LOGIN CLIENTE] Guardando en localStorage...')
      
      localStorage.setItem('financoop_token', token)
      localStorage.setItem('financoop_usuario', JSON.stringify(data.cliente || {}))
      localStorage.setItem('usuario', JSON.stringify(data.cliente || {}))
      
      // Verificar que se guardó correctamente
      const tokenGuardado = localStorage.getItem('financoop_token')
      console.log('💾 [LOGIN CLIENTE] Token guardado?:', !!tokenGuardado)
      console.log('💾 [LOGIN CLIENTE] Valor guardado:', tokenGuardado?.substring(0, 30) + '...')
      
      console.log('🛣️ [LOGIN CLIENTE] Redirigiendo a /inicio...')
      await router.push('/inicio')
      console.log('✅ [LOGIN CLIENTE] Redirección completada')
    } else {
      console.error('❌ [LOGIN CLIENTE] NO se encontró token en la respuesta')
      console.error('❌ [LOGIN CLIENTE] Mensaje de error:', data.error || data.detail || data.message || 'Sin mensaje específico')
      alert('❌ Credenciales incorrectas: ' + (data.error || data.detail || data.message || 'Verifica tus datos'))
    }
  } catch (error) {
    console.error('💥 [LOGIN CLIENTE] ERROR CAPTURADO:')
    console.error('💥 [LOGIN CLIENTE] Nombre:', error.name)
    console.error('💥 [LOGIN CLIENTE] Mensaje:', error.message)
    console.error('💥 [LOGIN CLIENTE] Stack:', error.stack)
    alert('❌ Error de conexión con el servidor')
  } finally {
    cargandoCliente.value = false
    console.log('🏁 [LOGIN CLIENTE] PROCESO FINALIZADO')
    console.log('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━')
  }
}

// ============================================================
// ✅ LOGIN DE ADMINISTRADOR - CON LOGS DETALLADOS
// ============================================================
const loginAdmin = async () => {
  console.log('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━')
  console.log('🚀 [LOGIN ADMIN] INICIANDO PROCESO')
  console.log('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━')
  
  if (!username.value || !password.value) {
    console.warn('⚠️ [LOGIN ADMIN] Campos vacíos')
    alert('Ingresa usuario y contraseña')
    return
  }

  cargandoAdmin.value = true
  console.log('📤 [LOGIN ADMIN] Username:', username.value)

  try {
    const url = 'https://financoop.onrender.com/auth/login'
    const formData = new FormData()
    formData.append('username', username.value)
    formData.append('password', password.value)
    
    console.log('🌐 [LOGIN ADMIN] URL:', url)
    console.log('🌐 [LOGIN ADMIN] FormData entries:', [...formData.entries()])

    const res = await fetch(url, {
      method: 'POST',
      body: formData
    })

    console.log('📥 [LOGIN ADMIN] Status HTTP:', res.status, res.statusText)

    const data = await res.json()
    console.log('📥 [LOGIN ADMIN] Respuesta completa:', JSON.stringify(data, null, 2))
    console.log('📥 [LOGIN ADMIN] Claves en respuesta:', Object.keys(data))

    const token = data.access_token || data.token
    console.log('🔑 [LOGIN ADMIN] ¿Existe token?:', !!token)

    if (token) {
      console.log('✅ [LOGIN ADMIN] Login exitoso')
      console.log('💾 [LOGIN ADMIN] Guardando token...')
      
      localStorage.setItem('admin_token', token)
      localStorage.setItem('admin_rol', data.rol || '')
      localStorage.setItem('admin_username', data.username || '')
      
      alert('✅ Login exitoso')
      await router.push('/usuarios')
    } else {
      console.error('❌ [LOGIN ADMIN] NO se encontró access_token')
      console.error('❌ [LOGIN ADMIN] Error:', data.error || data.detail || data.message)
      alert('❌ Credenciales incorrectas')
    }
  } catch (error) {
    console.error('💥 [LOGIN ADMIN] ERROR:', error.name, error.message)
    alert('❌ Error de conexión')
  } finally {
    cargandoAdmin.value = false
    console.log('🏁 [LOGIN ADMIN] PROCESO FINALIZADO')
    console.log('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━')
  }
}
</script>