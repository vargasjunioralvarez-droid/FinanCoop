<template>
  <v-container fluid class="pa-0">
    <div class="background-gradient"></div>
    
    <v-row class="ma-0">
      <v-col cols="12" class="pa-4">
        <!-- HEADER PREMIUM -->
        <div class="header-premium d-flex align-center justify-space-between flex-wrap">
          <div class="d-flex align-center">
            <div class="icon-wrapper pulse-animation">
              <v-icon size="32" color="white">mdi-cart-plus</v-icon>
            </div>
            <div class="ml-3">
              <h1 class="text-h4 font-weight-bold text-white">Nueva Venta</h1>
              <p class="text-subtitle-2 text-white" style="opacity: 0.7;">Sistema de financiamiento inteligente</p>
            </div>
          </div>
          <div class="d-flex align-center" style="gap: 12px;">
            <div class="tasa-card glass-effect">
              <v-icon size="20" color="#FFD700">mdi-currency-usd</v-icon>
              <span class="font-weight-bold text-white ml-1">{{ tasaDolar }}</span>
              <span class="text-white" style="opacity: 0.6; font-size: 0.75rem;">BS/$</span>
            </div>
            <v-chip class="step-chip" color="transparent" size="large">
              <span class="text-white font-weight-bold">Paso {{ paso }}/4</span>
            </v-chip>
          </div>
        </div>

        <!-- PASO 1: IDENTIFICAR CLIENTE -->
        <div v-if="paso === 1" class="step-container fade-in">
          <v-card class="glass-card rounded-xl" elevation="0">
            <v-card-text class="pa-4">
              <div class="search-wrapper">
                <v-text-field v-model="busquedaCedula" label="Ingresa la cédula del cliente" @keyup.enter="buscarCliente" append-inner-icon="mdi-magnify" @click:append-inner="buscarCliente" variant="solo" density="comfortable" placeholder="Ej: V-12345678" :loading="cargando" clearable class="search-field" height="56">
                  <template v-slot:prepend-inner><v-icon color="#4facfe">mdi-card-account-details</v-icon></template>
                </v-text-field>
              </div>

              <!-- CLIENTE ENCONTRADO -->
              <div v-if="clienteEncontrado" class="mt-4 cliente-card-wrapper slide-up">
                <div class="cliente-premium-card" :class="`nivel-${clienteEncontrado.nivel}`">
                  <div class="card-glow"></div>
                  <v-row class="ma-0">
                    <v-col cols="12" md="8" class="pa-3">
                      <div class="d-flex align-center">
                        <div class="avatar-wrapper">
                          <v-avatar size="64" class="avatar-premium" :style="`background: ${nivelGradiente(clienteEncontrado.nivel)}`"><v-icon size="32" color="white">{{ nivelIcono(clienteEncontrado.nivel) }}</v-icon></v-avatar>
                          <div class="level-badge" :class="`level-${clienteEncontrado.nivel}`">{{ clienteEncontrado.nivel.toUpperCase() }}</div>
                        </div>
                        <div class="ml-3">
                          <h2 class="text-h5 font-weight-bold text-white">{{ clienteEncontrado.nombre }}</h2>
                          
                          <!-- ✅ TIENDA -->
                          <p class="text-caption text-white mt-1" style="opacity: 0.6;" v-if="clienteEncontrado.tienda_nombre">
                            <v-icon size="14" color="rgba(255,255,255,0.5)">mdi-store</v-icon>
                            Tienda: {{ clienteEncontrado.tienda_nombre }}
                          </p>
                          
                          <div class="d-flex align-center flex-wrap mt-1" style="gap: 8px;">
                            <div class="info-pill"><v-icon size="14" color="rgba(255,255,255,0.7)">mdi-star</v-icon><span class="text-white" style="opacity: 0.9; font-size: 0.8rem;">Score: {{ clienteEncontrado.score }}</span></div>
                            <div class="info-pill"><v-icon size="14" color="rgba(255,255,255,0.7)">mdi-phone</v-icon><span class="text-white" style="opacity: 0.9; font-size: 0.8rem;">{{ clienteEncontrado.telefono }}</span></div>
                            <v-chip v-if="clienteEncontrado.estado === 'aprobado'" color="success" size="x-small" class="status-chip"><v-icon start size="12">mdi-check-circle</v-icon>Aprobado</v-chip>
                            <v-chip v-else color="warning" size="x-small" class="status-chip"><v-icon start size="12">mdi-clock</v-icon>Pendiente</v-chip>
                          </div>
                        </div>
                      </div>
                    </v-col>
                    <v-col cols="12" md="4" class="pa-3 d-flex align-center justify-md-end">
                      <div class="disponible-wrapper text-center"><div class="disponible-number">${{ formatearNumero(clienteEncontrado.limite_disponible?.disponible_usd || 0) }}</div><div class="disponible-label">Disponible</div></div>
                    </v-col>
                  </v-row>
                </div>

                <!-- BARRAS DE PROGRESO -->
                <div class="limite-card glass-effect mt-3">
                  <div class="d-flex justify-space-between align-center flex-wrap" style="gap: 8px;">
                    <div class="d-flex align-center" style="gap: 16px; flex-wrap: wrap;">
                      <div class="metric-item"><span class="metric-label">Límite</span><span class="metric-value">${{ clienteEncontrado.limite_disponible?.limite_usd || 0 }}</span></div>
                      <div class="metric-divider"></div>
                      <div class="metric-item"><span class="metric-label">Usado</span><span class="metric-value text-error">${{ clienteEncontrado.limite_disponible?.usado_usd || 0 }}</span></div>
                      <div class="metric-divider"></div>
                      <div class="metric-item"><span class="metric-label">Disponible</span><span class="metric-value text-success">${{ clienteEncontrado.limite_disponible?.disponible_usd || 0 }}</span></div>
                    </div>
                    <v-chip :color="clienteEncontrado.limite_disponible?.disponible_usd > 0 ? 'success' : 'error'" size="small" class="status-chip">
                      {{ clienteEncontrado.limite_disponible?.disponible_usd > 0 ? '✅ Puede comprar' : '❌ Sin saldo' }}
                    </v-chip>
                  </div>
                  <div class="progress-wrapper mt-2">
                    <v-progress-linear :model-value="porcentajeUsado" :color="porcentajeUsado > 80 ? 'error' : porcentajeUsado > 50 ? 'warning' : 'success'" height="8" rounded class="progress-bar-custom" />
                  </div>
                </div>

                <!-- COMPRAS ACTIVAS -->
                <div v-if="clienteEncontrado.financiamientos_activos?.length" class="mt-3">
                  <div class="financiamientos-header d-flex align-center">
                    <v-icon color="#FFD700" class="mr-2">mdi-clock-outline</v-icon>
                    <h4 class="text-subtitle-1 font-weight-bold text-white">Compras Activas</h4>
                    <v-chip size="small" color="#FFD700" class="ml-2">{{ clienteEncontrado.financiamientos_activos.length }}</v-chip>
                  </div>
                  <div class="financiamientos-grid mt-2">
                    <div v-for="fin in clienteEncontrado.financiamientos_activos" :key="fin.id" class="financiamiento-item glass-effect">
                      <div class="d-flex flex-column" style="gap: 4px;">
                        <!-- FILA 1: Tienda + Categoría + Código -->
                        <div class="d-flex align-center flex-wrap" style="gap: 6px;">
                          <v-chip v-if="fin.tienda_nombre" size="x-small" color="info" variant="flat">
                            <v-icon start size="12">mdi-store</v-icon>{{ fin.tienda_nombre }}
                          </v-chip>
                          <v-chip v-if="fin.descripcion" size="x-small" :color="colorCategoria(fin.descripcion)" variant="tonal">
                            {{ fin.descripcion }}
                          </v-chip>
                          <v-chip size="x-small" variant="outlined" class="text-white">{{ fin.codigo }}</v-chip>
                        </div>
                        <!-- FILA 2: Factura + Cuotas + Estado -->
                        <div class="d-flex justify-space-between align-center flex-wrap" style="gap: 8px;">
                          <span v-if="fin.numero_factura" class="text-caption font-mono" style="color: rgba(255,255,255,0.5);">
                            🧾 {{ fin.numero_factura }}
                          </span>
                          <span v-else></span>
                          <div class="d-flex align-center" style="gap: 8px;">
                            <v-chip size="x-small" :color="fin.cuotas_pagadas === fin.cuotas_aprobadas ? 'success' : 'primary'" variant="tonal">
                              {{ fin.cuotas_pagadas || 0 }}/{{ fin.cuotas_aprobadas }} cuotas
                            </v-chip>
                            <v-chip size="x-small" :color="fin.estado === 'activo' ? 'success' : 'warning'" variant="flat">{{ fin.estado }}</v-chip>
                          </div>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
                <div v-else class="mt-3">
                  <div class="empty-state glass-effect">
                    <v-icon color="rgba(255,255,255,0.3)" size="32">mdi-check-circle</v-icon>
                    <div class="text-caption" style="color: rgba(255,255,255,0.4);">No tiene compras activas</div>
                  </div>
                </div>

                <!-- BOTÓN CONTINUAR O ALERTA -->
                <div class="mt-4">
                  <v-btn v-if="clienteEncontrado.limite_disponible?.disponible_usd > 0 && (clienteEncontrado?.cuotas_vencidas || 0) === 0" 
                    color="#4facfe" @click="paso = 2" size="x-large" block elevation="0" class="btn-continuar rounded-xl">
                    <span class="font-weight-bold">Continuar con la venta</span>
                    <v-icon end>mdi-arrow-right</v-icon>
                  </v-btn>
                  
                  <v-alert v-else type="error" variant="tonal" class="rounded-xl" border="start">
                    <div class="d-flex align-center">
                      <v-icon color="error" size="28" class="mr-2">mdi-alert-circle</v-icon>
                      <div>
                        <strong class="text-white" v-if="(clienteEncontrado?.cuotas_vencidas || 0) > 0">
                          ⚠️ Cliente moroso - {{ clienteEncontrado.cuotas_vencidas }} cuota(s) vencida(s)
                        </strong>
                        <strong class="text-white" v-else>Cliente sin saldo disponible</strong>
                        <div class="text-caption" style="color: rgba(255,255,255,0.6);">
                          <span v-if="(clienteEncontrado?.cuotas_vencidas || 0) > 0">Debe ponerse al día antes de comprar</span>
                          <span v-else>Ha alcanzado el límite máximo de crédito</span>
                        </div>
                      </div>
                    </div>
                  </v-alert>
                </div>
              </div>

              <!-- REGISTRO NUEVO CLIENTE -->
              <div v-if="clienteNoEncontrado" class="mt-4 slide-up">
                <div class="register-card glass-effect">
                  <div class="d-flex align-center mb-3"><div class="register-icon-wrapper"><v-icon size="28" color="#FFD700">mdi-account-plus</v-icon></div><h3 class="text-h6 font-weight-bold text-white ml-2">Registrar Nuevo Cliente</h3></div>
                  <v-row>
                    <v-col cols="12" md="6"><v-text-field v-model="nuevoCliente.nombre" label="Nombre completo *" variant="outlined" density="comfortable" required prepend-inner-icon="mdi-account" dark class="custom-input" placeholder="Ej: Juan Pérez" /></v-col>
                    <v-col cols="12" md="6"><v-text-field v-model="nuevoCliente.telefono" label="Teléfono *" variant="outlined" density="comfortable" required prepend-inner-icon="mdi-phone" dark class="custom-input" placeholder="Ej: 04121234567" /></v-col>
                    <v-col cols="12" md="6"><v-text-field v-model="nuevoCliente.email" label="Email *" variant="outlined" density="comfortable" required prepend-inner-icon="mdi-email" dark class="custom-input" placeholder="Ej: correo@ejemplo.com" /></v-col>
                    <v-col cols="12" md="6"><v-textarea v-model="nuevoCliente.direccion" label="Dirección completa *" rows="1" variant="outlined" density="comfortable" required prepend-inner-icon="mdi-map-marker" dark class="custom-input" placeholder="Ej: Calle, urbanización, ciudad" /></v-col>
                  </v-row>
                  <v-divider class="my-3" style="border-color: rgba(255,255,255,0.1);"></v-divider>
                  <h4 class="text-subtitle-2 font-weight-bold text-white mb-2"><v-icon size="18" class="mr-1" color="rgba(255,255,255,0.6)">mdi-account-group</v-icon>Referencia personal</h4>
                  <v-row>
                    <v-col cols="12" md="4"><v-text-field v-model="nuevoCliente.referencia_nombre" label="Nombre de referencia *" variant="outlined" density="comfortable" required prepend-inner-icon="mdi-account" dark class="custom-input" placeholder="Ej: María García" /></v-col>
                    <v-col cols="12" md="4"><v-text-field v-model="nuevoCliente.referencia_telefono" label="Teléfono de referencia *" variant="outlined" density="comfortable" required prepend-inner-icon="mdi-phone" dark class="custom-input" placeholder="Ej: 04121234567" /></v-col>
                    <v-col cols="12" md="4"><v-select v-model="nuevoCliente.referencia_parentesco" :items="['Vecino', 'Familiar', 'Jefe de trabajo', 'Amigo', 'Otro']" label="Parentesco/Relación *" variant="outlined" density="comfortable" required dark class="custom-input" /></v-col>
                  </v-row>
                  <v-btn color="#4caf50" @click="registrarCliente" block size="large" :disabled="!registroValido" elevation="0" class="btn-registrar rounded-xl mt-2"><v-icon start>mdi-account-plus</v-icon>Registrar Cliente</v-btn>
                </div>
              </div>
            </v-card-text>
          </v-card>
        </div>

        <!-- PASO 2: Monto en BS -->
        <v-col cols="12" v-if="paso === 2">
          <v-card class="glass-card rounded-xl" elevation="0">
            <v-card-title class="text-h5 pa-4 text-white"><v-icon start color="#4facfe">mdi-currency-brl</v-icon>2. Monto de la Compra</v-card-title>
            <v-card-text class="pa-4">
              <div class="glass-effect pa-3 mb-4">
                <div class="d-flex justify-space-between flex-wrap" style="gap: 8px;">
                  <div class="text-white"><strong>Cliente:</strong> {{ clienteEncontrado?.nombre }}</div>
                  <div class="text-white"><strong>Disponible:</strong> <span class="text-success">${{ clienteEncontrado?.limite_disponible?.disponible_usd || 0 }}</span></div>
                </div>
              </div>
              
              <v-text-field v-model="montoTotalBS" label="Monto Total en Bolívares" type="number" @input="calcularPropuesta" variant="outlined" density="comfortable" hint="Ingrese el monto en Bolívares" persistent-hint prepend-inner-icon="mdi-cash" dark class="custom-input" placeholder="Ej: 5.000,00" />
              
              <div class="text-caption mb-2" v-if="tasaDolar && montoTotalBS"><v-icon color="info" size="small">mdi-information</v-icon>Equivalente: ~${{ (parseFloat(montoTotalBS) / tasaDolar).toFixed(2) }} USD</div>

              <v-alert v-if="excedeLimite" type="error" class="mt-3 rounded-xl" border="start" prominent>
                <v-icon start>mdi-cancel</v-icon><strong>Monto excede el límite disponible</strong>
              </v-alert>
              
              <v-alert v-if="propuesta && !excedeLimite" type="info" class="mt-3 rounded-xl" border="start">
                <h3 class="text-h6 mb-2">📋 Propuesta de Financiamiento</h3>
                <v-row>
                  <v-col cols="12" md="6">
                    <div class="d-flex justify-space-between pa-2 rounded-lg" style="background: rgba(255,255,255,0.05);">
                      <span class="text-white">Monto Total:</span>
                      <strong class="text-white">BS {{ formatearNumero(propuesta.propuesta?.monto_solicitado_bs || propuesta.monto_total_bs) }}</strong>
                    </div>
                  </v-col>
                  <v-col cols="12" md="6">
                    <div class="d-flex justify-space-between pa-2 rounded-lg" style="background: rgba(0,0,0,0.3);">
                      <span class="text-white">💳 Entrada HOY ({{ propuesta.propuesta?.entrada_pct || propuesta.entrada_pct }}%):</span>
                      <strong class="text-warning">BS {{ formatearNumero(propuesta.propuesta?.entrada_bs || propuesta.monto_entrada_bs) }}</strong>
                    </div>
                    <div class="d-flex justify-space-between pa-2 mt-1 rounded-lg" style="background: rgba(0,0,0,0.3);">
                      <span class="text-white">📊 A financiar:</span>
                      <strong class="text-success">BS {{ formatearNumero(propuesta.propuesta?.financia_bs || propuesta.monto_financia_bs) }}</strong>
                    </div>
                  </v-col>
                </v-row>
              </v-alert>
              
              <div v-if="propuesta && !excedeLimite" class="mt-3">
                <label class="text-subtitle-2 font-weight-bold text-white">Seleccionar cuotas:</label>
                <v-radio-group v-model="cuotasSeleccionadas" class="mt-2">
                  <v-radio v-for="cuota in opcionesCuotas" :key="cuota.value" :value="cuota.value" color="#4facfe">
                    <template v-slot:label><div class="text-white"><strong>{{ cuota.value }} cuotas</strong><span class="text-caption ml-2">BS {{ formatearNumero(cuota.monto) }} c/u</span></div></template>
                  </v-radio>
                </v-radio-group>
              </div>
              
              <div class="d-flex mt-4" style="gap: 8px;">
                <v-btn @click="paso = 1" variant="text" color="grey"><v-icon start>mdi-arrow-left</v-icon>Volver</v-btn>
                <v-btn v-if="cuotasSeleccionadas && !excedeLimite" color="#4caf50" @click="paso = 3" class="flex-grow-1" size="large" elevation="0" rounded="xl">Confirmar <v-icon end>mdi-arrow-right</v-icon></v-btn>
              </div>
            </v-card-text>
          </v-card>
        </v-col>

        <!-- PASO 3: CONFIRMAR VENTA -->
        <v-col cols="12" v-if="paso === 3">
          <v-card class="glass-card rounded-xl" elevation="0">
            <v-card-title class="text-h5 pa-4 text-white"><v-icon start color="#FFD700">mdi-check-circle</v-icon>3. Confirmar Venta</v-card-title>
            <v-card-text class="pa-4">
              
              <!-- CATEGORÍAS -->
              <div class="mb-4">
                <h4 class="text-subtitle-1 font-weight-bold text-white mb-3"><v-icon color="#4facfe" class="mr-1">mdi-shape</v-icon>¿Qué estás comprando?</h4>
                <div class="categorias-grid">
                  <div v-for="cat in categorias" :key="cat.title" class="categoria-item glass-effect"
                    :class="{ 'categoria-seleccionada': categoriaSeleccionada?.title === cat.title }"
                    :style="categoriaSeleccionada?.title === cat.title ? `border-color: ${cat.color} !important; background: ${cat.color}22 !important;` : ''"
                    @click="categoriaSeleccionada = cat">
                    <v-icon :color="cat.color" size="28">{{ cat.icon }}</v-icon>
                    <span class="text-white text-caption mt-1 font-weight-bold">{{ cat.title }}</span>
                  </div>
                </div>
              </div>

              <!-- DESCRIPCIÓN -->
              <div class="glass-effect pa-4 mb-3 rounded-lg">
                <div class="d-flex align-center mb-2">
                  <v-icon color="#4facfe" class="mr-2">mdi-clipboard-text</v-icon>
                  <span class="text-white font-weight-bold">Descripción</span>
                  <v-spacer></v-spacer>
                  <v-chip v-if="categoriaSeleccionada" :color="categoriaSeleccionada.color" size="x-small" variant="tonal">{{ categoriaSeleccionada.title }}</v-chip>
                </div>
                <div v-if="categoriaSeleccionada" class="pa-3 rounded-lg" :style="`background: ${categoriaSeleccionada.color}15; border-left: 3px solid ${categoriaSeleccionada.color};`">
                  <v-icon :color="categoriaSeleccionada.color" size="20" class="mr-2">{{ categoriaSeleccionada.icon }}</v-icon>
                  <span class="text-white font-weight-bold">{{ categoriaSeleccionada.title }}</span>
                </div>
                <p v-else class="text-caption" style="color: rgba(255,255,255,0.4);">Selecciona una categoría arriba</p>
              </div>

              <!-- NÚMERO DE FACTURA -->
              <div class="glass-effect pa-4 mb-3 rounded-lg">
                <div class="d-flex align-center mb-2">
                  <v-icon color="#FFD700" class="mr-2">mdi-receipt</v-icon>
                  <span class="text-white font-weight-bold">Número de Factura</span>
                  <v-spacer></v-spacer>
                  <span class="text-caption" style="color: rgba(255,255,255,0.4);">Opcional</span>
                </div>
                <v-text-field v-model="numeroFactura" label="Número de factura / control" placeholder="Ej: FAC-001-12345" variant="outlined" density="comfortable" prepend-inner-icon="mdi-numeric" dark class="custom-input" clearable />
              </div>

              <!-- RESUMEN -->
              <div class="glass-effect pa-4 mb-3 rounded-lg">
                <h3 class="text-h6 mb-2 text-white">📋 Resumen</h3>
                <v-row>
                  <v-col cols="12" md="6">
                    <p class="text-white"><strong>Cliente:</strong> {{ clienteEncontrado?.nombre }}</p>
                    <p class="text-white"><strong>Monto Total:</strong> BS {{ formatearNumero(montoTotalBS) }}</p>
                    <p class="text-white" v-if="categoriaSeleccionada"><strong>Categoría:</strong> {{ categoriaSeleccionada.title }}</p>
                  </v-col>
                  <v-col cols="12" md="6">
                    <p style="color: #FFD54F;"><strong>💳 Entrada:</strong> BS {{ formatearNumero(propuesta?.propuesta?.entrada_bs || propuesta?.monto_entrada_bs) }}</p>
                    <p class="text-success"><strong>📊 Financia:</strong> BS {{ formatearNumero(propuesta?.propuesta?.financia_bs || propuesta?.monto_financia_bs) }}</p>
                    <p class="text-white"><strong>Cuotas:</strong> {{ cuotasSeleccionadas }} quincenales</p>
                  </v-col>
                </v-row>
              </div>

              <div class="d-flex mt-4" style="gap: 8px;">
                <v-btn @click="paso = 2" variant="text" color="grey"><v-icon start>mdi-arrow-left</v-icon>Volver</v-btn>
                <v-btn color="#4caf50" @click="crearFinanciamiento" class="flex-grow-1" size="large" elevation="0" rounded="xl" :disabled="!categoriaSeleccionada">
                  <v-icon start>mdi-cash-check</v-icon>Cobrar y Crear Financiamiento
                </v-btn>
              </div>
            </v-card-text>
          </v-card>
        </v-col>

        <!-- PASO 4: Éxito -->
        <v-col cols="12" v-if="paso === 4">
          <v-card class="glass-card rounded-xl" elevation="0" color="transparent">
            <v-card-text class="pa-6 text-center">
              <div class="success-icon-wrapper"><v-icon size="80" color="#4caf50">mdi-check-circle-outline</v-icon></div>
              <h2 class="text-h3 font-weight-bold text-white mt-3">✅ Financiamiento Creado</h2>
              <h3 class="text-h5 mt-2 text-white" style="opacity: 0.8;">{{ resultado?.financiamiento?.codigo }}</h3>
              <v-btn color="#4facfe" @click="resetear" block class="mt-4 font-weight-bold" size="large" rounded="xl" elevation="0"><v-icon start>mdi-plus</v-icon>Nueva Venta</v-btn>
            </v-card-text>
          </v-card>
        </v-col>
      </v-col>
    </v-row>
  </v-container>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { api } from '@/config/api'

