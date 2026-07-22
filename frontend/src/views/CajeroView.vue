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
                <div class="search-hint"><v-icon size="14" color="rgba(255,255,255,0.3)">mdi-keyboard-return</v-icon><span class="text-caption" style="color: rgba(255,255,255,0.3);">Presiona Enter para buscar</span></div>
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
                    <v-chip :color="clienteEncontrado.limite_disponible?.disponible_usd > 0 ? 'success' : 'error'" size="small" class="status-chip">{{ clienteEncontrado.limite_disponible?.disponible_usd > 0 ? '✅ Puede comprar' : '❌ Sin saldo' }}</v-chip>
                  </div>
                  <div class="progress-wrapper mt-2">
                    <v-progress-linear :model-value="porcentajeUsado" :color="porcentajeUsado > 80 ? 'error' : porcentajeUsado > 50 ? 'warning' : 'success'" height="8" rounded class="progress-bar-custom">
                      <template v-slot:default="{ value }"><span class="progress-text">{{ Math.round(value) }}% usado</span></template>
                    </v-progress-linear>
                  </div>
                </div>

                <!-- FINANCIAMIENTOS ACTIVOS -->
                <div v-if="clienteEncontrado.financiamientos_activos && clienteEncontrado.financiamientos_activos.length > 0" class="mt-3">
                  <div class="financiamientos-header d-flex align-center"><v-icon color="#FFD700" class="mr-2">mdi-clock-outline</v-icon><h4 class="text-subtitle-1 font-weight-bold text-white">Compras Activas</h4><v-chip size="small" color="#FFD700" class="ml-2">{{ clienteEncontrado.financiamientos_activos.length }}</v-chip></div>
                  <div class="financiamientos-grid mt-2">
                    <div v-for="fin in clienteEncontrado.financiamientos_activos" :key="fin.id" class="financiamiento-item glass-effect">
                      <div class="d-flex justify-space-between align-center flex-wrap" style="gap: 8px;">
                        <div class="d-flex align-center flex-wrap" style="gap: 8px;">
                          <v-chip size="small" color="info" variant="flat" class="tienda-chip"><v-icon start size="12">mdi-store</v-icon>{{ fin.tienda_nombre || 'Sin tienda' }}</v-chip>
                          <v-chip size="x-small" variant="outlined" class="text-white">{{ fin.codigo }}</v-chip>
                          <span class="text-white font-weight-bold">${{ formatearNumero(fin.monto_total_usd) }}<span class="text-caption" style="color: rgba(255,255,255,0.4);">(BS {{ formatearNumero(fin.monto_total_bs) }})</span></span>
                        </div>
                        <div class="d-flex align-center" style="gap: 8px;">
                          <v-chip size="x-small" :color="fin.cuotas_pagadas === fin.cuotas_aprobadas ? 'success' : 'primary'" variant="tonal">{{ fin.cuotas_pagadas || 0 }}/{{ fin.cuotas_aprobadas }} cuotas</v-chip>
                          <v-chip size="x-small" :color="fin.estado === 'activo' ? 'success' : 'warning'" variant="flat">{{ fin.estado }}</v-chip>
                        </div>
                      </div>
                      <div class="text-caption mt-1" style="color: rgba(255,255,255,0.4);" v-if="fin.descripcion"><v-icon size="12" color="rgba(255,255,255,0.3)">mdi-clipboard-text</v-icon>{{ fin.descripcion }}</div>
                    </div>
                  </div>
                </div>
                <div v-else class="mt-3"><div class="empty-state glass-effect"><v-icon color="rgba(255,255,255,0.3)" size="32">mdi-check-circle</v-icon><div class="text-caption" style="color: rgba(255,255,255,0.4);">No tiene compras activas</div></div></div>

                <!-- BOTÓN CONTINUAR -->
                <div class="mt-4">
                  <v-btn v-if="clienteEncontrado.limite_disponible?.disponible_usd > 0 && (clienteEncontrado?.cuotas_vencidas || 0) === 0" color="#4facfe" @click="paso = 2" size="x-large" block elevation="0" class="btn-continuar rounded-xl"><span class="font-weight-bold">Continuar con la venta</span><v-icon end>mdi-arrow-right</v-icon></v-btn>
                  <v-alert v-else type="error" variant="tonal" class="rounded-xl" border="start">
                    <div class="d-flex align-center"><v-icon color="error" size="28" class="mr-2">mdi-alert-circle</v-icon>
                      <div>
                        <strong class="text-white" v-if="(clienteEncontrado?.cuotas_vencidas || 0) > 0">⚠️ Cliente con {{ clienteEncontrado.cuotas_vencidas }} cuota(s) vencida(s)</strong>
                        <strong class="text-white" v-else>Cliente sin saldo disponible</strong>
                        <div class="text-caption" style="color: rgba(255,255,255,0.6);"><span v-if="(clienteEncontrado?.cuotas_vencidas || 0) > 0">Debe ponerse al día antes de comprar</span><span v-else>Ha alcanzado el límite máximo de crédito</span></div>
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
                  <h4 class="text-subtitle-2 font-weight-bold text-white mb-2"><v-icon size="18" class="mr-1" color="rgba(255,255,255,0.6)">mdi-account-group</v-icon>Referencia personal (obligatorio)</h4>
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
                  <v-chip :color="nivelColor(clienteEncontrado?.nivel)" text-color="white" size="small">{{ clienteEncontrado?.nivel?.toUpperCase() }}</v-chip>
                  <div class="text-white"><strong>Disponible:</strong> <span class="text-success">${{ clienteEncontrado?.limite_disponible?.disponible_usd || 0 }}</span></div>
                  <div class="text-white"><strong>Límite:</strong> ${{ clienteEncontrado?.limite_disponible?.limite_usd || 0 }}</div>
                </div>
              </div>
              
              <v-text-field v-model="montoTotalBS" label="Monto Total en Bolívares" type="number" prefix="BS" @input="calcularPropuesta" variant="outlined" density="comfortable" hint="Ingrese el monto en Bolívares" persistent-hint prepend-inner-icon="mdi-currency-brl" dark class="custom-input" placeholder="Ej: 5000" />
              
              <div class="text-caption mb-2" v-if="tasaDolar && montoTotalBS"><v-icon color="info" size="small">mdi-information</v-icon>Equivalente: ~${{ (parseFloat(montoTotalBS) / tasaDolar).toFixed(2) }} USD</div>

              <v-alert v-if="excedeLimite" type="error" class="mt-3 rounded-xl" border="start" prominent>
                <v-icon start>mdi-cancel</v-icon><strong>Monto excede el límite disponible</strong>
                <div class="text-caption mt-1">Límite disponible: <strong>${{ clienteEncontrado?.limite_disponible?.disponible_usd || 0 }} USD</strong> | Solicitado: <strong>~${{ ((parseFloat(montoTotalBS) || 0) / (tasaDolar || 40)).toFixed(2) }} USD</strong></div>
              </v-alert>
              
              <v-alert v-if="propuesta && !excedeLimite" type="info" class="mt-3 rounded-xl" border="start">
                <h3 class="text-h6 mb-2">📋 Propuesta de Financiamiento</h3>
                <v-divider class="my-2"></v-divider>
                <v-row>
                  <v-col cols="12" md="6">
                    <div class="d-flex justify-space-between pa-2 rounded-lg" style="background: rgba(255,255,255,0.05);">
                      <span class="text-white" style="opacity: 0.7;">Monto Total:</span>
                      <strong class="text-white">BS {{ formatearNumero(propuesta.propuesta?.monto_solicitado_bs || propuesta.monto_total_bs) }}</strong>
                    </div>
                    <div class="d-flex justify-space-between pa-2 mt-1" style="background: rgba(255,255,255,0.03);">
                      <span class="text-white" style="opacity: 0.7;">Monto en USD:</span>
                      <strong class="text-white">${{ formatearNumero(propuesta.propuesta?.monto_solicitado_usd || propuesta.monto_total_usd) }}</strong>
                    </div>
                  </v-col>
                  <v-col cols="12" md="6">
                    <div class="d-flex justify-space-between pa-2 rounded-lg" style="background: rgba(0,0,0,0.3);">
                      <span class="text-white" style="opacity: 0.9;">💳 Entrada HOY ({{ propuesta.propuesta?.entrada_pct || propuesta.entrada_pct }}%):</span>
                      <strong class="text-warning">BS {{ formatearNumero(propuesta.propuesta?.entrada_bs || propuesta.monto_entrada_bs) }}</strong>
                    </div>
                    <div class="d-flex justify-space-between pa-2 mt-1 rounded-lg" style="background: rgba(0,0,0,0.3);">
                      <span class="text-white" style="opacity: 0.9;">📊 A financiar ({{ propuesta.propuesta?.financia_pct || propuesta.financia_pct }}%):</span>
                      <strong class="text-success">BS {{ formatearNumero(propuesta.propuesta?.financia_bs || propuesta.monto_financia_bs) }}</strong>
                    </div>
                  </v-col>
                </v-row>
                <div class="d-flex justify-space-between pa-2 mt-2 rounded-lg" style="background: rgba(0,0,0,0.3);">
                  <span class="text-white" style="opacity: 0.9;">💰 Disponible después:</span>
                  <strong class="text-white">${{ formatearNumero(clienteEncontrado?.limite_disponible?.disponible_usd - (propuesta.propuesta?.monto_solicitado_usd || 0)) }}</strong>
                </div>
              </v-alert>
              
              <div v-if="propuesta && !excedeLimite" class="mt-3">
                <label class="text-subtitle-2 font-weight-bold text-white">Seleccionar cuotas:</label>
                <v-radio-group v-model="cuotasSeleccionadas" class="mt-2">
                  <v-radio v-for="cuota in opcionesCuotas" :key="cuota.value" :value="cuota.value" color="#4facfe">
                    <template v-slot:label><div class="text-white"><strong>{{ cuota.value }} cuotas</strong><span class="text-caption ml-2" style="color: rgba(255,255,255,0.6);">BS {{ formatearNumero(cuota.monto) }} cada una<span style="color: rgba(255,255,255,0.3);">(${{ formatearNumero(cuota.monto_usd) }} ref.)</span></span></div></template>
                  </v-radio>
                </v-radio-group>
                <v-alert v-if="requiereAprobacion" type="warning" class="mt-2 rounded-xl" border="start">⚠️ Requiere aprobación para {{ cuotasSeleccionadas }} cuotas</v-alert>
              </div>
              
              <div class="d-flex mt-4" style="gap: 8px;">
                <v-btn @click="paso = 1" variant="text" color="grey"><v-icon start>mdi-arrow-left</v-icon>Volver</v-btn>
                <v-btn v-if="cuotasSeleccionadas && !excedeLimite" color="#4caf50" @click="paso = 3" class="flex-grow-1" size="large" elevation="0" rounded="xl">Confirmar Propuesta <v-icon end>mdi-arrow-right</v-icon></v-btn>
              </div>
            </v-card-text>
          </v-card>
        </v-col>

        <!-- PASO 3: CONFIRMAR VENTA (CON CATEGORÍAS + FACTURA) -->
        <v-col cols="12" v-if="paso === 3">
          <v-card class="glass-card rounded-xl" elevation="0">
            <v-card-title class="text-h5 pa-4 text-white">
              <v-icon start color="#FFD700">mdi-check-circle</v-icon>
              3. Confirmar Venta
            </v-card-title>
            <v-card-text class="pa-4">
              
              <!-- ✅ CATEGORÍAS TIPO CASHEA -->
              <div class="mb-4">
                <h4 class="text-subtitle-1 font-weight-bold text-white mb-3">
                  <v-icon color="#4facfe" class="mr-1">mdi-shape</v-icon>
                  ¿Qué estás comprando?
                </h4>
                <div class="categorias-grid">
                  <div 
                    v-for="cat in categorias" 
                    :key="cat.title"
                    class="categoria-item glass-effect"
                    :class="{ 'categoria-seleccionada': categoriaSeleccionada?.title === cat.title }"
                    :style="categoriaSeleccionada?.title === cat.title ? `border-color: ${cat.color} !important; background: ${cat.color}22 !important;` : ''"
                    @click="seleccionarCategoria(cat)"
                  >
                    <v-icon :color="cat.color" size="28">{{ cat.icon }}</v-icon>
                    <span class="text-white text-caption mt-1 font-weight-bold">{{ cat.title }}</span>
                  </div>
                </div>
              </div>

              <!-- ✅ DESCRIPCIÓN -->
              <div class="glass-effect pa-4 mb-3 rounded-lg">
                <div class="d-flex align-center mb-2">
                  <v-icon color="#4facfe" class="mr-2">mdi-clipboard-text</v-icon>
                  <span class="text-white font-weight-bold">Descripción de la compra</span>
                  <v-spacer></v-spacer>
                  <v-chip v-if="categoriaSeleccionada" :color="categoriaSeleccionada.color" size="x-small" variant="tonal">
                    {{ categoriaSeleccionada.title }}
                  </v-chip>
                </div>
                
                <div v-if="!descripcionManual && categoriaSeleccionada" class="descripcion-auto pa-3 rounded-lg" 
                     :style="`background: ${categoriaSeleccionada.color}15; border-left: 3px solid ${categoriaSeleccionada.color};`">
                  <v-icon :color="categoriaSeleccionada.color" size="16" class="mr-1">{{ categoriaSeleccionada.icon }}</v-icon>
                  <span class="text-white">{{ categoriaSeleccionada.descripcion }}</span>
                  <v-btn variant="text" size="x-small" color="grey" class="ml-2" @click="descripcionManual = categoriaSeleccionada.descripcion">
                    <v-icon size="14">mdi-pencil</v-icon> Editar
                  </v-btn>
                </div>
                
                <v-text-field 
                  v-if="descripcionManual || !categoriaSeleccionada"
                  v-model="descripcionManual"
                  label="Escribe la descripción de la compra"
                  placeholder="Ej: iPhone 15 Pro Max 256GB"
                  variant="outlined"
                  density="comfortable"
                  prepend-inner-icon="mdi-pencil"
                  dark
                  class="custom-input mt-2"
                  clearable
                  @click:clear="descripcionManual = ''"
                />
              </div>

              <!-- ✅ NÚMERO DE FACTURA -->
              <div class="glass-effect pa-4 mb-3 rounded-lg">
                <div class="d-flex align-center mb-2">
                  <v-icon color="#FFD700" class="mr-2">mdi-receipt</v-icon>
                  <span class="text-white font-weight-bold">Número de Factura</span>
                  <v-spacer></v-spacer>
                  <span class="text-caption" style="color: rgba(255,255,255,0.4);">Opcional</span>
                </div>
                <v-text-field 
                  v-model="numeroFactura"
                  label="Número de factura / control"
                  placeholder="Ej: FAC-001-12345"
                  variant="outlined"
                  density="comfortable"
                  prepend-inner-icon="mdi-numeric"
                  dark
                  class="custom-input"
                  clearable
                />
              </div>

              <!-- ✅ RESUMEN -->
              <div class="glass-effect pa-4 mb-3 rounded-lg">
                <h3 class="text-h6 mb-2 text-white">📋 Resumen de la Venta</h3>
                <v-divider class="my-2" style="border-color: rgba(255,255,255,0.1);"></v-divider>
                <v-row>
                  <v-col cols="12" md="6">
                    <p class="text-white"><strong>Cliente:</strong> {{ clienteEncontrado?.nombre }}</p>
                    <p class="text-white"><strong>Teléfono:</strong> {{ clienteEncontrado?.telefono }}</p>
                    <p class="text-white" v-if="numeroFactura"><strong>Factura:</strong> {{ numeroFactura }}</p>
                  </v-col>
                  <v-col cols="12" md="6">
                    <p class="text-white"><strong>Monto Total:</strong> BS {{ formatearNumero(montoTotalBS) }}</p>
                    <p style="color: #FFD54F;"><strong>💳 Entrada HOY:</strong> BS {{ formatearNumero(propuesta?.propuesta?.entrada_bs || propuesta?.monto_entrada_bs) }}</p>
                    <p class="text-success"><strong>📊 Financia:</strong> BS {{ formatearNumero(propuesta?.propuesta?.financia_bs || propuesta?.monto_financia_bs) }}</p>
                  </v-col>
                </v-row>
                <v-divider class="my-2" style="border-color: rgba(255,255,255,0.1);"></v-divider>
                <v-row>
                  <v-col cols="12" md="4"><p class="text-white"><strong>Cuotas:</strong> {{ cuotasSeleccionadas }} quincenales</p></v-col>
                  <v-col cols="12" md="4"><p class="text-white"><strong>Monto cuota:</strong> BS {{ formatearNumero(montoCuotaSeleccionada) }}</p></v-col>
                  <v-col cols="12" md="4"><p class="text-white"><strong>Total a pagar:</strong> BS {{ formatearNumero(parseFloat(montoTotalBS)) }}</p></v-col>
                </v-row>
              </div>

              <div class="d-flex mt-4" style="gap: 8px;">
                <v-btn @click="paso = 2" variant="text" color="grey"><v-icon start>mdi-arrow-left</v-icon>Volver</v-btn>
                <v-btn color="#4caf50" @click="crearFinanciamiento" class="flex-grow-1" size="large" elevation="0" rounded="xl" :disabled="!descripcionFinal">
                  <v-icon start>mdi-cash-check</v-icon>Cobrar Entrada y Crear Financiamiento
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
              <p class="text-body-1 mt-2 text-white" style="opacity: 0.7;">{{ resultado?.mensaje }}</p>
              <p v-if="numeroFactura" class="text-caption mt-1 text-white" style="opacity: 0.5;">Factura: {{ numeroFactura }}</p>
              <v-divider class="my-4" style="border-color: rgba(255,255,255,0.1);"></v-divider>
              <h4 class="mb-2 text-white">📅 Cuotas Generadas ({{ cuotasSeleccionadas }})</h4>
              <div class="glass-effect pa-3"><div v-for="n in cuotasSeleccionadas" :key="n" class="d-flex justify-space-between py-1" style="border-bottom: 1px solid rgba(255,255,255,0.05);"><span class="text-white font-weight-bold">Cuota #{{ n }}</span><span class="text-white" style="opacity: 0.7;">Vence: {{ fechaCuota(n) }} | BS {{ formatearNumero(resultado?.financiamiento?.monto_cuota_bs) }}</span></div></div>
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
const descripcionManual = ref('')
const numeroFactura = ref('')
const resultado = ref({})
const tasaDolar = ref(40.0)
const requiereAprobacion = ref(false)
const excedeLimite = ref(false)
const cargando = ref(false)
const categoriaSeleccionada = ref(null)

