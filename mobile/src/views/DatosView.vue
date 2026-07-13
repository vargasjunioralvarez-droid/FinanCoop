<template>
  <div class="datos-wrapper">
    <div class="bg-gradient"></div>

    <div class="page-content">
      <!-- Header -->
      <div class="header-section">
        <h1 class="header-title">Mis Datos</h1>
      </div>

      <!-- Perfil -->
      <v-card class="profile-card glass-card" elevation="0">
        <v-card-text class="pa-4 text-center">
          <v-avatar size="72" :color="colorNivel(usuario.nivel)" class="mb-2">
            <v-icon size="36" color="white">{{ iconoNivel(usuario.nivel) }}</v-icon>
          </v-avatar>
          <div class="profile-name">{{ usuario.nombre }}</div>
          <div class="profile-sub">Nivel {{ usuario.nivel }} • {{ usuario.score }} puntos</div>
          <v-chip :color="colorNivel(usuario.nivel)" size="small" variant="tonal" class="mt-1">
            {{ descripcionNivel(usuario.nivel) }}
          </v-chip>
        </v-card-text>
      </v-card>

      <!-- Mi nivel -->
      <h3 class="section-title">Mi nivel</h3>
      <v-card class="nivel-card glass-card" elevation="0">
        <v-card-text class="pa-4">
          <div class="d-flex align-center mb-3">
            <v-icon :color="colorNivel(usuario.nivel)" size="32" class="mr-3">{{ iconoNivel(usuario.nivel) }}</v-icon>
            <div>
              <div class="nivel-name">{{ usuario.nivel }}</div>
              <div class="nivel-desc">{{ descripcionNivel(usuario.nivel) }}</div>
            </div>
          </div>
          <v-divider style="border-color: rgba(255,255,255,0.06);" />
          <div class="beneficios-container">
            <div class="beneficios-label">Beneficios actuales:</div>
            <div class="beneficios-grid">
              <v-chip size="small" variant="outlined" color="#4facfe">
                <v-icon size="12" start>mdi-percent</v-icon>
                {{ nivelActual.entrada_pct || 0 }}% entrada
              </v-chip>
              <v-chip size="small" variant="outlined" color="#4facfe">
                <v-icon size="12" start>mdi-calendar</v-icon>
                {{ nivelActual.cuotas_max || 0 }} cuotas máx
              </v-chip>
              <v-chip size="small" variant="outlined" color="#4facfe">
                <v-icon size="12" start>mdi-currency-usd</v-icon>
                ${{ nivelActual.monto_max_usd || 0 }} límite
              </v-chip>
              <v-chip size="small" variant="outlined" color="#4facfe">
                <v-icon size="12" start>mdi-alert</v-icon>
                {{ nivelActual.mora_diaria || 0 }}% mora/día
              </v-chip>
            </div>
          </div>
        </v-card-text>
      </v-card>

      <!-- Estadísticas -->
      <h3 class="section-title">Estadísticas</h3>
      <v-card class="stats-card glass-card" elevation="0">
        <v-card-text class="pa-4">
          <div class="stats-grid">
            <div class="stat-item">
              <div class="stat-number">{{ usuario.total_compras || 0 }}</div>
              <div class="stat-label">Compras</div>
            </div>
            <div class="stat-divider"></div>
            <div class="stat-item">
              <div class="stat-number success">{{ usuario.cuotas_pagadas_tiempo || 0 }}</div>
              <div class="stat-label">Puntuales</div>
            </div>
            <div class="stat-divider"></div>
            <div class="stat-item">
              <div class="stat-number warning">{{ usuario.cuotas_con_mora || 0 }}</div>
              <div class="stat-label">Con mora</div>
            </div>
          </div>
        </v-card-text>
      </v-card>

      <!-- Datos para pagar -->
      <h3 class="section-title">Datos para pagar</h3>

      <!-- Pago Móvil -->
      <v-card class="pago-card glass-card" elevation="0" color="#1a237e">
        <v-card-text class="pa-4">
          <div class="pago-header">
            <v-icon class="mr-2">mdi-cellphone</v-icon>
            <span>Pago Móvil</span>
          </div>
          <div class="pago-row">
            <span class="pago-label">Banco:</span>
            <span class="pago-value">{{ datosPago?.pago_movil?.banco || 'No disponible' }}</span>
          </div>
          <div class="pago-row">
            <span class="pago-label">Teléfono:</span>
            <span class="pago-value highlight">{{ datosPago?.pago_movil?.telefono || 'No disponible' }}</span>
          </div>
          <div class="pago-row">
            <span class="pago-label">Cédula:</span>
            <span class="pago-value">{{ datosPago?.pago_movil?.cedula || 'No disponible' }}</span>
          </div>
          <v-btn block color="white" variant="outlined" rounded="pill" class="copy-btn" @click="copiarAlPortapapeles(datosPago?.pago_movil?.telefono)">
            <v-icon start size="18">mdi-content-copy</v-icon>
            Copiar Teléfono
          </v-btn>
        </v-card-text>
      </v-card>

      <!-- Transferencia -->
      <v-card class="pago-card glass-card" elevation="0">
        <v-card-text class="pa-4">
          <div class="pago-header">
            <v-icon class="mr-2" color="#4facfe">mdi-bank-transfer</v-icon>
            <span>Transferencia</span>
          </div>
          <div class="pago-row">
            <span class="pago-label">Banco:</span>
            <span class="pago-value">{{ datosPago?.transferencia?.banco || 'No disponible' }}</span>
          </div>
          <div class="pago-row">
            <span class="pago-label">Cuenta:</span>
            <span class="pago-value highlight">{{ datosPago?.transferencia?.cuenta || 'No disponible' }}</span>
          </div>
          <v-btn block color="#4facfe" variant="outlined" rounded="pill" class="copy-btn" @click="copiarAlPortapapeles(datosPago?.transferencia?.cuenta)">
            <v-icon start size="18">mdi-content-copy</v-icon>
            Copiar Cuenta
          </v-btn>
        </v-card-text>
      </v-card>

      <!-- Zelle -->
      <v-card v-if="datosPago?.zelle" class="pago-card glass-card" elevation="0">
        <v-card-text class="pa-4">
          <div class="pago-header">
            <v-icon class="mr-2" color="#4fc3f7">mdi-currency-usd</v-icon>
            <span>Zelle</span>
          </div>
          <div class="pago-row">
            <span class="pago-label">Email:</span>
            <span class="pago-value highlight">{{ datosPago.zelle }}</span>
          </div>
          <v-btn block color="#4fc3f7" variant="outlined" rounded="pill" class="copy-btn" @click="copiarAlPortapapeles(datosPago.zelle)">
            <v-icon start size="18">mdi-content-copy</v-icon>
            Copiar Email
          </v-btn>
        </v-card-text>
      </v-card>

      <!-- Binance -->
      <v-card v-if="datosPago?.binance" class="pago-card glass-card" elevation="0">
        <v-card-text class="pa-4">
          <div class="pago-header">
            <v-icon class="mr-2" color="#ffd54f">mdi-bitcoin</v-icon>
            <span>Binance</span>
          </div>
          <div class="pago-row">
            <span class="pago-label">ID:</span>
            <span class="pago-value highlight">{{ datosPago.binance }}</span>
          </div>
          <v-btn block color="#ffd54f" variant="outlined" rounded="pill" class="copy-btn" @click="copiarAlPortapapeles(datosPago.binance)">
            <v-icon start size="18">mdi-content-copy</v-icon>
            Copiar ID
          </v-btn>
        </v-card-text>
      </v-card>

      <!-- Historial del dólar -->
      <h3 class="section-title">Historial del dólar</h3>
      <v-card class="dolar-historial glass-card" elevation="0">
        <v-card-text class="pa-4">
          <div class="d-flex align-center mb-3">
            <div class="flex-grow-1">
              <div class="dolar-label">Tasa actual</div>
              <div class="dolar-value">{{ formatearNumero(tasaActual) }} Bs/$</div>
            </div>
            <v-chip :color="variacionDolar >= 0 ? 'error' : 'success'" size="small" variant="tonal">
              <v-icon size="12" start>{{ variacionDolar >= 0 ? 'mdi-arrow-up' : 'mdi-arrow-down' }}</v-icon>
              {{ Math.abs(variacionDolar).toFixed(2) }}%
            </v-chip>
          </div>

          <svg v-if="historialDolar.length > 1" viewBox="0 0 300 60" style="width: 100%; height: 60px;">
            <polyline
              :points="lineaHistorial"
              fill="none"
              stroke="#4facfe"
              stroke-width="2"
              stroke-linecap="round"
              stroke-linejoin="round"
            />
            <circle
              v-for="(punto, i) in puntosHistorial"
              :key="i"
              :cx="punto.x" :cy="punto.y" r="3"
              fill="#4facfe"
            />
          </svg>

          <div class="dolar-info">
            Tu deuda se mantiene en USD. Los montos en Bs se actualizan automáticamente.
          </div>
        </v-card-text>
      </v-card>

      <!-- Cerrar sesión -->
      <v-btn block color="error" variant="tonal" rounded="pill" size="large" class="logout-btn" @click="cerrarSesion">
        <v-icon start>mdi-logout</v-icon>
        Cerrar sesión
      </v-btn>
    </div>
  </div>
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
.datos-wrapper {
  min-height: 100vh;
  background: #0a0e1a;
  position: relative;
}