const paso = ref(1)
const busquedaCedula = ref('')
const clienteEncontrado = ref(null)
const clienteNoEncontrado = ref(false)
const montoTotalBS = ref('')
const propuesta = ref(null)
const cuotasSeleccionadas = ref(null)
const numeroFactura = ref('')
const resultado = ref({})
const tasaDolar = ref(40.0)
const excedeLimite = ref(false)
const cargando = ref(false)
const categoriaSeleccionada = ref(null)

const nuevoCliente = ref({
  nombre: '', telefono: '', email: '', cedula: '',
  direccion: '', referencia_nombre: '', referencia_telefono: '', referencia_parentesco: ''
})

const categorias = [
  { title: 'Feria', icon: 'mdi-basket', color: '#FF9800' },
  { title: 'Salud', icon: 'mdi-hospital-box', color: '#EF5350' },
  { title: 'Odontología', icon: 'mdi-tooth', color: '#42A5F5' },
  { title: 'Laboratorio', icon: 'mdi-flask', color: '#AB47BC' },
  { title: 'Otros', icon: 'mdi-dots-horizontal', color: '#B0BEC5' }
]
const porcentajeUsado = computed(() => {
  if (!clienteEncontrado.value) return 0
  const l = clienteEncontrado.value.limite_disponible?.limite_usd || 0
  const u = clienteEncontrado.value.limite_disponible?.usado_usd || 0
  return l > 0 ? (u / l) * 100 : 0
})