const nuevoCliente = ref({
  nombre: '', telefono: '', email: '', cedula: '',
  direccion: '', referencia_nombre: '', referencia_telefono: '', referencia_parentesco: ''
})

// ✅ CATEGORÍAS TIPO CASHEA
const categorias = [
  { title: 'Salud', icon: 'mdi-hospital-box', color: '#EF5350', descripcion: 'Consulta médica, medicinas, tratamiento' },
  { title: 'Ropa', icon: 'mdi-tshirt-crew', color: '#42A5F5', descripcion: 'Ropa, calzado, accesorios' },
  { title: 'Comida', icon: 'mdi-food', color: '#FFA726', descripcion: 'Alimentos, restaurante, mercado' },
  { title: 'Hogar', icon: 'mdi-home', color: '#66BB6A', descripcion: 'Muebles, electrodomésticos, decoración' },
  { title: 'Tecnología', icon: 'mdi-laptop', color: '#AB47BC', descripcion: 'Celular, computadora, tablet' },
  { title: 'Educación', icon: 'mdi-school', color: '#26C6DA', descripcion: 'Útiles, cursos, matrícula' },
  { title: 'Transporte', icon: 'mdi-car', color: '#78909C', descripcion: 'Repuestos, pasajes, mantenimiento' },
  { title: 'Belleza', icon: 'mdi-content-cut', color: '#EC407A', descripcion: 'Peluquería, cosméticos, cuidado personal' },
  { title: 'Deporte', icon: 'mdi-run', color: '#8D6E63', descripcion: 'Equipamiento, ropa deportiva, gimnasio' },
  { title: 'Otro', icon: 'mdi-dots-horizontal', color: '#B0BEC5', descripcion: 'Otra compra' }
]

