import { createVuetify } from 'vuetify'
import * as components from 'vuetify/components'
import * as directives from 'vuetify/directives'
import 'vuetify/styles'

export default createVuetify({
  components,
  directives,
  theme: {
    defaultTheme: 'dark',  // ✅ CAMBIADO A DARK
    themes: {
      dark: {
        dark: true,
        colors: {
          background: '#0a0e1a',
          surface: '#1a1f35',
          primary: '#4facfe',
          secondary: '#6366f1',
          accent: '#FFD700',
          error: '#FF5252',
          info: '#4facfe',
          success: '#4CAF50',
          warning: '#FFC107'
        }
      },
      light: {
        dark: false,
        colors: {
          background: '#f5f5f5',
          surface: '#ffffff',
          primary: '#1976D2',
          secondary: '#424242',
          accent: '#82B1FF',
          error: '#FF5252',
          info: '#2196F3',
          success: '#4CAF50',
          warning: '#FFC107'
        }
      }
    }
  }
})