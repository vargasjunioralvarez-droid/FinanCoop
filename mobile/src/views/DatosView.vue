<template>
  <v-container class="pa-4 datos-view">
    <div class="text-h6 font-weight-medium mb-4">Mis datos</div>

    <!-- Perfil -->
    <v-card class="mb-4 perfil-card" elevation="2">
      <v-card-text class="pa-4 text-center">
        <v-avatar size="64" :color="colorNivel(usuario.nivel)" class="mb-2">
          <v-icon size="32" color="white">{{ iconoNivel(usuario.nivel) }}</v-icon>
        </v-avatar>
        <div class="text-h6 font-weight-medium">{{ usuario.nombre }}</div>
        <div class="text-body-2 text-medium-emphasis mb-2">
          Nivel {{ usuario.nivel }} • {{ usuario.score }} puntos
        </div>
        <v-chip :color="colorNivel(usuario.nivel)" size="small" variant="tonal">
          {{ descripcionNivel(usuario.nivel) }}
        </v-chip>
      </v-card-text>
    </v-card>

    <!-- Mi nivel y beneficios -->
    <div class="text-subtitle-1 font-weight-medium mb-2">Mi nivel</div>
    <v-card class="mb-4" elevation="1">
      <v-card-text class="pa-3">
        <div class="d-flex align-center mb-3">
          <v-icon :color="colorNivel(usuario.nivel)" size="28" class="mr-3">{{ iconoNivel(usuario.nivel) }}</v-icon>
          <div>
            <div class="text-body-1 font-weight-medium text-capitalize">{{ usuario.nivel }}</div>
            <div class="text-caption text-medium-emphasis">{{ descripcionNivel(usuario.nivel) }}</div>
          </div>
        </div>
        <v-divider class="mb-3"></v-divider>
        <div class="text-caption text-medium-emphasis mb-2">Beneficios actuales:</div>
        <div class="d-flex flex-wrap gap-2">
          <v-chip size="small" variant="outlined" color="primary">
            <v-icon size="12" start>mdi-percent</v-icon>
            {{ nivelActual.entrada_pct || 0 }}% entrada
          </v-chip>
          <v-chip size="small" variant="outlined" color="primary">
            <v-icon size="12" start>mdi-calendar</v-icon>
            {{ nivelActual.cuotas_max || 0 }} cuotas máx
          </v-chip>
          <v-chip size="small" variant="outlined" color="primary">
            <v-icon size="12" start>mdi-currency-usd</v-icon>
            ${{ nivelActual.monto_max_usd || 0 }} límite
          </v-chip>
          <v-chip size="small" variant="outlined" color="primary">
            <v-icon size="12" start>mdi-alert</v-icon>
            {{ nivelActual.mora_diaria || 0 }}% mora/día
          </v-chip>
        </div>
      </v-card-text>
    </v-card>

    <!-- Estadísticas -->
    <div class="text-subtitle-1 font-weight-medium mb-2">Estadísticas</div>
    <v-card class="mb-4" elevation="1">
      <v-card-text class="pa-3">
        <div class="d-flex justify-space-between text-center">
          <div style="flex:1">
            <div class="text-h5 font-weight-medium">{{ usuario.total_compras || 0 }}</div>
            <div class="text-caption text-medium-emphasis">Compras</div>
          </div>
          <v-divider vertical></v-divider>
          <div style="flex:1">
            <div class="text-h5 font-weight-medium" style="color: rgb(var(--v-theme-success));">
              {{ usuario.cuotas_pagadas_tiempo || 0 }}
            </div>
            <div class="text-caption text-medium-emphasis">Puntuales</div>
          </div>
          <v-divider vertical></v-divider>
          <div style="flex:1">
            <div class="text-h5 font-weight-medium" style="color: rgb(var(--v-theme-warning));">
              {{ usuario.cuotas_con_mora || 0 }}
            </div>
            <div class="text-caption text-medium-emphasis">Con mora</div>
          </div>
        </div>
      </v-card-text>
    </v-card>

    <!-- Datos para pagar (tu estructura original mejorada) -->
    <div class="text-subtitle-1 font-weight-medium mb-2">Datos para pagar</div>

    <v-card class="mb-4" elevation="4" color="primary" dark>
      <v-card-text class="pa-4">
        <div class="text-h6 mb-4">📱 Pago Móvil</div>
        <div class="d-flex justify-space-between mb-2">
          <span class="text-grey-lighten-2">Banco:</span>
          <span class="font-weight-bold">{{ datosPago?.pago_movil?.banco }}</span>
        </div>
        <div class="d-flex justify-space-between mb-2">
          <span class="text-grey-lighten-2">Teléfono:</span>
          <span class="font-weight-bold text-h6">{{ datosPago?.pago_movil?.telefono }}</span>
        </div>
        <div class="d-flex justify-space-between mb-4">
          <span class="text-grey-lighten-2">Cédula:</span>
          <span class="font-weight-bold">{{ datosPago?.pago_movil?.cedula }}</span>
        </div>
        <v-btn block color="white" variant="outlined" rounded="pill" @click="copiarAlPortapapeles(datosPago?.pago_movil?.telefono)">
          <v-icon start>mdi-content-copy</v-icon>
          Copiar Teléfono
        </v-btn>
      </v-card-text>
    </v-card>

    <v-card class="mb-4" elevation="4">
      <v-card-text class="pa-4">
        <div class="text-h6 mb-4 text-primary">🏦 Transferencia</div>
        <div class="d-flex justify-space-between mb-2">
          <span class="text-medium-emphasis">Banco:</span>
          <span class="font-weight-bold">{{ datosPago?.transferencia?.banco }}</span>
        </div>
        <div class="d-flex justify-space-between mb-4">
          <span class="text-medium-emphasis">Cuenta:</span>
          <span class="font-weight-bold text-h6">{{ datosPago?.transferencia?.cuenta }}</span>
        </div>
        <v-btn block color="primary" variant="outlined" rounded="pill" @click="copiarAlPortapapeles(datosPago?.transferencia?.cuenta)">
          <v-icon start>mdi-content-copy</v-icon>
          Copiar Cuenta
        </v-btn>
      </v-card-text>
    </v-card>

    <!-- Zelle / Binance si existen -->
    <v-card v-if="datosPago?.zelle" class="mb-4" elevation="2">
      <v-card-text class="pa-4">
        <div class="text-h6 mb-4 text-info">💵 Zelle</div>
        <div class="d-flex justify-space-between mb-2">
          <span class="text-medium-emphasis">Email:</span>
          <span class="font-weight-bold">{{ datosPago.zelle }}</span>
        </div>
        <v-btn block color="info" variant="outlined" rounded="pill" @click="copiarAlPortapapeles(datosPago.zelle)">
          <v-icon start>mdi-content-copy</v-icon>
          Copiar Email
        </v-btn>
      </v-card-text>
    </v-card>

    <v-card v-if="datosPago?.binance" class="mb-4" elevation="2">
      <v-card-text class="pa-4">
        <div class="text-h6 mb-4 text-warning">₿ Binance</div>
        <div class="d-flex justify-space-between mb-2">
          <span class="text-medium-emphasis">ID:</span>
          <span class="font-weight-bold">{{ datosPago.binance }}</span>
        </div>
        <v-btn block color="warning" variant="outlined" rounded="pill" @click="copiarAlPortapapeles(datosPago.binance)">
          <v-icon start>mdi-content-copy</v-icon>
          Copiar ID
        </v-btn>
      </v-card-text>
    </v-card>

    <!-- Historial de dólar -->
    <div class="text-subtitle-1 font-weight-medium mb-2">Historial del dólar</div>
    <v-card class="mb-4" elevation="1">
      <v-card-text class="pa-3">
        <div class="d-flex align-center mb-2">
          <div class="flex-grow-1">
            <div class="text-caption text-medium-emphasis">Tasa actual</div>
            <div class="text-h5 font-weight-medium">{{ formatearNumero(tasaActual) }} Bs/$</div>
          </div>
          <v-chip :color="variacionDolar >= 0 ? 'error' : 'success'" size="small" variant="tonal">
            <v-icon size="12" start>{{ variacionDolar >= 0 ? 'mdi-arrow-up' : 'mdi-arrow-down' }}</v-icon>
            {{ Math.abs(variacionDolar).toFixed(2) }}%
          </v-chip>
        </div>

        <!-- Mini gráfico de línea SVG -->
        <svg v-if="historialDolar.length > 1" viewBox="0 0 300 60" style="width: 100%; height: 60px;">
          <polyline
            :points="lineaHistorial"
            fill="none"
            stroke="rgb(var(--v-theme-primary))"
            stroke-width="2"
            stroke-linecap="round"
            stroke-linejoin="round"
          />
          <circle
            v-for="(punto, i) in puntosHistorial"
            :key="i"
            :cx="punto.x" :cy="punto.y" r="3"
            fill="rgb(var(--v-theme-primary))"
          />
        </svg>

        <div class="text-caption text-medium-emphasis mt-2">
          Tu deuda se mantiene en USD. Los montos en Bs se actualizan automáticamente.
        </div>
      </v-card-text>
    </v-card>

    <v-btn block color="error" variant="outlined" rounded="pill" @click="cerrarSesion">
      <v-icon start>mdi-logout</v-icon>
      Cerrar sesión
    </v-btn>
  </v-container>