const descripcionFinal = computed(() => {
  if (descripcionManual.value) return descripcionManual.value
  if (categoriaSeleccionada.value) return categoriaSeleccionada.value.descripcion
  return ''
})

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
  const cb = p.cuotas_base || config.cuotas_base || 4
  const cm = p.cuotas_max || config.cuotas_max || 12
  const fb = p.financia_bs || propuesta.value.monto_financia_bs || 0
  const o = []
  for (let i = cb; i <= cm; i++) {
    const mc = fb / i
    o.push({ value: i, monto: mc, monto_usd: mc / (propuesta.value.tasa_dolar_actual || tasaDolar.value || 40) })
  }
  return o
})

const montoCuotaSeleccionada = computed(() => {
  const op = opcionesCuotas.value.find(o => o.value === cuotasSeleccionadas.value)
  return op?.monto || 0
})

const registroValido = computed(() =>
  nuevoCliente.value.nombre && nuevoCliente.value.telefono && nuevoCliente.value.email &&
  nuevoCliente.value.direccion && nuevoCliente.value.referencia_nombre &&
  nuevoCliente.value.referencia_telefono && nuevoCliente.value.referencia_parentesco
)

const formatearNumero = (num) => num ? Number(num).toLocaleString('es-VE', { minimumFractionDigits: 2, maximumFractionDigits: 2 }) : '0,00'
const nivelColor = (nivel) => ({ nuevo: 'grey darken-2', bronce: 'brown darken-2', plata: 'blue-grey darken-2', oro: 'amber darken-2', platino: 'deep-purple darken-2' })[nivel] || 'grey'
const nivelGradiente = (nivel) => ({ nuevo: 'linear-gradient(135deg, #78909C, #546E7A)', bronce: 'linear-gradient(135deg, #A1887F, #6D4C41)', plata: 'linear-gradient(135deg, #90A4AE, #546E7A)', oro: 'linear-gradient(135deg, #FFD54F, #F9A825)', platino: 'linear-gradient(135deg, #7E57C2, #4A148C)' })[nivel] || 'linear-gradient(135deg, #78909C, #546E7A)'
const nivelIcono = (nivel) => ({ nuevo: 'mdi-star-outline', bronce: 'mdi-medal-outline', plata: 'mdi-silverware', oro: 'mdi-gold', platino: 'mdi-diamond-stone' })[nivel] || 'mdi-star'

