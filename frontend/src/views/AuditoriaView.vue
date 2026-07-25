<template>
  <v-container fluid>
    <v-card class="glass-card rounded-xl" elevation="0">
      <v-card-title class="text-h5 font-weight-bold text-white pa-4">
        <v-icon color="#4facfe" class="mr-2">mdi-shield-check</v-icon>
        Registro de Auditoría
        <v-spacer />
        <v-btn color="primary" variant="outlined" @click="cargarLogs" :loading="cargando">
          <v-icon left>mdi-refresh</v-icon>
          Actualizar
        </v-btn>
      </v-card-title>
      
      <v-card-text class="pa-4">
        <!-- Filtros -->
        <v-row class="mb-4">
          <v-col cols="12" sm="4">
            <v-select
              v-model="filtros.accion"
              :items="acciones"
              label="Filtrar por acción"
              clearable
              variant="outlined"
              density="compact"
              hide-details
              color="white"
              style="color: white;"
              class="filter-select"
            />
          </v-col>
          <v-col cols="12" sm="4">
            <v-text-field
              v-model="filtros.usuario"
              label="Filtrar por usuario"
              clearable
              variant="outlined"
              density="compact"
              hide-details
              color="white"
              style="color: white;"
              class="filter-input"
            />
          </v-col>
          <v-col cols="12" sm="4">
            <v-btn color="#4facfe" @click="aplicarFiltros" block class="filter-btn">
              <v-icon left>mdi-filter</v-icon>
              Filtrar
            </v-btn>
          </v-col>
        </v-row>

        <!-- Tabla de logs -->
        <v-data-table
          :headers="headers"
          :items="logs"
          :loading="cargando"
          :items-per-page="20"
          class="audit-table"
          item-value="id"
        >
          <!-- Columna Acción con colores -->
          <template v-slot:[`item.accion`]="{ item }">
            <v-chip :color="colorAccion(item.accion)" size="small" dark>
              {{ item.accion }}
            </v-chip>
          </template>

          <!-- Columna Fecha formateada -->
          <template v-slot:[`item.fecha`]="{ item }">
            {{ formatearFecha(item.fecha) }}
          </template>

          <!-- Columna Detalles con botón -->
          <template v-slot:[`item.detalles`]="{ item }">
            <v-btn
              size="small"
              color="info"
              variant="text"
              @click="verDetalles(item)"
            >
              Ver
            </v-btn>
          </template>
        </v-data-table>

        <!-- Paginación -->
        <div class="d-flex justify-end mt-2">
          <span class="text-caption" style="color: rgba(255,255,255,0.4);">
            Total: {{ logs.length }} registros
          </span>
        </div>
      </v-card-text>
    </v-card>

    <!-- Modal de detalles -->
    <v-dialog v-model="dialogDetalles" max-width="900">
      <v-card class="glass-card rounded-xl">
        <v-card-title class="text-h6 text-white">
          <v-icon color="#4facfe" class="mr-2">mdi-information</v-icon>
          Detalles de Auditoría
          <v-spacer />
          <v-chip :color="colorAccion(logSeleccionado?.accion)" size="small" dark>
            {{ logSeleccionado?.accion }}
          </v-chip>
        </v-card-title>
        <v-card-text>
          <!-- Información básica siempre visible -->
          <v-row>
            <v-col cols="12">
              <v-sheet class="pa-3 rounded" style="background: rgba(255,255,255,0.03);">
                <v-row dense>
                  <v-col cols="6" md="3">
                    <span class="text-caption" style="color: rgba(255,255,255,0.3);">ID:</span>
                    <span class="text-caption text-white ml-1">{{ logSeleccionado?.id || 'N/A' }}</span>
                  </v-col>
                  <v-col cols="6" md="3">
                    <span class="text-caption" style="color: rgba(255,255,255,0.3);">Usuario:</span>
                    <span class="text-caption text-white ml-1">{{ logSeleccionado?.usuario_nombre || 'N/A' }}</span>
                  </v-col>
                  <v-col cols="6" md="3">
                    <span class="text-caption" style="color: rgba(255,255,255,0.3);">Rol:</span>
                    <span class="text-caption text-white ml-1">{{ logSeleccionado?.usuario_rol || 'N/A' }}</span>
                  </v-col>
                  <v-col cols="6" md="3">
                    <span class="text-caption" style="color: rgba(255,255,255,0.3);">Tabla:</span>
                    <span class="text-caption text-white ml-1">{{ logSeleccionado?.tabla || 'N/A' }}</span>
                  </v-col>
                  <v-col cols="6" md="3">
                    <span class="text-caption" style="color: rgba(255,255,255,0.3);">Registro ID:</span>
                    <span class="text-caption text-white ml-1">{{ logSeleccionado?.registro_id || 'N/A' }}</span>
                  </v-col>
                  <v-col cols="6" md="3">
                    <span class="text-caption" style="color: rgba(255,255,255,0.3);">IP:</span>
                    <span class="text-caption text-white ml-1">{{ logSeleccionado?.ip || 'N/A' }}</span>
                  </v-col>
                  <v-col cols="6" md="3">
                    <span class="text-caption" style="color: rgba(255,255,255,0.3);">Endpoint:</span>
                    <span class="text-caption text-white ml-1" style="word-break: break-all;">{{ logSeleccionado?.endpoint || 'N/A' }}</span>
                  </v-col>
                  <v-col cols="6" md="3">
                    <span class="text-caption" style="color: rgba(255,255,255,0.3);">Método:</span>
                    <span class="text-caption text-white ml-1">{{ logSeleccionado?.metodo_http || 'N/A' }}</span>
                  </v-col>
                  <v-col cols="12">
                    <span class="text-caption" style="color: rgba(255,255,255,0.3);">Fecha:</span>
                    <span class="text-caption text-white ml-1">{{ formatearFechaCompleta(logSeleccionado?.fecha) }}</span>
                  </v-col>
                  <v-col cols="12" v-if="logSeleccionado?.detalles">
                    <span class="text-caption" style="color: rgba(255,255,255,0.3);">Detalles:</span>
                    <span class="text-caption text-white ml-1">{{ logSeleccionado?.detalles }}</span>
                  </v-col>
                </v-row>
              </v-sheet>
            </v-col>
          </v-row>
          
          <!-- Datos antes/después (si existen) -->
          <v-row v-if="tieneDatosAdicionales">
            <v-col cols="12">
              <v-divider class="my-2" style="border-color: rgba(255,255,255,0.05);" />
            </v-col>
            <v-col cols="12" md="6">
              <div class="text-subtitle-2" style="color: rgba(255,255,255,0.4);">📦 Datos Anteriores</div>
              <pre class="json-view">{{ formatearJSON(logSeleccionado?.datos_antes) }}</pre>
            </v-col>
            <v-col cols="12" md="6">
              <div class="text-subtitle-2" style="color: rgba(255,255,255,0.4);">📦 Datos Nuevos</div>
              <pre class="json-view">{{ formatearJSON(logSeleccionado?.datos_despues) }}</pre>
            </v-col>
          </v-row>
          
          <!-- Mensaje si no hay datos antes/después -->
          <v-row v-else>
            <v-col cols="12">
              <v-divider class="my-2" style="border-color: rgba(255,255,255,0.05);" />
              <div class="text-center text-caption" style="color: rgba(255,255,255,0.3);">
                <v-icon color="rgba(255,255,255,0.2)" size="24">mdi-information-outline</v-icon>
                <div>No hay datos adicionales disponibles para esta acción</div>
              </div>
            </v-col>
          </v-row>
          
          <!-- Dispositivo -->
          <v-row>
            <v-col cols="12">
              <v-divider class="my-2" style="border-color: rgba(255,255,255,0.05);" />
              <div class="text-subtitle-2" style="color: rgba(255,255,255,0.4);">📱 Dispositivo</div>
              <div class="text-caption text-white" style="word-break: break-all; font-size: 0.7rem; opacity: 0.6;">
                {{ logSeleccionado?.user_agent || 'N/A' }}
              </div>
            </v-col>
          </v-row>
        </v-card-text>
        <v-card-actions>
          <v-btn @click="dialogDetalles = false" color="primary">Cerrar</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>
  </v-container>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue'