const opcionesCuotas = computed(() => {
  if (!propuesta.value) return []
  
  const p = propuesta.value.propuesta || propuesta.value
  const config = propuesta.value.configuracion_nivel || {}
  
  // ✅ Obtener cuotas base y max del backend
  const cb = p.cuotas_base || config.cuotas_base || 1
  const cm = p.cuotas_max || config.cuotas_max || 1
  
  const fb = p.financia_bs || propuesta.value.monto_financia_bs || 0
  
  console.log('📊 Cuotas base:', cb)
  console.log('📊 Cuotas máx:', cm)
  console.log('📊 Monto a financiar:', fb)
  
  const o = []
  for (let i = cb; i <= cm; i++) {
    o.push({ value: i, monto: fb / i })
  }
  
  console.log('✅ Opciones de cuotas:', o)
  return o
})

const montoCuotaSeleccionada = computed(() => {
  return opcionesCuotas.value.find(o => o.value === cuotasSeleccionadas.value)?.monto || 0
})

const registroValido = computed(() =>
  nuevoCliente.value.nombre && nuevoCliente.value.telefono && nuevoCliente.value.email &&
  nuevoCliente.value.direccion && nuevoCliente.value.referencia_nombre &&
  nuevoCliente.value.referencia_telefono && nuevoCliente.value.referencia_parentesco
)

