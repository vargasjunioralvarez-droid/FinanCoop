<template>
  <v-container class="pa-4">
    <v-row>
      <v-col cols="12">
        <!-- ✅ HEADER MEJORADO -->
        <div class="d-flex align-center justify-space-between flex-wrap mb-4">
          <div>
            <h1 class="text-h4 font-weight-bold">
              <v-icon color="primary" size="36" class="mr-2">mdi-cart-plus</v-icon>
              Nueva Venta
            </h1>
            <p class="text-subtitle-1 text-grey">Registra un nuevo financiamiento</p>
          </div>
          <v-chip color="primary" size="large" class="font-weight-bold">
            <v-icon start>mdi-currency-usd</v-icon>
            Tasa: {{ tasaDolar }} BS/$
          </v-chip>
        </div>
      </v-col>

      <!-- PASO 1: Cliente -->
      <v-col cols="12" v-if="paso === 1">
        <v-card class="rounded-xl" elevation="2">
          <v-card-title class="text-h5 pa-4 bg-primary-lighten-5">
            <v-icon start color="primary">mdi-account-search</v-icon>
            1. Identificar Cliente
          </v-card-title>
          
          <v-card-text class="pa-4">
            <v-text-field
              v-model="busquedaCedula"
              label="Cédula del Cliente"
              @keyup.enter="buscarCliente"
              append-inner-icon="mdi-magnify"
              @click:append-inner="buscarCliente"
              variant="outlined"
              density="comfortable"
              placeholder="Ej: 12345678"
              :loading="cargando"
              clearable
            >
              <template v-slot:prepend-inner>
                <v-icon color="grey">mdi-card-account-details</v-icon>
              </template>
            </v-text-field>
            
            <!-- ✅ CLIENTE ENCONTRADO - VERSIÓN MEJORADA -->
            <div v-if="clienteEncontrado" class="mt-4">
              <!-- Tarjeta principal del cliente -->
              <v-card class="rounded-xl" :class="`nivel-${clienteEncontrado.nivel}`" elevation="2">
                <v-card-text class="pa-4">
                  <v-row>
                    <v-col cols="12" md="8">
                      <div class="d-flex align-center flex-wrap">
                        <v-avatar size="56" :color="nivelColor(clienteEncontrado.nivel)" class="mr-3">
                          <v-icon size="28" color="white">{{ nivelIcono(clienteEncontrado.nivel) }}</v-icon>
                        </v-avatar>
                        <div>
                          <h2 class="text-h5 font-weight-bold text-white">
                            {{ clienteEncontrado.nombre }}
                          </h2>
                          <div class="d-flex align-center flex-wrap mt-1">
                            <v-chip size="small" :color="nivelColor(clienteEncontrado.nivel)" text-color="white" class="font-weight-bold">
                              <v-icon start size="14">{{ nivelIcono(clienteEncontrado.nivel) }}</v-icon>
                              {{ clienteEncontrado.nivel.toUpperCase() }}
                            </v-chip>
                            <span class="text-white ml-2 text-caption" style="opacity: 0.9;">
                              <v-icon size="14" color="white" class="mr-1">mdi-star</v-icon>
                              Score: {{ clienteEncontrado.score }} pts
                            </span>
                            <v-chip size="x-small" :color="clienteEncontrado.estado === 'aprobado' ? 'success' : 'warning'" class="ml-2">
                              {{ clienteEncontrado.estado }}
                            </v-chip>
                          </div>
                        </div>
                      </div>
                      
                      <div class="d-flex flex-wrap mt-3" style="gap: 16px;">
                        <div class="d-flex align-center">
                          <v-icon size="18" color="white" class="mr-1">mdi-phone</v-icon>
                          <span class="text-white" style="opacity: 0.9;">{{ clienteEncontrado.telefono }}</span>
                        </div>
                        <div class="d-flex align-center" v-if="clienteEncontrado.email">
                          <v-icon size="18" color="white" class="mr-1">mdi-email</v-icon>
                          <span class="text-white" style="opacity: 0.9;">{{ clienteEncontrado.email }}</span>
                        </div>
                        <div class="d-flex align-center" v-if="clienteEncontrado.direccion">
                          <v-icon size="18" color="white" class="mr-1">mdi-map-marker</v-icon>
                          <span class="text-white" style="opacity: 0.9;">{{ clienteEncontrado.direccion }}</span>
                        </div>
                      </div>
                    </v-col>
                    
                    <v-col cols="12" md="4" class="d-flex align-center justify-md-end">
                      <div class="text-center">
                        <div class="text-h3 font-weight-bold text-white">
                          ${{ formatearNumero(clienteEncontrado.limite_disponible?.disponible_usd || 0) }}
                        </div>
                        <div class="text-caption text-white" style="opacity: 0.8;">Disponible</div>
                      </div>
                    </v-col>
                  </v-row>
                </v-card-text>
              </v-card>
              
              <!-- ✅ LÍMITE Y DISPONIBLE - BARRAS DE PROGRESO -->
              <v-card class="rounded-xl mt-3" elevation="1">
                <v-card-text class="pa-3">
                  <div class="d-flex justify-space-between align-center mb-1">
                    <span class="text-caption font-weight-medium">Límite: <strong>${{ clienteEncontrado.limite_disponible?.limite_usd || 0 }}</strong></span>
                    <span class="text-caption font-weight-medium">Usado: <strong class="text-error">${{ clienteEncontrado.limite_disponible?.usado_usd || 0 }}</strong></span>
                    <span class="text-caption font-weight-medium">Disponible: <strong class="text-success">${{ clienteEncontrado.limite_disponible?.disponible_usd || 0 }}</strong></span>
                  </div>
                  
                  <v-progress-linear
                    :model-value="(clienteEncontrado.limite_disponible?.usado_usd / clienteEncontrado.limite_disponible?.limite_usd) * 100 || 0"
                    :color="porcentajeUsado > 80 ? 'error' : porcentajeUsado > 50 ? 'warning' : 'success'"
                    height="8"
                    rounded
                    class="mt-1"
                  >
                    <template v-slot:default="{ value }">
                      <span class="text-caption font-weight-bold" style="color: white; text-shadow: 0 1px 2px rgba(0,0,0,0.5);">
                        {{ Math.round(value) }}% usado
                      </span>
                    </template>
                  </v-progress-linear>
                  
                  <div class="d-flex justify-space-between mt-1">
                    <span class="text-caption text-grey">0%</span>
                    <span class="text-caption text-grey">100%</span>
                  </div>
                </v-card-text>
              </v-card>
              
              <!-- ✅ FINANCIAMIENTOS ACTIVOS - MEJORADO -->
              <div v-if="clienteEncontrado.financiamientos_activos && clienteEncontrado.financiamientos_activos.length > 0" class="mt-3">
                <v-card class="rounded-xl" elevation="1">
                  <v-card-text class="pa-3">
                    <div class="d-flex align-center mb-2">
                      <v-icon color="warning" class="mr-2">mdi-clock-outline</v-icon>
                      <h4 class="text-subtitle-1 font-weight-bold">Compras Activas</h4>
                      <v-chip size="small" color="warning" class="ml-2">{{ clienteEncontrado.financiamientos_activos.length }}</v-chip>
                    </div>
                    
                    <v-table density="compact" class="rounded-lg">
                      <thead>
                        <tr>
                          <th class="text-left">Tienda</th>
                          <th class="text-right">Monto</th>
                          <th class="text-center">Cuotas</th>
                          <th class="text-center">Estado</th>
                        </tr>
                      </thead>
                      <tbody>
                        <tr v-for="fin in clienteEncontrado.financiamientos_activos" :key="fin.id">
                          <td>
                            <v-chip size="small" color="info" variant="flat">
                              <v-icon start size="12">mdi-store</v-icon>
                              {{ fin.tienda_nombre || 'N/A' }}
                            </v-chip>
                          </td>
                          <td class="text-right font-weight-medium">
                            ${{ formatearNumero(fin.monto_total_usd) }}
                            <span class="text-caption text-grey">(BS {{ formatearNumero(fin.monto_total_bs) }})</span>
                          </td>
                          <td class="text-center">
                            <v-chip size="x-small" :color="fin.cuotas_pagadas === fin.cuotas_aprobadas ? 'success' : 'primary'" variant="tonal">
                              {{ fin.cuotas_pagadas || 0 }}/{{ fin.cuotas_aprobadas }}
                            </v-chip>
                          </td>
                          <td class="text-center">
                            <v-chip size="x-small" :color="fin.estado === 'activo' ? 'success' : 'warning'" variant="flat">
                              {{ fin.estado }}
                            </v-chip>
                          </td>
                        </tr>
                      </tbody>
                    </v-table>
                    
                    <!-- Resumen de deuda por tienda -->
                    <div class="mt-2" v-if="Object.keys(clienteEncontrado.deuda_por_tienda || {}).length > 0">
                      <span class="text-caption text-grey font-weight-medium">Deuda por tienda:</span>
                      <div class="d-flex flex-wrap mt-1" style="gap: 8px;">
                        <v-chip v-for="(deuda, tienda) in clienteEncontrado.deuda_por_tienda" :key="tienda" size="small" color="error" variant="tonal">
                          {{ tienda }}: ${{ formatearNumero(deuda.monto_usd) }} ({{ deuda.cuotas_restantes }} cuotas)
                        </v-chip>
                      </div>
                    </div>
                  </v-card-text>
                </v-card>
              </div>
              <div v-else class="mt-3">
                <v-card class="rounded-xl" elevation="1" color="grey-lighten-4">
                  <v-card-text class="pa-3 text-center">
                    <v-icon color="success" size="24" class="mb-1">mdi-check-circle</v-icon>
                    <div class="text-caption text-grey">No tiene compras activas</div>
                  </v-card-text>
                </v-card>
              </div>
              
              <!-- Botones de acción -->
              <div class="mt-4">
                <v-btn 
                  v-if="clienteEncontrado.limite_disponible?.puede_comprar" 
                  color="primary" 
                  @click="paso = 2" 
                  size="large"
                  block
                  elevation="2"
                  class="rounded-xl"
                >
                  <v-icon start>mdi-arrow-right</v-icon>
                  Continuar con la venta
                </v-btn>
                
                <v-alert 
                  v-else 
                  type="error" 
                  variant="tonal" 
                  class="rounded-xl"
                  border="start"
                >
                  <div class="d-flex align-center">
                    <v-icon color="error" size="28" class="mr-2">mdi-alert-circle</v-icon>
                    <div>
                      <strong>Cliente sin saldo disponible</strong>
                      <div class="text-caption">Ha alcanzado el límite máximo de crédito</div>
                    </div>
                  </div>
                </v-alert>
              </div>
            </div>
            
            <!-- ✅ REGISTRO DE NUEVO CLIENTE - MEJORADO -->
            <div v-if="clienteNoEncontrado" class="mt-4">
              <v-card class="rounded-xl" color="warning-lighten-5" elevation="1">
                <v-card-text class="pa-4">
                  <div class="d-flex align-center mb-3">
                    <v-icon color="warning" size="28" class="mr-2">mdi-account-plus</v-icon>
                    <h3 class="text-h6 font-weight-bold">Registrar Nuevo Cliente</h3>
                  </div>
                  
                  <v-row>
                    <v-col cols="12" md="6">
                      <v-text-field 
                        v-model="nuevoCliente.nombre" 
                        label="Nombre completo *" 
                        variant="outlined" 
                        density="comfortable" 
                        required 
                        prepend-inner-icon="mdi-account"
                      />
                    </v-col>
                    <v-col cols="12" md="6">
                      <v-text-field 
                        v-model="nuevoCliente.telefono" 
                        label="Teléfono *" 
                        variant="outlined" 
                        density="comfortable" 
                        required 
                        prepend-inner-icon="mdi-phone"
                      />
                    </v-col>
                    <v-col cols="12" md="6">
                      <v-text-field 
                        v-model="nuevoCliente.email" 
                        label="Email *" 
                        variant="outlined" 
                        density="comfortable" 
                        required 
                        prepend-inner-icon="mdi-email"
                      />
                    </v-col>
                    <v-col cols="12" md="6">
                      <v-textarea 
                        v-model="nuevoCliente.direccion" 
                        label="Dirección completa *" 
                        rows="1"
                        variant="outlined" 
                        density="comfortable" 
                        required 
                        prepend-inner-icon="mdi-map-marker"
                      />
                    </v-col>
                  </v-row>
                  
                  <v-divider class="my-3"></v-divider>
                  
                  <h4 class="text-subtitle-2 font-weight-bold mb-2">
                    <v-icon size="18" class="mr-1">mdi-account-group</v-icon>
                    Referencia personal (obligatorio)
                  </h4>
                  
                  <v-row>
                    <v-col cols="12" md="4">
                      <v-text-field 
                        v-model="nuevoCliente.referencia_nombre" 
                        label="Nombre de referencia *" 
                        variant="outlined" 
                        density="comfortable" 
                        required 
                        prepend-inner-icon="mdi-account"
                      />
                    </v-col>
                    <v-col cols="12" md="4">
                      <v-text-field 
                        v-model="nuevoCliente.referencia_telefono" 
                        label="Teléfono de referencia *" 
                        variant="outlined" 
                        density="comfortable" 
                        required 
                        prepend-inner-icon="mdi-phone"
                      />
                    </v-col>
                    <v-col cols="12" md="4">
                      <v-select 
                        v-model="nuevoCliente.referencia_parentesco" 
                        :items="['Vecino', 'Familiar', 'Jefe de trabajo', 'Amigo', 'Otro']" 
                        label="Parentesco/Relación *" 
                        variant="outlined" 
                        density="comfortable" 
                        required 
                      />
                    </v-col>
                  </v-row>
                  
                  <v-btn 
                    color="success" 
                    @click="registrarCliente" 
                    block 
                    size="large"
                    :disabled="!registroValido"
                    elevation="2"
                    class="rounded-xl mt-2"
                  >
                    <v-icon start>mdi-account-plus</v-icon>
                    Registrar Cliente
                  </v-btn>
                </v-card-text>
              </v-card>
            </div>
          </v-card-text>
        </v-card>
      </v-col>
      
      <!-- PASO 2: Monto en BS (Misma lógica pero con mejor diseño) -->
      <v-col cols="12" v-if="paso === 2">
        <v-card class="rounded-xl" elevation="2">
          <v-card-title class="text-h5 pa-4 bg-primary-lighten-5">
            <v-icon start color="primary">mdi-currency-brl</v-icon>
            2. Monto de la Compra
          </v-card-title>
          
          <v-card-text class="pa-4">
            <!-- Resumen cliente -->
            <v-card class="rounded-xl mb-4" color="info-lighten-5" variant="tonal">
              <v-card-text class="pa-3">
                <div class="d-flex justify-space-between flex-wrap" style="gap: 8px;">
                  <div><strong>Cliente:</strong> {{ clienteEncontrado?.nombre }}</div>
                  <v-chip :color="nivelColor(clienteEncontrado?.nivel)" text-color="white" size="small">
                    {{ clienteEncontrado?.nivel?.toUpperCase() }}
                  </v-chip>
                  <div><strong>Disponible:</strong> <span class="text-success">${{ clienteEncontrado?.limite_disponible?.disponible_usd || 0 }}</span></div>
                  <div><strong>Límite:</strong> ${{ clienteEncontrado?.limite_disponible?.limite_usd || 0 }}</div>
                </div>
              </v-card-text>
            </v-card>
            
            <v-text-field
              v-model="montoTotalBS"
              label="Monto Total en Bolívares"
              type="number"
              prefix="BS"
              @input="calcularPropuesta"
              variant="outlined"
              density="comfortable"
              hint="Ingrese el monto en Bolívares"
              persistent-hint
              prepend-inner-icon="mdi-currency-brl"
            ></v-text-field>
            
            <div class="text-caption mb-2" v-if="tasaDolar && montoTotalBS">
              <v-icon color="info" size="small">mdi-information</v-icon>
              Equivalente: ~${{ (parseFloat(montoTotalBS) / tasaDolar).toFixed(2) }} USD (referencia)
            </div>

            <v-alert v-if="excedeLimite" type="error" class="mt-3 rounded-xl" border="start" prominent>
              <v-icon start>mdi-cancel</v-icon>
              <strong>Monto excede el límite disponible</strong>
              <div class="text-caption mt-1">
                Límite disponible: <strong>${{ clienteEncontrado?.limite_disponible?.disponible_usd || 0 }} USD</strong> | 
                Solicitado: <strong>~${{ ((parseFloat(montoTotalBS) || 0) / (tasaDolar || 40)).toFixed(2) }} USD</strong>
              </div>
            </v-alert>
            
            <v-alert v-if="propuesta && !excedeLimite" type="info" class="mt-3 rounded-xl" border="start">
              <h3 class="text-h6 mb-2">📋 Propuesta de Financiamiento</h3>
              <v-divider class="my-2"></v-divider>
              
              <v-row>
                <v-col cols="12" md="6">
                  <div class="d-flex justify-space-between pa-2 rounded-lg" style="background: rgba(0,0,0,0.03);">
                    <span>Monto Total:</span>
                    <strong>BS {{ formatearNumero(propuesta.propuesta?.monto_solicitado_bs || propuesta.monto_total_bs) }}</strong>
                  </div>
                  <div class="d-flex justify-space-between pa-2 mt-1">
                    <span>Monto en USD:</span>
                    <strong>${{ formatearNumero(propuesta.propuesta?.monto_solicitado_usd || propuesta.monto_total_usd) }}</strong>
                  </div>
                </v-col>
                <v-col cols="12" md="6">
                  <div class="d-flex justify-space-between pa-2 rounded-lg" style="background: rgba(255,87,34,0.08);">
                    <span>💳 Entrada HOY ({{ propuesta.propuesta?.entrada_pct || propuesta.entrada_pct }}%):</span>
                    <strong class="text-error">BS {{ formatearNumero(propuesta.propuesta?.entrada_bs || propuesta.monto_entrada_bs) }}</strong>
                  </div>
                  <div class="d-flex justify-space-between pa-2 mt-1" style="background: rgba(76,175,80,0.08);">
                    <span>📊 A financiar ({{ propuesta.propuesta?.financia_pct || propuesta.financia_pct }}%):</span>
                    <strong class="text-success">BS {{ formatearNumero(propuesta.propuesta?.financia_bs || propuesta.monto_financia_bs) }}</strong>
                  </div>
                </v-col>
              </v-row>
              
              <div class="d-flex justify-space-between pa-2 mt-2 rounded-lg" style="background: rgba(33,150,243,0.08);">
                <span>💰 Disponible después:</span>
                <strong class="text-primary">${{ formatearNumero(clienteEncontrado?.limite_disponible?.disponible_usd - (propuesta.propuesta?.monto_solicitado_usd || 0)) }}</strong>
              </div>
            </v-alert>
            
            <div v-if="propuesta && !excedeLimite" class="mt-3">
              <label class="text-subtitle-2 font-weight-bold">Seleccionar cuotas:</label>
              <v-radio-group v-model="cuotasSeleccionadas" class="mt-2">
                <v-radio v-for="cuota in opcionesCuotas" :key="cuota.value" :value="cuota.value">
                  <template v-slot:label>
                    <div>
                      <strong>{{ cuota.value }} cuotas</strong>
                      <span class="text-caption ml-2">
                        BS {{ formatearNumero(cuota.monto) }} cada una
                        <span class="text-grey">(${{ formatearNumero(cuota.monto_usd) }} ref.)</span>
                      </span>
                    </div>
                  </template>
                </v-radio>
              </v-radio-group>
              
              <v-alert v-if="requiereAprobacion" type="warning" class="mt-2 rounded-xl" border="start">
                ⚠️ Requiere aprobación del establecimiento para {{ cuotasSeleccionadas }} cuotas
              </v-alert>
            </div>
            
            <div class="d-flex mt-4" style="gap: 8px;">
              <v-btn @click="paso = 1" variant="text" color="grey">
                <v-icon start>mdi-arrow-left</v-icon> Volver
              </v-btn>
              <v-btn 
                v-if="cuotasSeleccionadas && !excedeLimite" 
                color="success" 
                @click="paso = 3" 
                class="flex-grow-1"
                size="large"
                elevation="2"
                rounded="xl"
              >
                Confirmar Propuesta <v-icon end>mdi-arrow-right</v-icon>
              </v-btn>
            </div>
          </v-card-text>
        </v-card>
      </v-col>
      
      <!-- PASO 3: Confirmar -->
      <v-col cols="12" v-if="paso === 3">
        <v-card class="rounded-xl" elevation="2">
          <v-card-title class="text-h5 pa-4 bg-warning-lighten-5">
            <v-icon start color="warning">mdi-check-circle</v-icon>
            3. Confirmar Venta
          </v-card-title>
          
          <v-card-text class="pa-4">
            <v-card class="rounded-xl mb-3" color="warning-lighten-5" variant="tonal">
              <v-card-text>
                <h3 class="text-h6 mb-2">📋 Resumen de la Venta</h3>
                <v-divider class="my-2"></v-divider>
                <v-row>
                  <v-col cols="12" md="6">
                    <p><strong>Cliente:</strong> {{ clienteEncontrado?.nombre }}</p>
                    <p><strong>Teléfono:</strong> {{ clienteEncontrado?.telefono }}</p>
                    <p><strong>Dirección:</strong> {{ clienteEncontrado?.direccion }}</p>
                  </v-col>
                  <v-col cols="12" md="6">
                    <p><strong>Monto Total:</strong> BS {{ formatearNumero(montoTotalBS) }}</p>
                    <p class="text-error"><strong>💳 Entrada HOY:</strong> BS {{ formatearNumero(propuesta?.propuesta?.entrada_bs || propuesta?.monto_entrada_bs) }}</p>
                    <p class="text-success"><strong>📊 Financia:</strong> BS {{ formatearNumero(propuesta?.propuesta?.financia_bs || propuesta?.monto_financia_bs) }}</p>
                  </v-col>
                </v-row>
                <v-divider class="my-2"></v-divider>
                <v-row>
                  <v-col cols="12" md="4">
                    <p><strong>Cuotas:</strong> {{ cuotasSeleccionadas }} quincenales</p>
                  </v-col>
                  <v-col cols="12" md="4">
                    <p><strong>Monto cuota:</strong> BS {{ formatearNumero(montoCuotaSeleccionada) }}</p>
                  </v-col>
                  <v-col cols="12" md="4">
                    <p><strong>Total a pagar:</strong> BS {{ formatearNumero(parseFloat(montoTotalBS)) }}</p>
                  </v-col>
                </v-row>
              </v-card-text>
            </v-card>
            
            <v-text-field 
              v-model="descripcion" 
              label="Descripción de la compra" 
              placeholder="Ej: iPhone 15, Consulta Dental, etc." 
              variant="outlined" 
              density="comfortable"
              prepend-inner-icon="mdi-clipboard-text"
            />
            
            <div class="d-flex mt-4" style="gap: 8px;">
              <v-btn @click="paso = 2" variant="text" color="grey">
                <v-icon start>mdi-arrow-left</v-icon> Volver
              </v-btn>
              <v-btn 
                color="success" 
                @click="crearFinanciamiento" 
                class="flex-grow-1"
                size="large"
                elevation="2"
                rounded="xl"
              >
                <v-icon start>mdi-cash-check</v-icon> Cobrar Entrada y Crear Financiamiento
              </v-btn>
            </div>
          </v-card-text>
        </v-card>
      </v-col>
      
      <!-- PASO 4: Éxito -->
      <v-col cols="12" v-if="paso === 4">
        <v-card class="rounded-xl" color="success" dark elevation="4">
          <v-card-text class="pa-6 text-center">
            <v-icon size="80" color="white" class="mb-3">mdi-check-circle-outline</v-icon>
            <h2 class="text-h3 font-weight-bold">✅ Financiamiento Creado</h2>
            <h3 class="text-h5 mt-2">{{ resultado?.financiamiento?.codigo }}</h3>
            <p class="text-body-1 mt-2">{{ resultado?.mensaje }}</p>
            <p class="text-caption mt-1">Tasa aplicada: {{ resultado?.financiamiento?.tasa_aplicada }} BS/$</p>
            
            <v-divider class="my-4" style="border-color: rgba(255,255,255,0.2);"></v-divider>
            
            <h4 class="mb-2">📅 Cuotas Generadas ({{ cuotasSeleccionadas }})</h4>
            <v-list bg-color="transparent" class="text-white">
              <v-list-item v-for="n in cuotasSeleccionadas" :key="n" class="border-bottom" style="border-color: rgba(255,255,255,0.1);">
                <v-list-item-title class="font-weight-bold text-white">Cuota #{{ n }}</v-list-item-title>
                <v-list-item-subtitle class="text-white" style="opacity: 0.8;">
                  Vence: {{ fechaCuota(n) }} | Monto: BS {{ formatearNumero(resultado?.financiamiento?.monto_cuota_bs) }}
                </v-list-item-subtitle>
              </v-list-item>
            </v-list>
            
            <v-btn 
              color="white" 
              @click="resetear" 
              block 
              class="mt-4 text-success font-weight-bold"
              size="large"
              rounded="xl"
              elevation="2"
            >
              <v-icon start>mdi-plus</v-icon> Nueva Venta
            </v-btn>
          </v-card-text>
        </v-card>
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
const nuevoCliente = ref({ 
  nombre: '', telefono: '', email: '', cedula: '', 
  direccion: '', referencia_nombre: '', referencia_telefono: '', 
  referencia_parentesco: '' 
})
const montoTotalBS = ref('')
const propuesta = ref(null)
const cuotasSeleccionadas = ref(null)
const descripcion = ref('')
const resultado = ref({})
const tasaDolar = ref(40.0)
const requiereAprobacion = ref(false)
const excedeLimite = ref(false)
const cargando = ref(false)