function seleccionarCategoria(cat) {
  categoriaSeleccionada.value = cat
  descripcionManual.value = ''
}

onMounted(async () => { try { const d = await api.get('/config/tasa-dolar'); tasaDolar.value = d.tasa } catch (e) {} })

const buscarCliente = async () => {
  if (!busquedaCedula.value) return; cargando.value = true
  try {
    const data = await api.get(`/clientes/buscar/${busquedaCedula.value}`)
    if (data.error || !data.encontrado) { clienteEncontrado.value = null; clienteNoEncontrado.value = true; nuevoCliente.value.cedula = busquedaCedula.value }
    else {
      const financiamientos = await api.get(`/financiamientos?cliente_id=${data.id}&estado=activo`)
      const listaFinanciamientos = Array.isArray(financiamientos) ? financiamientos : (financiamientos.financiamientos || [])
      clienteEncontrado.value = { ...data, bloqueado: false, financiamientos_activos: listaFinanciamientos }; clienteNoEncontrado.value = false
    }
  } catch (e) { clienteEncontrado.value = null; clienteNoEncontrado.value = true }
  finally { cargando.value = false }
}

const registrarCliente = async () => {
  if (!registroValido.value) { alert('Complete todos los campos'); return }
  try { await api.post('/clientes', { nombre: nuevoCliente.value.nombre, cedula: busquedaCedula.value, telefono: nuevoCliente.value.telefono, email: nuevoCliente.value.email || '', direccion: nuevoCliente.value.direccion, referencia_nombre: nuevoCliente.value.referencia_nombre, referencia_telefono: nuevoCliente.value.referencia_telefono, referencia_parentesco: nuevoCliente.value.referencia_parentesco }); alert('✅ Cliente registrado'); await buscarCliente() } catch (e) { alert('Error registrando') }
}

