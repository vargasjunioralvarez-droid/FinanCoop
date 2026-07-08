import { createRouter, createWebHistory } from 'vue-router'
import Dashboard from './views/Dashboard.vue'
import CajeroView from './views/CajeroView.vue'
import Clientes from './views/Clientes.vue'
import Financiamientos from './views/Financiamientos.vue'
import Cuotas from './views/Cuotas.vue'
import ConciliacionView from './views/ConciliacionView.vue'
import ConfiguracionView from './views/ConfiguracionView.vue'
import NivelesView from './views/NivelesView.vue'  // ← NUEVO

const routes = [
  { path: '/', component: Dashboard },
  { path: '/cajero', component: CajeroView },
  { path: '/clientes', component: Clientes },
  { path: '/financiamientos', component: Financiamientos },
  { path: '/cuotas/:id', component: Cuotas, props: true },
  { path: '/conciliacion', component: ConciliacionView },
  { path: '/configuracion', component: ConfiguracionView },
  { path: '/niveles', component: NivelesView }  // ← NUEVO
]

export default createRouter({
  history: createWebHistory(),
  routes
})