// ✅ COLORES Y ICONOS PARA NIVELES - MÁS VISIBLES
const nivelColor = (nivel) => {
  const colores = { 
    nuevo: 'grey darken-2', 
    bronce: 'brown darken-2', 
    plata: 'blue-grey darken-2', 
    oro: 'amber darken-2', 
    platino: 'deep-purple darken-2',
    diamante: 'cyan darken-3',
    elite: 'red darken-3'
  }
  return colores[nivel] || 'grey'
}

const nivelIcono = (nivel) => {
  const iconos = { 
    nuevo: 'mdi-star-outline', 
    bronce: 'mdi-medal-outline', 
    plata: 'mdi-silverware', 
    oro: 'mdi-gold', 
    platino: 'mdi-diamond-stone',
    diamante: 'mdi-crown',
    elite: 'mdi-crown-outline'
  }
  return iconos[nivel] || 'mdi-star'
}

const porcentajeUsado = computed(() => {
  if (!clienteEncontrado.value) return 0
  const limite = clienteEncontrado.value.limite_disponible?.limite_usd || 0
  const usado = clienteEncontrado.value.limite_disponible?.usado_usd || 0
  return limite > 0 ? (usado / limite) * 100 : 0
})

const opcionesCuotas = computed(() => {
  if (!propuesta.value) return []
  const p = propuesta.value.propuesta || propuesta.value
  const config = propuesta.value.configuracion_nivel || {}
  const cuotasBase = p.cuotas_base || config.cuotas_base || 4
  const cuotasMax = p.cuotas_max || config.cuotas_max || 12
  const financiaBs = p.financia_bs || propuesta.value.monto_financia_bs || 0
  const opciones = []
  for (let i = cuotasBase; i <= cuotasMax; i++) {
    const montoCuota = financiaBs / i
    opciones.push({ 
      value: i, 
      monto: montoCuota, 
      monto_usd: montoCuota / (propuesta.value.tasa_dolar_actual || tasaDolar.value || 40) 
    })
  }
  return opciones
})

