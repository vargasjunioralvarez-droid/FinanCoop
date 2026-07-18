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
                autocomplete="username"
              />
              <v-text-field
                v-model="password"
                label="Contraseña"
                type="password"
                prepend-inner-icon="mdi-lock"
                variant="outlined"
                density="comfortable"
                required
                autocomplete="current-password"
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
import { api } from '@/config/api'

const router = useRouter()

const username = ref('')
const password = ref('')
const cargando = ref(false)

const login = async () => {
  if (!username.value || !password.value) {
    alert('Ingresa usuario y contraseña')
    return
  }

  cargando.value = true

  try {
    // ✅ NUEVO: Enviar como JSON (más seguro y limpio)
    const data = await api.post('/auth/login-json', {
      username: username.value,
      password: password.value
    })

    if (data.access_token) {
      localStorage.setItem('admin_token', data.access_token)
      localStorage.setItem('admin_rol', data.rol)
      localStorage.setItem('admin_username', data.username)
      localStorage.setItem('admin_nombre', data.nombre)
      
      window.location.href = data.rol === 'admin' ? '/usuarios' : '/inicio'
    } else {
      alert('❌ Credenciales incorrectas')
    }
  } catch (error) {
    const mensaje = error.response?.data?.detail || 'Error de conexión con el servidor'
    alert('❌ ' + mensaje)
  } finally {
    cargando.value = false
  }
}
</script>