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
// ✅ LOGIN DE CLIENTE - CORREGIDO PARA /auth/login-cliente
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
  console.log('📤 [LOGIN CLIENTE] Cédula:', cedula.value)

  try {
    // ✅ URL CORREGIDA: /auth/login-cliente (no /app/login)
    const url = 'https://financoop.onrender.com/auth/login-cliente'
    const body = JSON.stringify({ cedula: cedula.value, pin: pin.value })
    
    console.log('🌐 [LOGIN CLIENTE] URL:', url)
    console.log('🌐 [LOGIN CLIENTE] Body:', body)

    const response = await fetch(url, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: body
    })

    console.log('📥 [LOGIN CLIENTE] Status:', response.status, response.statusText)

    const data = await response.json()
    console.log('📥 [LOGIN CLIENTE] Respuesta:', JSON.stringify(data, null, 2))
    console.log('📥 [LOGIN CLIENTE] Claves:', Object.keys(data))

    // ✅ CORREGIDO: El backend devuelve "access_token", no "token"
    const token = data.access_token || data.token
    console.log('🔑 [LOGIN CLIENTE] ¿Token?:', !!token)

    if (token) {
      console.log('✅ [LOGIN CLIENTE] Login exitoso')
      console.log('💾 [LOGIN CLIENTE] Guardando token...')
      
      localStorage.setItem('financoop_token', token)
      localStorage.setItem('financoop_usuario', JSON.stringify(data.cliente || {}))
      localStorage.setItem('usuario', JSON.stringify(data.cliente || {}))
      
      console.log('🛣️ [LOGIN CLIENTE] Redirigiendo a /inicio...')
      await router.push('/inicio')
    } else {
      console.error('❌ [LOGIN CLIENTE] Sin token. Error:', data.detail || data.error || 'Desconocido')
      alert('❌ Credenciales incorrectas: ' + (data.detail || data.error || 'Verifica tus datos'))
    }
  } catch (error) {
    console.error('💥 [LOGIN CLIENTE] Error:', error.name, error.message)
    alert('❌ Error de conexión con el servidor')
  } finally {
    cargandoCliente.value = false
    console.log('🏁 [LOGIN CLIENTE] Finalizado')
  }
}

// ============================================================
// ✅ LOGIN DE ADMINISTRADOR (sin cambios, ya funcionaba)
// ============================================================
const loginAdmin = async () => {
  console.log('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━')
  console.log('🚀 [LOGIN ADMIN] INICIANDO')
  console.log('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━')
  
  if (!username.value || !password.value) {
    alert('Ingresa usuario y contraseña')
    return
  }

  cargandoAdmin.value = true

  try {
    const formData = new FormData()
    formData.append('username', username.value)
    formData.append('password', password.value)

    const res = await fetch('https://financoop.onrender.com/auth/login', {
      method: 'POST',
      body: formData
    })

    const data = await res.json()
    console.log('📥 [LOGIN ADMIN] Respuesta:', data)

    if (data.access_token) {
      localStorage.setItem('admin_token', data.access_token)
      localStorage.setItem('admin_rol', data.rol)
      localStorage.setItem('admin_username', data.username)
      
      alert('✅ Login exitoso')
      await router.push('/usuarios')
    } else {
      alert('❌ Credenciales incorrectas')
    }
  } catch (error) {
    console.error('💥 [LOGIN ADMIN] Error:', error)
    alert('❌ Error de conexión')
  } finally {
    cargandoAdmin.value = false
  }
}
</script>