const calcularPropuesta = async () => {
  if (!montoTotalBS.value || parseFloat(montoTotalBS.value) <= 0 || !clienteEncontrado.value) { propuesta.value = null; cuotasSeleccionadas.value = null; excedeLimite.value = false; return }
  const tasa = tasaDolar.value || 40; const montoUSD = parseFloat(montoTotalBS.value) / tasa; const disponibleUSD = clienteEncontrado.value?.limite_disponible?.disponible_usd || 0
  if (montoUSD > disponibleUSD) { excedeLimite.value = true; propuesta.value = null; cuotasSeleccionadas.value = null; return }
  excedeLimite.value = false
  try { const data = await api.get(`/clientes/${clienteEncontrado.value.id}/nivel-propuesta?monto_total_bs=${montoTotalBS.value}`); propuesta.value = data; cuotasSeleccionadas.value = data.propuesta?.cuotas_base || data.configuracion_nivel?.cuotas_base || 4; requiereAprobacion.value = data.propuesta?.requiere_aprobacion_extra || false } catch (e) { propuesta.value = null }
}

const fechaCuota = (n) => { const f = new Date(); f.setDate(f.getDate() + (15 * n)); return f.toLocaleDateString('es-VE') }

const crearFinanciamiento = async () => {
  try {
    const payload = {
      cliente_id: clienteEncontrado.value.id,
      descripcion: descripcionFinal.value || 'Compra',
      monto_total_bs: parseFloat(montoTotalBS.value),
      cuotas_solicitadas: cuotasSeleccionadas.value,
      numero_factura: numeroFactura.value || null
    }
    const data = await api.post('/financiamientos', payload)
    if (data.error) { alert('Error: ' + data.error); return }
    resultado.value = data; paso.value = 4
  } catch (e) { alert('Error creando financiamiento') }
}