const montoCuotaSeleccionada = computed(() => {
  const opcion = opcionesCuotas.value.find(o => o.value === cuotasSeleccionadas.value)
  return opcion?.monto || 0
})

const registroValido = computed(() => {
  return nuevoCliente.value.nombre && nuevoCliente.value.telefono && nuevoCliente.value.email &&
         nuevoCliente.value.direccion && nuevoCliente.value.referencia_nombre &&
         nuevoCliente.value.referencia_telefono && nuevoCliente.value.referencia_parentesco
})

const formatearNumero = (num) => num ? Number(num).toLocaleString('es-VE', { minimumFractionDigits: 2, maximumFractionDigits: 2 }) : '0,00'

onMounted(async () => {
  try { 
    const data = await api.get('/config/tasa-dolar')
    tasaDolar.value = data.tasa 
  } catch (e) {
    console.error('Error cargando tasa:', e)
  }
})

const buscarCliente = async () => {
  if (!busquedaCedula.value) return
  cargando.value = true
  try {
    const data = await api.get(`/clientes/buscar/${busquedaCedula.value}`)
    if (data.error || !data.encontrado) {
      clienteEncontrado.value = null
      clienteNoEncontrado.value = true
      nuevoCliente.value.cedula = busquedaCedula.value
    } else {
      // Obtener financiamientos activos del cliente
      const financiamientos = await api.get(`/financiamientos?cliente_id=${data.id}&estado=activo`)
      
      // Calcular deuda por tienda
      const deudaPorTienda = {}
      if (financiamientos.financiamientos) {
        financiamientos.financiamientos.forEach(fin => {
          const tienda = fin.tienda_nombre || 'Sin tienda'
          if (!deudaPorTienda[tienda]) {
            deudaPorTienda[tienda] = { monto_usd: 0, cuotas_restantes: 0 }
          }
          deudaPorTienda[tienda].monto_usd += fin.monto_total_usd
          deudaPorTienda[tienda].cuotas_restantes += fin.cuotas_aprobadas - (fin.cuotas_pagadas || 0)
        })
      }
      
      clienteEncontrado.value = { 
        ...data, 
        bloqueado: false,
        financiamientos_activos: financiamientos.financiamientos || [],
        deuda_por_tienda: deudaPorTienda
      }
      clienteNoEncontrado.value = false
    }
  } catch (e) {
    console.error('Error buscando cliente:', e)
    clienteEncontrado.value = null
    clienteNoEncontrado.value = true
    nuevoCliente.value.cedula = busquedaCedula.value
  } finally {
    cargando.value = false
  }
}