const formatearNumero = (num) => num ? Number(num).toLocaleString('es-VE', { minimumFractionDigits: 2, maximumFractionDigits: 2 }) : '0,00'
const nivelColor = (n) => ({ nuevo: 'grey', bronce: 'brown', plata: 'blue-grey', oro: 'amber', platino: 'deep-purple' })[n] || 'grey'
const nivelGradiente = (n) => ({ nuevo: 'linear-gradient(135deg, #78909C, #546E7A)', bronce: 'linear-gradient(135deg, #A1887F, #6D4C41)', plata: 'linear-gradient(135deg, #90A4AE, #546E7A)', oro: 'linear-gradient(135deg, #FFD54F, #F9A825)', platino: 'linear-gradient(135deg, #7E57C2, #4A148C)' })[n] || ''
const nivelIcono = (n) => ({ nuevo: 'mdi-star-outline', bronce: 'mdi-medal-outline', plata: 'mdi-silverware', oro: 'mdi-gold', platino: 'mdi-diamond-stone' })[n] || 'mdi-star'

const colorCategoria = (cat) => {
  const colores = {
    'Feria': '#FF9800',
    'Salud': '#EF5350',
    'Odontología': '#42A5F5',
    'Laboratorio': '#AB47BC',
    'Otros': '#B0BEC5'
  }
  return colores[cat] || '#B0BEC5'
}