import { api } from '@/config/api'

const logs = ref([])
const cargando = ref(false)
const dialogDetalles = ref(false)
const logSeleccionado = ref(null)

const filtros = ref({
  accion: null,
  usuario: null
})

const acciones = [
  'LOGIN',
  'LOGIN_FAILED',
  'LOGOUT',
  'CONCILIAR',
  'REPORTAR_PAGO',
  'PAGAR_EFECTIVO',
  'CREAR_FINANCIAMIENTO',
  'APROBAR_FINANCIAMIENTO',
  'ELIMINAR_FINANCIAMIENTO',
  'CREAR_CLIENTE',
  'APROBAR_CLIENTE',
  'ELIMINAR_CLIENTE',
  'ACTUALIZAR_CLIENTE',
  'ACTUALIZAR_TASA',
  'ACTUALIZAR_NIVEL',
  'RESET_NIVELES',
  'ACTUALIZAR_CONFIG_PAGO',
  'COMPLETAR_FINANCIAMIENTO'
]

const headers = [
  { title: 'ID', key: 'id', width: 60 },
  { title: 'Fecha', key: 'fecha', width: 170 },
  { title: 'Usuario', key: 'usuario_nombre', width: 130 },
  { title: 'Rol', key: 'usuario_rol', width: 100 },
  { title: 'Acción', key: 'accion', width: 140 },
  { title: 'Tabla', key: 'tabla', width: 120 },
  { title: 'Registro', key: 'registro_id', width: 70 },
  { title: 'IP', key: 'ip', width: 120 },
  { title: 'Detalles', key: 'detalles', width: 80 }
]

