<template>
  <div class="explorar-wrapper">
    <div class="bg-gradient"></div>

    <div class="page-content">
      <!-- Banner -->
      <v-card class="banner-card glass-card" elevation="0">
        <v-card-text class="pa-4 text-center">
          <v-img src="/icons/icon-512x512.png" width="64" class="mx-auto mb-2" contain />
          <h2 class="banner-title">FinanCoop</h2>
          <p class="banner-sub">Tu aliado financiero de Cecosesola</p>
        </v-card-text>
      </v-card>

      <!-- Cómo funciona -->
      <h3 class="section-title">¿Cómo funciona?</h3>
      <v-timeline density="compact" align="start" class="timeline">
        <v-timeline-item v-for="paso in pasos" :key="paso.titulo" :dot-color="paso.color" size="small">
          <div class="timeline-title">{{ paso.titulo }}</div>
          <div class="timeline-desc">{{ paso.descripcion }}</div>
        </v-timeline-item>
      </v-timeline>

      <!-- Beneficios -->
      <h3 class="section-title">Beneficios por nivel</h3>
      <v-expansion-panels variant="accordion" class="expansion">
        <v-expansion-panel v-for="(config, nivel) in nivelesConfig" :key="nivel">
          <v-expansion-panel-title>
            <div class="d-flex align-center">
              <v-icon :color="colorNivel(nivel)" class="mr-2">{{ iconoNivel(nivel) }}</v-icon>
              <span class="text-capitalize">{{ nivel }}</span>
              <v-chip size="x-small" :color="colorNivel(nivel)" variant="tonal" class="ml-2">${{ config.monto_max_usd }}</v-chip>
            </div>
          </v-expansion-panel-title>
          <v-expansion-panel-text>
            <v-list density="compact" class="bg-transparent">
              <v-list-item><v-list-item-title>{{ config.entrada_pct }}% de entrada inicial</v-list-item-title></v-list-item>
              <v-list-item><v-list-item-title>Hasta {{ config.cuotas_max }} cuotas quincenales</v-list-item-title></v-list-item>
              <v-list-item><v-list-item-title>Límite de ${{ config.monto_max_usd }} por compra</v-list-item-title></v-list-item>
              <v-list-item><v-list-item-title>Mora diaria: {{ config.mora_diaria }}%</v-list-item-title></v-list-item>
            </v-list>
          </v-expansion-panel-text>
        </v-expansion-panel>
      </v-expansion-panels>

      <!-- FAQs -->
      <h3 class="section-title">Preguntas frecuentes</h3>
      <v-expansion-panels variant="accordion" class="expansion">
        <v-expansion-panel v-for="faq in faqs" :key="faq.pregunta">
          <v-expansion-panel-title class="faq-question">{{ faq.pregunta }}</v-expansion-panel-title>
          <v-expansion-panel-text class="faq-answer">{{ faq.respuesta }}</v-expansion-panel-text>
        </v-expansion-panel>
      </v-expansion-panels>

      <!-- Contacto -->
      <v-card class="contacto-card glass-card" elevation="0">
        <v-card-text class="pa-4 text-center">
          <v-icon size="32" class="mb-2" color="#4facfe">mdi-store</v-icon>
          <div class="contacto-title">¿Necesitas ayuda?</div>
          <div class="contacto-sub">Visita tu tienda Cecosesola afiliada</div>
          <v-btn color="#4facfe" rounded="pill" variant="outlined" class="mt-2">
            <v-icon start>mdi-map-marker</v-icon>Ver tiendas
          </v-btn>
        </v-card-text>
      </v-card>
    </div>
  </div>
</template>

<script setup>
import { useFinanCash } from '@/composables/useFinanCash'

const { nivelesConfig, colorNivel, iconoNivel } = useFinanCash()

const pasos = [
  { titulo: 'Compra en tu tienda', descripcion: 'Elige tus productos y solicita financiamiento en caja', color: '#4facfe' },
  { titulo: 'Paga la entrada', descripcion: 'Según tu nivel, pagas del 20% al 60% de entrada', color: '#4caf50' },
  { titulo: 'Recibe tu PIN', descripcion: 'Te damos acceso a la app para ver tus cuotas', color: '#4facfe' },
  { titulo: 'Paga quincenalmente', descripcion: 'Reporta tus pagos por Pago Móvil, Transferencia, Zelle o Binance', color: '#ffd54f' },
  { titulo: 'Sube de nivel', descripcion: 'Cada compra completada mejora tus condiciones', color: '#f472b6' }
]

const faqs = [
  { pregunta: '¿En qué moneda está mi deuda?', respuesta: 'Tu deuda se mantiene en dólares (USD), pero pagas en bolívares (Bs) al tipo de cambio del día.' },
  { pregunta: '¿Qué pasa si me atrazo?', respuesta: 'Tienes 3 días de gracia. Después se aplica mora diaria según tu nivel.' },
  { pregunta: '¿Puedo pagar antes?', respuesta: 'Sí, puedes pagar cuotas anticipadas sin penalización.' },
  { pregunta: '¿Cómo subo de nivel?', respuesta: 'Completando financiamientos sin mora. Cada compra pagada completa suma 1 punto.' },
  { pregunta: '¿Puedo usar la app sin internet?', respuesta: 'La app funciona parcialmente offline. Puedes ver tus datos guardados.' }
]
</script>

<style scoped>
.explorar-wrapper {
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

.glass-card {
  background: rgba(255,255,255,0.04) !important;
  backdrop-filter: blur(12px) !important;
  -webkit-backdrop-filter: blur(12px) !important;
  border: 1px solid rgba(255,255,255,0.06);
  border-radius: 16px !important;
}

.banner-card {
  margin-bottom: 16px;
}

.banner-title {
  font-size: 22px;
  font-weight: 700;
  color: #ffffff;
}

.banner-sub {
  font-size: 13px;
  color: rgba(255,255,255,0.4);
}

.section-title {
  font-size: 16px;
  font-weight: 700;
  color: #ffffff;
  margin: 16px 0 12px;
}

.timeline {
  margin-bottom: 8px;
}

.timeline-title {
  font-size: 13px;
  font-weight: 600;
  color: #ffffff;
}

.timeline-desc {
  font-size: 12px;
  color: rgba(255,255,255,0.4);
}

.expansion {
  background: transparent !important;
  margin-bottom: 8px;
}

.expansion :deep(.v-expansion-panel) {
  background: rgba(255,255,255,0.04) !important;
  border: 1px solid rgba(255,255,255,0.06);
  border-radius: 12px !important;
  margin-bottom: 6px;
}

.expansion :deep(.v-expansion-panel-title) {
  color: #ffffff !important;
}

.expansion :deep(.v-expansion-panel-text) {
  color: rgba(255,255,255,0.6) !important;
}

.faq-question {
  font-size: 13px !important;
  font-weight: 500 !important;
}

.faq-answer {
  font-size: 13px !important;
  line-height: 1.6;
}

.contacto-card {
  margin-top: 8px;
}

.contacto-title {
  font-size: 16px;
  font-weight: 600;
  color: #ffffff;
}

.contacto-sub {
  font-size: 13px;
  color: rgba(255,255,255,0.4);
}
</style>