const registrarCliente = async () => {
  if (!registroValido.value) { 
    alert('Complete todos los campos obligatorios')
    return 
  }
  try {
    await api.post('/clientes', { 
      nombre: nuevoCliente.value.nombre, 
      cedula: busquedaCedula.value, 
      telefono: nuevoCliente.value.telefono, 
      email: nuevoCliente.value.email || '', 
      direccion: nuevoCliente.value.direccion, 
      referencia_nombre: nuevoCliente.value.referencia_nombre, 
      referencia_telefono: nuevoCliente.value.referencia_telefono, 
      referencia_parentesco: nuevoCliente.value.referencia_parentesco 
    })
    alert('✅ Cliente registrado exitosamente')
    await buscarCliente()
  } catch (e) { 
    console.error('Error registrando cliente:', e)
    alert('Error registrando cliente') 
  }
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
    propuesta.value = null
    cuotasSeleccionadas.value = null
    return
  }
  
  excedeLimite.value = false
  
  try {
    const data = await api.get(`/clientes/${clienteEncontrado.value.id}/nivel-propuesta?monto_total_bs=${montoTotalBS.value}`)
    propuesta.value = data
    cuotasSeleccionadas.value = data.propuesta?.cuotas_base || data.configuracion_nivel?.cuotas_base || 4
    requiereAprobacion.value = data.propuesta?.requiere_aprobacion_extra || false
  } catch (e) { 
    console.error('Error calculando propuesta:', e)
    propuesta.value = null 
  }
}

