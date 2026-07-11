<template>
  <v-container>
    <v-card class="mx-auto" max-width="400">
      <v-card-title>Login Administrador</v-card-title>
      <v-card-text>
        <v-text-field v-model="username" label="Usuario" />
        <v-text-field v-model="password" label="Contraseña" type="password" />
      </v-card-text>
      <v-card-actions>
        <v-btn color="primary" @click="loginAdmin" block>Ingresar</v-btn>
      </v-card-actions>
    </v-card>
  </v-container>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { api } from '@/config/api'

const username = ref('')
const password = ref('')
const router = useRouter()

const loginAdmin = async () => {
  try {
    const formData = new FormData()
    formData.append('username', username.value)
    formData.append('password', password.value)
    
    const res = await fetch(`${api.baseURL}/auth/login`, {
      method: 'POST',
      body: formData
    })
    const data = await res.json()
    
    if (data.access_token) {
      localStorage.setItem('admin_token', data.access_token)
      localStorage.setItem('admin_rol', data.rol)
      router.push('/clientes-admin')
    }
  } catch (e) {
    alert('Error de login')
  }
}
</script>