.bg-gradient {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: radial-gradient(ellipse at 20% 50%, rgba(79, 172, 254, 0.08), transparent 70%),
              radial-gradient(ellipse at 80% 50%, rgba(99, 102, 241, 0.08), transparent 70%);
  z-index: 0;
}

.page-content {
  position: relative;
  z-index: 1;
  padding: 16px 16px 80px;
}

.header-title {
  font-size: 24px;
  font-weight: 700;
  color: #ffffff;
  margin-bottom: 16px;
}

.section-title {
  font-size: 14px;
  font-weight: 600;
  color: #ffffff;
  margin: 16px 0 10px;
}

.glass-card {
  background: rgba(255,255,255,0.04) !important;
  backdrop-filter: blur(12px) !important;
  -webkit-backdrop-filter: blur(12px) !important;
  border: 1px solid rgba(255,255,255,0.06);
  border-radius: 16px !important;
}

.profile-card {
  margin-bottom: 8px;
  padding: 8px 0;
}

.profile-name {
  font-size: 18px;
  font-weight: 700;
  color: #ffffff;
}

.profile-sub {
  font-size: 13px;
  color: rgba(255,255,255,0.4);
}

.nivel-card {
  margin-bottom: 8px;
}

.nivel-name {
  font-size: 16px;
  font-weight: 600;
  color: #ffffff;
  text-transform: capitalize;
}

