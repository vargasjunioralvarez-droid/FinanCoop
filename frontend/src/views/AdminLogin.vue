<template>
  <v-container class="fill-height" fluid>
    <v-row align="center" justify="center">
      <v-col cols="12" sm="8" md="4">
        <v-card class="elevation-12">
          <v-card-title class="text-center py-4">
            <h1 class="text-h5">🔐 Panel Administrativo</h1>
            <p class="text-caption text-medium-emphasis">Ingresa con tus credenciales</p>
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
                Ingresar
              </v-btn>
            </v-form>
          </v-card-text>
          <v-card-actions class="justify-center">
            <v-btn to="/" variant="text" size="small">Volver a la app</v-btn>
          </v-card-actions>
        </v-card>
      </v-col>
    </v-row>
  </v-container>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { api } from '@/config/api'

const username = ref('')
const password = ref('')
const cargando = ref(false)
const router = useRouter()

const login = async () => {
  if (!username.value || !password.value) {
    alert('Ingresa usuario y contraseña')
    return
  }

  cargando.value = true
  try {
    const formData = new FormData()
    formData.append('username', username.value)
    formData.append('password', password.value)

    const res = await fetch('https://financoop.onrender.com/auth/login', {
      method: 'POST',
      body: formData
    })

    const data = await res.json()

    if (data.access_token) {
      // Guardar token y datos del admin
      localStorage.setItem('admin_token', data.access_token)
      localStorage.setItem('admin_rol', data.rol)
      localStorage.setItem('admin_username', data.username)
      
      // ✅ Usar router.push para redirigir
      await router.push('/usuarios')
    } else {
      alert('❌ Credenciales incorrectas')
    }
  } catch (error) {
    console.error('Error en login:', error)
    alert('❌ Error de conexión')
  } finally {
    cargando.value = false
  }
}
</script>