onMounted(async () => { try { const d = await api.get('/config/tasa-dolar'); tasaDolar.value = d.tasa } catch (e) {} })

const buscarCliente = async () => {
  if (!busquedaCedula.value) return
  cargando.value = true
  try {
    const data = await api.get(`/clientes/buscar/${busquedaCedula.value}`)
    
    // 🔍 DEBUG: Ver qué devuelve el backend
    console.log('📦 Respuesta del backend:', data)
    
    // ✅ Si data tiene id, el cliente existe
    if (data && data.id) {
      // ✅ NORMALIZAR: Convertir limite_disponible_usd a estructura limite_disponible
      clienteEncontrado.value = {
        ...data,
        limite_disponible: {
          limite_usd: data.limite_total_usd || data.limite_usd || 0,
          usado_usd: data.usado_usd || 0,
          disponible_usd: data.limite_disponible_usd || data.disponible_usd || 0
        }
      }
      
      console.log('✅ Cliente normalizado:', clienteEncontrado.value)
      
      clienteNoEncontrado.value = false
      
      // Obtener financiamientos activos
      try {
        const financiamientos = await api.get(`/financiamientos/cliente/${data.id}/activos`)
        const lista = Array.isArray(financiamientos) ? financiamientos : (financiamientos.financiamientos || [])
        clienteEncontrado.value = { 
          ...clienteEncontrado.value, 
          financiamientos_activos: lista 
        }
        
        console.log('📋 Financiamientos:', lista)
      } catch (e) {
        console.warn('⚠️ Error obteniendo financiamientos:', e)
        clienteEncontrado.value = { 
          ...clienteEncontrado.value, 
          financiamientos_activos: [] 
        }
      }
    } else {
      clienteEncontrado.value = null
      clienteNoEncontrado.value = true
      nuevoCliente.value.cedula = busquedaCedula.value
    }
  } catch (e) {
    console.error('❌ Error buscando cliente:', e)
    clienteEncontrado.value = null
    clienteNoEncontrado.value = true
    nuevoCliente.value.cedula = busquedaCedula.value
  } finally {
    cargando.value = false
  }
}

