<template>
  <v-container fluid>
    <v-card class="glass-card rounded-xl" elevation="0">
      <v-card-title class="text-h5 font-weight-bold text-white pa-4">
        <v-icon color="#4facfe" class="mr-2">mdi-backup-restore</v-icon>
        Gestión de Backups
        <v-spacer />
        <v-btn 
          color="success" 
          @click="crearBackup" 
          :loading="cargando"
          class="mr-2"
        >
          <v-icon left>mdi-plus</v-icon>
          Crear Backup
        </v-btn>
        <v-btn 
          color="primary" 
          variant="outlined" 
          @click="cargarBackups" 
          :loading="cargando"
        >
          <v-icon left>mdi-refresh</v-icon>
          Actualizar
        </v-btn>
      </v-card-title>
      
      <v-card-text class="pa-4">
        <!-- Mensaje de éxito -->
        <v-alert
          v-if="mensaje"
          :type="tipoMensaje"
          class="mb-4"
          dismissible
          @click:close="mensaje = ''"
        >
          {{ mensaje }}
        </v-alert>

        <!-- Tabla de backups -->
        <v-data-table
          :headers="headers"
          :items="backups"
          :loading="cargando"
          :items-per-page="10"
          class="audit-table"
        >
          <!-- Columna Tamaño -->
          <template v-slot:[`item.tamaño_mb`]="{ item }">
            {{ item.tamaño_mb }} MB
          </template>

          <!-- Columna Fecha -->
          <template v-slot:[`item.fecha`]="{ item }">
            {{ formatearFecha(item.fecha) }}
          </template>

          <!-- Columna Acciones -->
          <template v-slot:[`item.acciones`]="{ item }">
            <v-btn
              size="small"
              color="warning"
              variant="text"
              @click="restaurarBackup(item.nombre)"
              :loading="cargando"
            >
              <v-icon small>mdi-restore</v-icon>
              Restaurar
            </v-btn>
            <v-btn
              size="small"
              color="error"
              variant="text"
              @click="descargarBackup(item.nombre)"
            >
              <v-icon small>mdi-download</v-icon>
              Descargar
            </v-btn>
          </template>
        </v-data-table>

        <!-- Estado del scheduler -->
        <div class="mt-4 text-caption" style="color: rgba(255,255,255,0.3);">
          <v-icon small color="rgba(255,255,255,0.3)">mdi-clock-outline</v-icon>
          Los backups automáticos se ejecutan todos los días a las 2:00 AM
        </div>
      </v-card-text>
    </v-card>

    <!-- Dialog de confirmación -->
    <v-dialog v-model="dialogConfirmacion" max-width="400">
      <v-card class="glass-card rounded-xl">
        <v-card-title class="text-h6 text-white">
          <v-icon color="warning" class="mr-2">mdi-alert</v-icon>
          ¿Restaurar backup?
        </v-card-title>
        <v-card-text class="text-white">
          <p>Esto sobrescribirá TODOS los datos actuales con los del backup:</p>
          <p class="font-weight-bold">{{ backupSeleccionado }}</p>
          <p class="text-caption" style="color: rgba(255,255,255,0.4);">
            Esta acción NO se puede deshacer.
          </p>
        </v-card-text>
        <v-card-actions>
          <v-btn @click="dialogConfirmacion = false" color="grey">Cancelar</v-btn>
          <v-btn @click="confirmarRestauracion" color="warning" :loading="cargando">
            Restaurar
          </v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>
  </v-container>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { api } from '@/config/api'

const backups = ref([])
const cargando = ref(false)
const mensaje = ref('')
const tipoMensaje = ref('success')
const dialogConfirmacion = ref(false)
const backupSeleccionado = ref('')

const headers = [
  { title: 'Archivo', key: 'nombre' },
  { title: 'Tamaño', key: 'tamaño_mb' },
  { title: 'Fecha', key: 'fecha' },
  { title: 'Acciones', key: 'acciones', sortable: false }
]

const formatearFecha = (fecha) => {
  if (!fecha) return 'N/A'
  const d = new Date(fecha)
  return d.toLocaleString('es-VE', {
    day: '2-digit',
    month: 'short',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit'
  })
}

const cargarBackups = async () => {
  cargando.value = true
  try {
    const response = await api.get('/admin/backup/listar')
    backups.value = response.backups || []
  } catch (error) {
    console.error('Error cargando backups:', error)
    mensaje.value = 'Error cargando la lista de backups'
    tipoMensaje.value = 'error'
  } finally {
    cargando.value = false
  }
}

const crearBackup = async () => {
  cargando.value = true
  mensaje.value = ''
  try {
    const response = await api.post('/admin/backup/crear')
    if (response.success) {
      mensaje.value = '✅ Backup creado correctamente'
      tipoMensaje.value = 'success'
      await cargarBackups()
    }
  } catch (error) {
    console.error('Error creando backup:', error)
    mensaje.value = '❌ Error creando backup'
    tipoMensaje.value = 'error'
  } finally {
    cargando.value = false
  }
}

const restaurarBackup = (nombre) => {
  backupSeleccionado.value = nombre
  dialogConfirmacion.value = true
}

const confirmarRestauracion = async () => {
  cargando.value = true
  dialogConfirmacion.value = false
  try {
    const response = await api.post('/admin/backup/restaurar', null, {
      params: { archivo: backupSeleccionado.value }
    })
    if (response.success) {
      mensaje.value = `✅ Backup ${backupSeleccionado.value} restaurado correctamente`
      tipoMensaje.value = 'success'
    }
  } catch (error) {
    console.error('Error restaurando backup:', error)
    mensaje.value = '❌ Error restaurando backup'
    tipoMensaje.value = 'error'
  } finally {
    cargando.value = false
    backupSeleccionado.value = ''
  }
}

const descargarBackup = (nombre) => {
  // Por ahora, solo descarga desde la URL directa
  // En producción, necesitarías un endpoint para servir archivos
  const url = `/api/v1/admin/backup/descargar?archivo=${nombre}`
  window.open(url, '_blank')
}

onMounted(cargarBackups)
</script>

<style scoped>
.glass-card {
  background: rgba(255, 255, 255, 0.03) !important;
  backdrop-filter: blur(24px) !important;
  border: 1px solid rgba(255, 255, 255, 0.06) !important;
}

.audit-table {
  background: transparent;
}

:deep(.v-data-table__td) {
  color: rgba(255, 255, 255, 0.8) !important;
}

:deep(.v-data-table-header__content) {
  color: rgba(255, 255, 255, 0.4) !important;
  font-weight: 600 !important;
  font-size: 0.7rem !important;
  text-transform: uppercase !important;
  letter-spacing: 0.5px !important;
}

:deep(.v-btn) {
  text-transform: none !important;
}
</style>