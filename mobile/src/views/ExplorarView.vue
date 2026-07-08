<template>
  <v-container class="pa-4 explorar-view">
    <!-- Banner principal -->
    <v-card class="banner-card mb-4" elevation="4">
      <v-img
        src="/icons/icon-512x512.png"
        height="120"
        contain
        class="bg-primary"
      >
        <template v-slot:default>
          <div class="d-flex flex-column align-center justify-center fill-height text-white pa-4">
            <h2 class="text-h5 font-weight-bold">FinanCoop</h2>
            <p class="text-body-2 text-center text-white text-opacity-80">
              Tu aliado financiero de Cecosesola
            </p>
          </div>
        </template>
      </v-img>
    </v-card>

    <!-- Cómo funciona -->
    <div class="text-h6 font-weight-bold mb-3">¿Cómo funciona?</div>
    
    <v-timeline density="compact" align="start" class="mb-4">
      <v-timeline-item
        v-for="(paso, i) in pasos"
        :key="i"
        :dot-color="paso.color"
        size="small"
      >
        <div class="text-body-2 font-weight-medium">{{ paso.titulo }}</div>
        <div class="text-caption text-medium-emphasis">{{ paso.descripcion }}</div>
      </v-timeline-item>
    </v-timeline>

    <!-- Beneficios por nivel -->
    <div class="text-h6 font-weight-bold mb-3">Beneficios por nivel</div>
    
    <v-expansion-panels variant="accordion" class="mb-4">
      <v-expansion-panel
        v-for="(config, nivel) in nivelesConfig"
        :key="nivel"
      >
        <v-expansion-panel-title>
          <div class="d-flex align-center">
            <v-icon :color="colorNivel(nivel)" class="mr-2">{{ iconoNivel(nivel) }}</v-icon>
            <span class="text-capitalize font-weight-medium">{{ nivel }}</span>
            <v-chip size="x-small" :color="colorNivel(nivel)" variant="tonal" class="ml-2">
              ${{ config.monto_max_usd }}
            </v-chip>
          </div>
        </v-expansion-panel-title>
        <v-expansion-panel-text>
          <v-list density="compact">
            <v-list-item>
              <template v-slot:prepend>
                <v-icon size="16" color="primary">mdi-percent</v-icon>
              </template>
              <v-list-item-title class="text-body-2">
                {{ config.entrada_pct }}% de entrada inicial
              </v-list-item-title>
            </v-list-item>
            <v-list-item>
              <template v-slot:prepend>
                <v-icon size="16" color="primary">mdi-calendar</v-icon>
              </template>
              <v-list-item-title class="text-body-2">
                Hasta {{ config.cuotas_max }} cuotas quincenales
              </v-list-item-title>
            </v-list-item>
            <v-list-item>
              <template v-slot:prepend>
                <v-icon size="16" color="primary">mdi-currency-usd</v-icon>
              </template>
              <v-list-item-title class="text-body-2">
                Límite de ${{ config.monto_max_usd }} por compra
              </v-list-item-title>
            </v-list-item>
            <v-list-item>
              <template v-slot:prepend>
                <v-icon size="16" :color="config.mora_diaria <= 1 ? 'success' : 'warning'">mdi-alert</v-icon>
              </template>
              <v-list-item-title class="text-body-2">
                Mora diaria: {{ config.mora_diaria }}%
              </v-list-item-title>
            </v-list-item>
          </v-list>
        </v-expansion-panel-text>
      </v-expansion-panel>
    </v-expansion-panels>

    <!-- Preguntas frecuentes -->
    <div class="text-h6 font-weight-bold mb-3">Preguntas frecuentes</div>
    
    <v-expansion-panels variant="accordion" class="mb-4">
      <v-expansion-panel
        v-for="(faq, i) in faqs"
        :key="i"
      >
        <v-expansion-panel-title class="text-body-2 font-weight-medium">
          {{ faq.pregunta }}
        </v-expansion-panel-title>
        <v-expansion-panel-text class="text-body-2 text-medium-emphasis">
          {{ faq.respuesta }}
        </v-expansion-panel-text>
      </v-expansion-panel>
    </v-expansion-panels>

    <!-- Contacto -->
    <v-card class="contacto-card mb-4" elevation="2" color="primary" dark>
      <v-card-text class="pa-4 text-center">
        <v-icon size="32" class="mb-2">mdi-store</v-icon>
        <div class="text-h6 font-weight-bold mb-1">¿Necesitas ayuda?</div>
        <div class="text-body-2 text-white text-opacity-80 mb-3">
          Visita tu tienda Cecosesola afiliada
        </div>
        <v-btn variant="outlined" color="white" rounded="pill">
          <v-icon start>mdi-map-marker</v-icon>
          Ver tiendas
        </v-btn>
      </v-card-text>
    </v-card>
  </v-container>
</template>

<script setup>
import { useFinanCash } from '@/composables/useFinanCash'

const { nivelesConfig, colorNivel, iconoNivel } = useFinanCash()

const pasos = [
  {
    titulo: 'Compra en tu tienda',
    descripcion: 'Elige tus productos y solicita financiamiento en caja',
    color: 'primary'
  },
  {
    titulo: 'Paga la entrada',
    descripcion: 'Según tu nivel, pagas del 20% al 60% de entrada',
    color: 'success'
  },
  {
    titulo: 'Recibe tu PIN',
    descripcion: 'Te damos acceso a la app para ver tus cuotas',
    color: 'info'
  },
  {
    titulo: 'Paga quincenalmente',
    descripcion: 'Reporta tus pagos por Pago Móvil, Transferencia, Zelle o Binance',
    color: 'warning'
  },
  {
    titulo: 'Sube de nivel',
    descripcion: 'Cada compra completada mejora tus condiciones',
    color: 'amber'
  }
]

const faqs = [
  {
    pregunta: '¿En qué moneda está mi deuda?',
    respuesta: 'Tu deuda se mantiene en dólares (USD), pero pagas en bolívares (Bs) al tipo de cambio del día. Esto protege tu compra de la inflación.'
  },
  {
    pregunta: '¿Qué pasa si me atrazo?',
    respuesta: 'Tienes 3 días de gracia. Después se aplica mora diaria según tu nivel (0.5% a 2%). Si acumulas cuotas vencidas, quedas bloqueado para nuevas compras.'
  },
  {
    pregunta: '¿Puedo pagar antes?',
    respuesta: 'Sí, puedes pagar cuotas anticipadas sin penalización. Solo reporta el pago como una cuota normal.'
  },
  {
    pregunta: '¿Cómo subo de nivel?',
    respuesta: 'Completando financiamientos sin mora. Cada compra pagada completa suma 1 punto a tu score.'
  },
  {
    pregunta: '¿Puedo usar la app sin internet?',
    respuesta: 'La app funciona parcialmente offline. Puedes ver tus datos guardados, pero necesitas conexión para reportar pagos.'
  }
]
</script>

<style scoped>
.explorar-view {
  padding-bottom: 80px;
}

.banner-card {
  border-radius: 20px;
  overflow: hidden;
}

.contacto-card {
  border-radius: 16px;
}
</style>