const registrarCliente = async () => {
  if (!registroValido.value) { alert('Complete todos los campos'); return }
  try {
    await api.post('/clientes', { ...nuevoCliente.value, cedula: busquedaCedula.value })
    alert('✅ Cliente registrado')
    await buscarCliente()
  } catch (e) { alert('Error registrando') }
}

const calcularPropuesta = async () => {
  if (!montoTotalBS.value || parseFloat(montoTotalBS.value) <= 0 || !clienteEncontrado.value) {
    propuesta.value = null
    cuotasSeleccionadas.value = null
    excedeLimite.value = false
    return
  }
  
  const tasa = tasaDolar.value || 40
  const montoUSD = parseFloat(montoTotalBS.value) / tasa
  const disponibleUSD = clienteEncontrado.value?.limite_disponible?.disponible_usd || 0
  
  if (montoUSD > disponibleUSD) {
    excedeLimite.value = true
    return
  }
  
  excedeLimite.value = false
  
  try {
    // 1. Obtener propuesta del backend
    const data = await api.get(`/clientes/${clienteEncontrado.value.id}/nivel-propuesta?monto_total_bs=${montoTotalBS.value}`)
    
    // 2. Obtener configuración ACTUALIZADA de niveles desde la BD
    const nivelesData = await api.get('/config/niveles')
    const niveles = nivelesData?.niveles || nivelesData || {}
    
    // 3. Obtener el nivel REAL del cliente
    const nivelCliente = clienteEncontrado.value?.nivel || 'nuevo'
    const configNivel = niveles[nivelCliente] || niveles.nuevo || {}
    
    console.log('🏷️ Nivel cliente:', nivelCliente)
    console.log('📊 Config BD:', configNivel)
    
    // 4. Usar cuotas de la BD (siempre actualizadas)
    const cuotasBase = configNivel.cuotas_base || 2
    const cuotasMax = configNivel.cuotas_max || 2
    const entradaPct = configNivel.entrada_pct || 50
    const financiaPct = configNivel.financia_pct || 50
    
    // 5. Calcular montos con los porcentajes correctos
    const entradaBS = parseFloat(montoTotalBS.value) * (entradaPct / 100)
    const financiaBS = parseFloat(montoTotalBS.value) - entradaBS
    
    // 6. Actualizar propuesta con valores correctos
    propuesta.value = {
      ...data,
      propuesta: {
        ...data.propuesta,
        cuotas_base: cuotasBase,
        cuotas_max: cuotasMax,
        entrada_pct: entradaPct,
        financia_pct: financiaPct,
        entrada_bs: entradaBS,
        financia_bs: financiaBS
      },
      configuracion_nivel: {
        ...data.configuracion_nivel,
        ...configNivel,
        cuotas_base: cuotasBase,
        cuotas_max: cuotasMax
      }
    }
    
    // 7. Seleccionar cuota base por defecto
    cuotasSeleccionadas.value = cuotasBase
    
    console.log('✅ Cuotas BD:', cuotasBase, '-', cuotasMax)
    console.log('✅ Entrada:', entradaPct + '%', '| Financia:', financiaPct + '%')
    
  } catch (e) {
    console.error('❌ Error calculando propuesta:', e)
    propuesta.value = null
  }
}