const fechaCuota = (n) => {
  const fecha = new Date()
  fecha.setDate(fecha.getDate() + (15 * n))
  return fecha.toLocaleDateString('es-VE')
}

const crearFinanciamiento = async () => {
  try {
    const data = await api.post('/financiamientos', { 
      cliente_id: clienteEncontrado.value.id, 
      descripcion: descripcion.value || 'Compra', 
      monto_total_bs: parseFloat(montoTotalBS.value), 
      cuotas_solicitadas: cuotasSeleccionadas.value 
    })
    if (data.error) { 
      alert('Error: ' + data.error)
      return 
    }
    resultado.value = data
    paso.value = 4
  } catch (e) { 
    console.error('Error creando financiamiento:', e)
    alert('Error creando financiamiento') 
  }
}

const resetear = () => {
  paso.value = 1
  busquedaCedula.value = ''
  clienteEncontrado.value = null
  clienteNoEncontrado.value = false
  nuevoCliente.value = { 
    nombre: '', telefono: '', email: '', cedula: '', 
    direccion: '', referencia_nombre: '', referencia_telefono: '', 
    referencia_parentesco: '' 
  }
  montoTotalBS.value = ''
  propuesta.value = null
  cuotasSeleccionadas.value = null
  descripcion.value = ''
  resultado.value = {}
  requiereAprobacion.value = false
  excedeLimite.value = false
}
</script>