</template>

<script setup>
import { computed } from 'vue'
import { useFinanCash } from '@/composables/useFinanCash'

const { 
  usuario, 
  nivelActual,
  tasaActual,
  historialDolar,
  datosPago,
  formatearNumero,
  colorNivel,
  iconoNivel,
  copiarAlPortapapeles,
  cerrarSesion
} = useFinanCash()

const descripcionNivel = (nivel) => {
  const desc = {
    nuevo: 'Primeros pasos',
    bronce: 'Cliente nuevo',
    plata: 'Cliente confiable',
    oro: 'Cliente preferencial',
    platino: 'Cliente elite'
  }
  return desc[nivel] || ''
}

const variacionDolar = computed(() => {
  if (historialDolar.value.length < 2) return 0
  const ultimo = historialDolar.value[0]
  const anterior = historialDolar.value[1]
  if (!ultimo?.tasa || !anterior?.tasa) return 0
  return ((ultimo.tasa - anterior.tasa) / anterior.tasa) * 100
})

const puntosHistorial = computed(() => {
  if (historialDolar.value.length < 2) return []
  const datos = historialDolar.value.slice(0, 20).reverse()
  const minTasa = Math.min(...datos.map(d => d.tasa))
  const maxTasa = Math.max(...datos.map(d => d.tasa))
  const rango = maxTasa - minTasa || 1

  return datos.map((d, i) => ({
    x: (i / (datos.length - 1)) * 280 + 10,
    y: 50 - ((d.tasa - minTasa) / rango) * 40
  }))
})

const lineaHistorial = computed(() => {
  return puntosHistorial.value.map(p => `${p.x},${p.y}`).join(' ')
})
</script>

<style scoped>
.datos-view { padding-bottom: 80px; }
.perfil-card { border-top: 4px solid v-bind('colorNivel(usuario.nivel)'); }
.gap-2 { gap: 8px; }
</style>