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
import { useFinanCash } from '@/composables/useFinanCash'

const router = useRouter()
const { iniciarSesion } = useFinanCash()

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
// ✅ LOGIN DE CLIENTE
// ============================================================
const loginCliente = async () => {
  if (!cedula.value || !pin.value) {
    alert('Ingresa cédula y PIN')
    return
  }

  cargandoCliente.value = true
  try {
    const success = await iniciarSesion(cedula.value, pin.value)
    if (success) {
      router.push('/inicio')
    } else {
      alert('❌ Credenciales incorrectas')
    }
  } catch (error) {
    console.error('Error en login:', error)
    alert('❌ Error de conexión')
  } finally {
    cargandoCliente.value = false
  }
}

// ============================================================
// ✅ LOGIN DE ADMINISTRADOR
// ============================================================
const loginAdmin = async () => {
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

    if (data.access_token) {
      localStorage.setItem('admin_token', data.access_token)
      localStorage.setItem('admin_rol', data.rol)
      localStorage.setItem('admin_username', data.username)
      
      alert('✅ Login exitoso')
      router.push('/usuarios')
    } else {
      alert('❌ Credenciales incorrectas')
    }
  } catch (error) {
    console.error('Error en login:', error)
    alert('❌ Error de conexión')
  } finally {
    cargandoAdmin.value = false
  }
}
</script>