<style scoped>
/* ✅ ESTILOS PARA TARJETAS DE NIVEL */
.nivel-nuevo { 
  background: linear-gradient(135deg, #78909C 0%, #546E7A 100%) !important;
}
.nivel-bronce { 
  background: linear-gradient(135deg, #A1887F 0%, #6D4C41 100%) !important;
}
.nivel-plata { 
  background: linear-gradient(135deg, #90A4AE 0%, #546E7A 100%) !important;
}
.nivel-oro { 
  background: linear-gradient(135deg, #FFD54F 0%, #F9A825 100%) !important;
}
.nivel-platino { 
  background: linear-gradient(135deg, #7E57C2 0%, #4A148C 100%) !important;
}
.nivel-diamante { 
  background: linear-gradient(135deg, #26C6DA 0%, #00695C 100%) !important;
}
.nivel-elite { 
  background: linear-gradient(135deg, #EF5350 0%, #B71C1C 100%) !important;
}

/* ✅ TARJETAS REDONDEADAS */
.rounded-xl {
  border-radius: 16px !important;
  overflow: hidden;
}

/* ✅ ESTILOS PARA TABLA */
.v-table {
  border-radius: 12px !important;
  overflow: hidden;
}

.v-table thead th {
  background: rgba(0, 0, 0, 0.03) !important;
  font-weight: 600 !important;
  font-size: 0.75rem !important;
  text-transform: uppercase !important;
  letter-spacing: 0.5px !important;
  color: rgba(0,0,0,0.6) !important;
}

/* ✅ ESTILOS PARA BOTONES */
.v-btn.rounded-xl {
  border-radius: 50px !important;
}

/* ✅ RESPONSIVE */
@media (max-width: 600px) {
  .v-table {
    font-size: 0.75rem !important;
  }
  .v-table th, 
  .v-table td {
    padding: 4px 6px !important;
  }
  .text-h4 {
    font-size: 1.5rem !important;
  }
  .text-h3 {
    font-size: 1.8rem !important;
  }
}
</style>