const tieneDatosAdicionales = computed(() => {
  if (!logSeleccionado.value) return false
  return !!(logSeleccionado.value.datos_antes || logSeleccionado.value.datos_despues)
})

const colorAccion = (accion) => {
  const colores = {
    'LOGIN': 'success',
    'LOGIN_FAILED': 'error',
    'LOGOUT': 'info',
    'CONCILIAR': 'primary',
    'REPORTAR_PAGO': 'warning',
    'PAGAR_EFECTIVO': 'success',
    'CREAR_FINANCIAMIENTO': 'success',
    'APROBAR_FINANCIAMIENTO': 'primary',
    'ELIMINAR_FINANCIAMIENTO': 'error',
    'CREAR_CLIENTE': 'success',
    'APROBAR_CLIENTE': 'primary',
    'ELIMINAR_CLIENTE': 'error',
    'ACTUALIZAR_CLIENTE': 'warning',
    'ACTUALIZAR_TASA': 'warning',
    'ACTUALIZAR_NIVEL': 'warning',
    'RESET_NIVELES': 'error',
    'ACTUALIZAR_CONFIG_PAGO': 'warning',
    'COMPLETAR_FINANCIAMIENTO': 'purple'
  }
  return colores[accion] || 'grey'
}

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

const formatearFechaCompleta = (fecha) => {
  if (!fecha) return 'N/A'
  const d = new Date(fecha)
  return d.toLocaleString('es-VE', {
    day: '2-digit',
    month: 'long',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit'
  })
}

const formatearJSON = (data) => {
  if (!data) return 'No disponible'
  if (typeof data === 'string') return data
  try {
    return JSON.stringify(data, null, 2)
  } catch {
    return String(data)
  }
}

const cargarLogs = async () => {
  cargando.value = true
  try {
    const params = {}
    if (filtros.value.accion) params.accion = filtros.value.accion
    if (filtros.value.usuario) params.usuario_nombre = filtros.value.usuario
    
    const response = await api.get('/audit/logs', { params })
    logs.value = response.logs || []
  } catch (error) {
    console.error('Error cargando logs:', error)
    logs.value = []
  } finally {
    cargando.value = false
  }
}

const aplicarFiltros = () => {
  cargarLogs()
}

const verDetalles = (item) => {
  logSeleccionado.value = item
  dialogDetalles.value = true
}

onMounted(cargarLogs)
</script>

<style scoped>
.audit-table {
  background: transparent;
}

.json-view {
  background: rgba(0, 0, 0, 0.4);
  padding: 12px;
  border-radius: 8px;
  font-size: 11px;
  color: #4facfe;
  max-height: 250px;
  overflow: auto;
  margin-top: 4px;
  font-family: 'Courier New', monospace;
  white-space: pre-wrap;
  word-break: break-all;
}

.glass-card {
  background: rgba(255, 255, 255, 0.03) !important;
  backdrop-filter: blur(24px) !important;
  border: 1px solid rgba(255, 255, 255, 0.06) !important;
}