const resetear = () => {
  paso.value = 1; busquedaCedula.value = ''; clienteEncontrado.value = null; clienteNoEncontrado.value = false
  nuevoCliente.value = { nombre: '', telefono: '', email: '', cedula: '', direccion: '', referencia_nombre: '', referencia_telefono: '', referencia_parentesco: '' }
  montoTotalBS.value = ''; propuesta.value = null; cuotasSeleccionadas.value = null; descripcionManual.value = ''
  numeroFactura.value = ''; resultado.value = {}; requiereAprobacion.value = false; excedeLimite.value = false
  categoriaSeleccionada.value = null
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
.cliente-premium-card .card-glow { position: absolute; top: -50%; right: -50%; width: 100%; height: 100%; background: radial-gradient(ellipse, rgba(255,255,255,0.08), transparent 70%); pointer-events: none; }
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
.progress-text { position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%); font-size: 0.65rem; font-weight: 700; color: white; text-shadow: 0 1px 4px rgba(0,0,0,0.5); }
.financiamientos-header { padding: 4px 0; }
.financiamientos-grid { display: flex; flex-direction: column; gap: 8px; }
.financiamiento-item { padding: 12px 16px; border-radius: 12px; transition: all 0.3s ease; }
.financiamiento-item:hover { transform: translateX(4px); border-color: rgba(79,172,254,0.3); }
.tienda-chip { background: rgba(79,172,254,0.15) !important; color: #4facfe !important; }
.empty-state { padding: 24px; text-align: center; border: 1px dashed rgba(255,255,255,0.08); }
.btn-continuar { background: linear-gradient(135deg, #4facfe, #6366f1) !important; color: white !important; font-weight: 700 !important; font-size: 1.1rem !important; transition: all 0.3s ease !important; height: 56px !important; }
.btn-continuar:hover { transform: translateY(-2px); box-shadow: 0 8px 32px rgba(79,172,254,0.4) !important; }
.btn-registrar { background: linear-gradient(135deg, #4caf50, #2e7d32) !important; color: white !important; font-weight: 700 !important; transition: all 0.3s ease !important; }
.btn-registrar:hover { transform: translateY(-2px); box-shadow: 0 8px 32px rgba(76,175,80,0.4) !important; }
.custom-input :deep(.v-field) { background: rgba(255,255,255,0.05) !important; border-radius: 12px !important; border: 1px solid rgba(255,255,255,0.1) !important; }
.custom-input :deep(.v-field--focused) { border-color: #4facfe !important; box-shadow: 0 0 0 3px rgba(79,172,254,0.15) !important; }
.custom-input :deep(.v-label) { color: rgba(255,255,255,0.6) !important; }
.custom-input :deep(.v-field__input) { color: white !important; }
.custom-input :deep(.v-field__input::placeholder) { color: rgba(255,255,255,0.7) !important; font-weight: 500 !important; opacity: 1 !important; }
.categorias-grid { display: grid; grid-template-columns: repeat(5, 1fr); gap: 10px; }
.categoria-item { display: flex; flex-direction: column; align-items: center; justify-content: center; padding: 14px 8px; border-radius: 16px; cursor: pointer; transition: all 0.3s ease; min-height: 80px; }
.categoria-item:hover { transform: translateY(-4px); border-color: rgba(255,255,255,0.2) !important; }
.categoria-seleccionada { transform: translateY(-4px); box-shadow: 0 8px 24px rgba(0,0,0,0.3); }
.descripcion-auto { display: flex; align-items: center; padding: 12px 16px; border-radius: 10px; }
.fade-in { animation: fadeIn 0.5s ease; }
@keyframes fadeIn { from { opacity: 0; transform: translateY(20px); } to { opacity: 1; transform: translateY(0); } }
.slide-up { animation: slideUp 0.4s ease; }
@keyframes slideUp { from { opacity: 0; transform: translateY(30px); } to { opacity: 1; transform: translateY(0); } }
@media (max-width: 600px) { .header-premium { flex-direction: column; gap: 12px; align-items: stretch !important; } .disponible-number { font-size: 1.6rem; } .metric-item { align-items: center; } .metric-divider { display: none; } .cliente-premium-card .v-row { flex-direction: column !important; } .financiamiento-item { padding: 10px 12px; } .categorias-grid { grid-template-columns: repeat(3, 1fr); } }
</style>