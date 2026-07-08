<template>
  <v-dialog v-model="mostrar" max-width="450" scrollable>
    <template v-slot:activator="{ props }">
      <v-btn
        v-bind="props"
        icon="mdi-help-circle"
        color="info"
        variant="tonal"
        size="small"
        class="ml-2"
      ></v-btn>
    </template>
    
    <v-card>
      <v-card-title class="bg-primary text-white py-4">
        <v-icon start class="mr-2">mdi-information</v-icon>
        ¿Qué es FinanCash?
      </v-card-title>
      
      <v-card-text class="pa-4">
        <div class="seccion mb-4">
          <h3 class="text-subtitle-1 font-weight-bold mb-2 text-primary">
            <v-icon start color="primary">mdi-wallet</v-icon>
            ¿Qué es?
          </h3>
          <p class="text-body-2 text-grey">
            FinanCash es un sistema de financiamiento para compras. 
            Compra hoy, paga en cuotas quincenales.
          </p>
        </div>
        
        <v-divider class="my-3"></v-divider>
        
        <div class="seccion mb-4">
          <h3 class="text-subtitle-1 font-weight-bold mb-2 text-amber">
            <v-icon start color="amber">mdi-trophy</v-icon>
            Tu Nivel de Confianza
          </h3>
          <p class="text-caption text-grey mb-2">
            Cada compra que completas aumenta tu score y sube de nivel:
          </p>
          
          <v-list density="compact" class="pa-0">
            <v-list-item v-for="nivel in nivelesInfo" :key="nivel.nombre" class="px-0">
              <template v-slot:prepend>
                <v-icon :color="nivel.color" size="20">{{ nivel.icono }}</v-icon>
              </template>
              <v-list-item-title class="text-body-2">
                <strong>{{ nivel.nombre }}</strong> - Hasta ${{ nivel.monto }} USD
              </v-list-item-title>
              <v-list-item-subtitle class="text-caption">
                {{ nivel.entrada }}% entrada, {{ nivel.cuotas }} cuotas
              </v-list-item-subtitle>
            </v-list-item>
          </v-list>
        </div>
        
        <v-divider class="my-3"></v-divider>
        
        <div class="seccion mb-4">
          <h3 class="text-subtitle-1 font-weight-bold mb-2 text-error">
            <v-icon start color="error">mdi-alert-circle</v-icon>
            Importante
          </h3>
          <ul class="text-body-2 text-grey lista">
            <li>3 días de gracia por cuota</li>
            <li>Después se aplica mora diaria según tu nivel</li>
            <li>Si tienes cuotas vencidas, no puedes comprar más</li>
          </ul>
        </div>
        
        <v-divider class="my-3"></v-divider>
        
        <div class="seccion">
          <h3 class="text-subtitle-1 font-weight-bold mb-2 text-success">
            <v-icon start color="success">mdi-cash-check</v-icon>
            Paga fácil
          </h3>
          <p class="text-body-2 text-grey">
            Reporta tu pago por Pago Móvil, Transferencia, Zelle o Binance. 
            El establecimiento lo confirma y listo.
          </p>
        </div>
      </v-card-text>
      
      <v-card-actions class="pa-4">
        <v-btn color="primary" block @click="mostrar = false">
          <v-icon start>mdi-check</v-icon>
          Entendido
        </v-btn>
      </v-card-actions>
    </v-card>
  </v-dialog>
</template>

<script setup>
import { ref } from 'vue'
import { useFinanCash } from '@/composables/useFinanCash'

const { nivelesInfo } = useFinanCash()
const mostrar = ref(false)
</script>

<style scoped>
.seccion {
  padding: 0 4px;
}

.lista {
  padding-left: 16px;
  margin: 0;
}

.lista li {
  margin-bottom: 4px;
}
</style>