/* ✅ CORREGIR COLOR DE TEXTOS EN FILTROS */
:deep(.v-label) {
  color: rgba(255, 255, 255, 0.7) !important;
}

:deep(.v-select .v-field__input) {
  color: white !important;
}

:deep(.v-select .v-field__input input) {
  color: white !important;
}

:deep(.v-select .v-field__input input::placeholder) {
  color: rgba(255, 255, 255, 0.3) !important;
}

:deep(.v-text-field .v-field__input) {
  color: white !important;
}

:deep(.v-text-field .v-field__input input) {
  color: white !important;
}

:deep(.v-text-field .v-field__input input::placeholder) {
  color: rgba(255, 255, 255, 0.3) !important;
}

:deep(.v-select .v-field) {
  background: rgba(255, 255, 255, 0.05) !important;
  border-color: rgba(255, 255, 255, 0.1) !important;
}

:deep(.v-select .v-field--focused) {
  border-color: #4facfe !important;
}

:deep(.v-select .v-field__outline) {
  color: rgba(255, 255, 255, 0.2) !important;
}

:deep(.v-field__outline) {
  color: rgba(255, 255, 255, 0.2) !important;
}

:deep(.v-field--focused .v-field__outline) {
  color: #4facfe !important;
}

/* ✅ CORREGIR MENÚ DESPLEGABLE DEL SELECT */
:deep(.v-menu .v-list) {
  background: #1a1f3a !important;
}

:deep(.v-menu .v-list-item) {
  color: white !important;
}

:deep(.v-menu .v-list-item:hover) {
  background: rgba(79, 172, 254, 0.15) !important;
}

:deep(.v-menu .v-list-item--active) {
  background: rgba(79, 172, 254, 0.2) !important;
}

:deep(.v-menu .v-list-item-title) {
  color: white !important;
}

/* ✅ CORREGIR TABLA */
:deep(.v-data-table__td) {
  color: rgba(255, 255, 255, 0.8) !important;
  border-bottom-color: rgba(255, 255, 255, 0.05) !important;
}

:deep(.v-data-table-header__content) {
  color: rgba(255, 255, 255, 0.4) !important;
  font-weight: 600 !important;
  font-size: 0.7rem !important;
  text-transform: uppercase !important;
  letter-spacing: 0.5px !important;
}

:deep(.v-data-table-header) {
  background: rgba(255, 255, 255, 0.02) !important;
  border-bottom-color: rgba(255, 255, 255, 0.05) !important;
}

:deep(.v-data-table__tr) {
  border-bottom-color: rgba(255, 255, 255, 0.03) !important;
}

:deep(.v-data-table__tr:hover) {
  background: rgba(79, 172, 254, 0.03) !important;
}

/* ✅ CORREGIR PAGINACIÓN */
:deep(.v-data-table-footer) {
  color: rgba(255, 255, 255, 0.4) !important;
}

:deep(.v-data-table-footer .v-btn) {
  color: rgba(255, 255, 255, 0.6) !important;
}

:deep(.v-data-table-footer .v-btn:hover) {
  color: white !important;
}

/* ✅ BOTÓN FILTRAR */
.filter-btn {
  background: rgba(79, 172, 254, 0.15) !important;
  color: white !important;
  border-color: rgba(79, 172, 254, 0.3) !important;
  height: 40px !important;
}

.filter-btn:hover {
  background: rgba(79, 172, 254, 0.25) !important;
}

/* ✅ SCROLLBAR PERSONALIZADA */
.json-view::-webkit-scrollbar {
  width: 4px;
  height: 4px;
}

.json-view::-webkit-scrollbar-track {
  background: rgba(255, 255, 255, 0.05);
  border-radius: 4px;
}

.json-view::-webkit-scrollbar-thumb {
  background: rgba(79, 172, 254, 0.3);
  border-radius: 4px;
}

.json-view::-webkit-scrollbar-thumb:hover {
  background: rgba(79, 172, 254, 0.5);
}

/* ✅ RESPONSIVE */
@media (max-width: 600px) {
  :deep(.v-data-table) {
    font-size: 0.75rem !important;
  }
  
  :deep(.v-data-table__td) {
    padding: 4px 8px !important;
  }
  
  .json-view {
    font-size: 10px;
    padding: 8px;
    max-height: 150px;
  }
}
</style>