const crearFinanciamiento = async () => {
  try {
    console.log('📤 Enviando financiamiento:', {
      cliente_id: clienteEncontrado.value.id,
      descripcion: categoriaSeleccionada.value?.title || 'Compra',
      monto_total_bs: parseFloat(montoTotalBS.value),
      cuotas_solicitadas: cuotasSeleccionadas.value,
      numero_factura: numeroFactura.value || null
    })
    
    const data = await api.post('/financiamientos', {
      cliente_id: clienteEncontrado.value.id,
      descripcion: categoriaSeleccionada.value?.title || 'Compra',
      monto_total_bs: parseFloat(montoTotalBS.value),
      cuotas_solicitadas: cuotasSeleccionadas.value,
      numero_factura: numeroFactura.value || null
    })
    
    console.log('✅ Respuesta exitosa:', data)
    
    if (data.error) { 
      alert('Error: ' + data.error)
      return 
    }
    resultado.value = data
    paso.value = 4
  } catch (e) {
    console.error('❌ Error completo:', e)
    console.error('❌ Detalle del error:', e.response?.data?.detail)
    
    // Mostrar error detallado
    const detalle = e.response?.data?.detail || 'Error creando financiamiento'
    alert('❌ ' + detalle)
  }
}

const resetear = () => {
  paso.value = 1; busquedaCedula.value = ''; clienteEncontrado.value = null; clienteNoEncontrado.value = false
  montoTotalBS.value = ''; propuesta.value = null; cuotasSeleccionadas.value = null
  numeroFactura.value = ''; resultado.value = {}; categoriaSeleccionada.value = null
}
</script>