.nivel-desc {
  font-size: 12px;
  color: rgba(255,255,255,0.4);
}

.beneficios-container {
  margin-top: 12px;
}

.beneficios-label {
  font-size: 12px;
  color: rgba(255,255,255,0.4);
  margin-bottom: 8px;
}

.beneficios-grid {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.beneficios-grid :deep(.v-chip) {
  background: rgba(79, 172, 254, 0.06) !important;
  border-color: rgba(79, 172, 254, 0.15) !important;
  color: #4facfe !important;
}

.stats-card {
  margin-bottom: 8px;
}

.stats-grid {
  display: flex;
  justify-content: space-around;
  align-items: center;
}

.stat-item {
  text-align: center;
  flex: 1;
}

.stat-number {
  font-size: 24px;
  font-weight: 700;
  color: #ffffff;
}

.stat-number.success {
  color: #4caf50;
}

.stat-number.warning {
  color: #ffd54f;
}

.stat-label {
  font-size: 11px;
  color: rgba(255,255,255,0.3);
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.stat-divider {
  width: 1px;
  height: 40px;
  background: rgba(255,255,255,0.06);
}

.pago-card {
  margin-bottom: 10px;
  transition: all 0.3s ease;
}

.pago-card:hover {
  background: rgba(255,255,255,0.06) !important;
}

.pago-header {
  font-size: 16px;
  font-weight: 600;
  color: #ffffff;
  display: flex;
  align-items: center;
  margin-bottom: 12px;
}

.pago-row {
  display: flex;
  justify-content: space-between;
  padding: 6px 0;
  border-bottom: 1px solid rgba(255,255,255,0.04);
}

.pago-row:last-of-type {
  border-bottom: none;
  margin-bottom: 12px;
}

.pago-label {
  font-size: 12px;
  color: rgba(255,255,255,0.3);
}

.pago-value {
  font-size: 14px;
  font-weight: 500;
  color: #ffffff;
}

.pago-value.highlight {
  font-weight: 700;
  color: #4facfe;
}

.copy-btn {
  border-color: rgba(255,255,255,0.15) !important;
  color: #ffffff !important;
}

.copy-btn:hover {
  background: rgba(255,255,255,0.05) !important;
}

.dolar-historial {
  margin-bottom: 16px;
}

.dolar-label {
  font-size: 11px;
  color: rgba(255,255,255,0.3);
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.dolar-value {
  font-size: 20px;
  font-weight: 700;
  color: #ffffff;
}

.dolar-info {
  font-size: 11px;
  color: rgba(255,255,255,0.2);
  margin-top: 8px;
  text-align: center;
}

.logout-btn {
  background: rgba(239, 68, 68, 0.1) !important;
  color: #f87171 !important;
  border: 1px solid rgba(239, 68, 68, 0.15);
  margin-top: 4px;
}

.logout-btn:hover {
  background: rgba(239, 68, 68, 0.15) !important;
}
</style>