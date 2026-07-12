<template>
  <v-container class="fill-height" fluid>
    <v-row align="center" justify="center">
      <v-col cols="12" sm="8" md="4">
        <v-card class="elevation-12">
          <v-card-title class="text-center py-4">
            <h1 class="text-h5">🔐 FinanCoop</h1>
            <p class="text-caption text-medium-emphasis">Sistema de Administración</p>
          </v-card-title>
          
          <v-card-text>
            <v-form @submit.prevent="login">
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
                :loading="cargando"
                class="mt-2"
              >
                Ingresar al Sistema
              </v-btn>
            </v-form>
          </v-card-text>
          
          <v-card-actions class="justify-center pb-4">
            <span class="text-caption text-grey">Acceso solo para personal autorizado</span>
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

const username = ref('')
const password = ref('')
const cargando = ref(false)

// 🔥 URL de la API según el entorno
const API_URL = import.meta.env.VITE_API_URL || 'https://financoop.onrender.com'
console.log('🌐 API_URL:', API_URL)

const login = async () => {
  if (!username.value || !password.value) {
    alert('Ingresa usuario y contraseña')
    return
  }

  cargando.value = true

  try {
    const formData = new URLSearchParams()
    formData.append('username', username.value)
    formData.append('password', password.value)

    console.log('📡 Enviando login a:', `${API_URL}/auth/login`)
    console.log('📡 Datos:', formData.toString())

    const response = await fetch(`${API_URL}/auth/login`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded'
      },
      body: formData.toString()
    })

    console.log('📡 Status:', response.status)

    // Verificar que la respuesta sea JSON antes de parsear
    const contentType = response.headers.get('content-type')
    if (!contentType || !contentType.includes('application/json')) {
      const text = await response.text()
      console.error('❌ Respuesta no es JSON:', text)
      alert('❌ Error del servidor: respuesta inválida')
      return
    }

    const data = await response.json()
    console.log('📡 Response:', data)

    if (response.ok && data.access_token) {
      localStorage.setItem('admin_token', data.access_token)
      localStorage.setItem('admin_rol', data.rol)
      localStorage.setItem('admin_username', data.username)
      localStorage.setItem('admin_nombre', data.nombre)
      
      console.log('✅ Login exitoso:', data.username)
      
      if (data.rol === 'admin') {
        await router.push('/usuarios')
      } else {
        await router.push('/inicio')
      }
    } else {
      alert('❌ ' + (data.detail || 'Credenciales incorrectas'))
    }
  } catch (error) {
    console.error('❌ Error de login:', error)
    alert('❌ Error de conexión con el servidor')
  } finally {
    cargando.value = false
  }
}
</script>