<style scoped>
.background-gradient { position: fixed; top: 0; left: 0; right: 0; bottom: 0; background: radial-gradient(ellipse at 20% 50%, rgba(79,172,254,0.12), transparent 70%), radial-gradient(ellipse at 80% 50%, rgba(99,102,241,0.08), transparent 70%), #0a0e1a; z-index: 0; }
.header-premium { position: relative; z-index: 1; padding: 16px 24px; background: rgba(255,255,255,0.05); backdrop-filter: blur(20px); border-radius: 20px; border: 1px solid rgba(255,255,255,0.06); }
.icon-wrapper { width: 48px; height: 48px; background: linear-gradient(135deg, #4facfe, #6366f1); border-radius: 14px; display: flex; align-items: center; justify-content: center; }
.pulse-animation { animation: pulse 2s infinite; }
@keyframes pulse { 0%, 100% { transform: scale(1); } 50% { transform: scale(1.05); } }
.tasa-card { padding: 8px 16px; border-radius: 12px; display: flex; align-items: center; gap: 6px; }
.step-chip { background: rgba(255,255,255,0.08) !important; padding: 8px 16px !important; border-radius: 50px !important; }
.glass-effect { background: rgba(255,255,255,0.05) !important; backdrop-filter: blur(16px) !important; border: 1px solid rgba(255,255,255,0.08) !important; border-radius: 16px !important; }
.glass-card { background: rgba(255,255,255,0.03) !important; backdrop-filter: blur(24px) !important; border: 1px solid rgba(255,255,255,0.06) !important; border-radius: 24px !important; }
.cliente-premium-card { position: relative; border-radius: 20px; padding: 4px; overflow: hidden; box-shadow: 0 8px 40px rgba(0,0,0,0.3); }
.nivel-nuevo { background: linear-gradient(135deg, #78909C, #37474F) !important; }
.nivel-bronce { background: linear-gradient(135deg, #A1887F, #4E342E) !important; }
.nivel-plata { background: linear-gradient(135deg, #90A4AE, #37474F) !important; }
.nivel-oro { background: linear-gradient(135deg, #FFD54F, #F57F17) !important; }
.nivel-platino { background: linear-gradient(135deg, #7E57C2, #311B92) !important; }
.avatar-wrapper { position: relative; }
.avatar-premium { border: 3px solid rgba(255,255,255,0.3); box-shadow: 0 4px 20px rgba(0,0,0,0.3); }
.level-badge { position: absolute; bottom: -4px; right: -4px; font-size: 8px; font-weight: 800; padding: 2px 8px; border-radius: 50px; color: white; letter-spacing: 0.5px; border: 2px solid rgba(0,0,0,0.2); }
.level-nuevo { background: #546E7A; } .level-bronce { background: #6D4C41; } .level-plata { background: #546E7A; } .level-oro { background: #F9A825; } .level-platino { background: #4A148C; }
.info-pill { display: flex; align-items: center; gap: 4px; background: rgba(255,255,255,0.08); padding: 2px 10px; border-radius: 50px; }
.status-chip { font-weight: 600 !important; }
.disponible-wrapper { background: rgba(0,0,0,0.2); padding: 8px 24px; border-radius: 16px; backdrop-filter: blur(8px); }
.disponible-number { font-size: 2.2rem; font-weight: 800; color: white; line-height: 1.2; }
.disponible-label { font-size: 0.7rem; color: rgba(255,255,255,0.6); text-transform: uppercase; letter-spacing: 1px; }
.limite-card { padding: 16px 20px; }
.metric-item { display: flex; flex-direction: column; }
.metric-label { font-size: 0.65rem; color: rgba(255,255,255,0.4); text-transform: uppercase; letter-spacing: 0.5px; }
.metric-value { font-size: 1rem; font-weight: 700; color: white; }
.metric-divider { width: 1px; height: 30px; background: rgba(255,255,255,0.1); }
.progress-wrapper { position: relative; }
.progress-bar-custom { border-radius: 50px !important; overflow: hidden; }
.financiamientos-header { padding: 4px 0; }
.financiamientos-grid { display: flex; flex-direction: column; gap: 8px; }
.financiamiento-item { padding: 12px 16px; border-radius: 12px; transition: all 0.3s ease; }
.empty-state { padding: 24px; text-align: center; border: 1px dashed rgba(255,255,255,0.08); }
.btn-continuar { background: linear-gradient(135deg, #4facfe, #6366f1) !important; color: white !important; font-weight: 700 !important; font-size: 1.1rem !important; transition: all 0.3s ease !important; height: 56px !important; }
.btn-registrar { background: linear-gradient(135deg, #4caf50, #2e7d32) !important; color: white !important; font-weight: 700 !important; }
.custom-input :deep(.v-field) { background: rgba(255,255,255,0.05) !important; border-radius: 12px !important; border: 1px solid rgba(255,255,255,0.1) !important; }
.custom-input :deep(.v-field--focused) { border-color: #4facfe !important; }
.custom-input :deep(.v-label) { color: rgba(255,255,255,0.6) !important; }
.custom-input :deep(.v-field__input) { color: white !important; }
.categorias-grid { display: grid; grid-template-columns: repeat(5, 1fr); gap: 10px; }
.categoria-item { display: flex; flex-direction: column; align-items: center; justify-content: center; padding: 14px 8px; border-radius: 16px; cursor: pointer; transition: all 0.3s ease; min-height: 80px; }
.categoria-item:hover { transform: translateY(-4px); }
.categoria-seleccionada { transform: translateY(-4px); box-shadow: 0 8px 24px rgba(0,0,0,0.3); }
.font-mono { font-family: monospace; font-size: 11px; }
.fade-in { animation: fadeIn 0.5s ease; }
@keyframes fadeIn { from { opacity: 0; transform: translateY(20px); } to { opacity: 1; transform: translateY(0); } }
.slide-up { animation: slideUp 0.4s ease; }
@keyframes slideUp { from { opacity: 0; transform: translateY(30px); } to { opacity: 1; transform: translateY(0); } }
@media (max-width: 600px) { .categorias-grid { grid-template-columns: repeat(3, 1fr); } }
</style>