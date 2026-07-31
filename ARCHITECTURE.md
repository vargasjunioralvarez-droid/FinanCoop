# 🏗️ Arquitectura de FinanCoop

## 1. Visión General

FinanCoop es una plataforma de financiamiento cooperativo compuesta por tres componentes:

- **Backend**: API REST construida con FastAPI + SQLAlchemy + PostgreSQL.
- **Frontend Admin**: Panel de administración en Vue 3 + Vuetify.
- **App Móvil**: Aplicación para asociados en Vue 3 + Capacitor (Android).

El backend sigue una arquitectura de **tres capas** con separación de responsabilidades:
┌─────────────────────────────────────────────────────────┐
│ ROUTERS (Presentación) │
│ Reciben HTTP, validan con Pydantic, delegan en │
│ servicios de aplicación. │
└────────────────────────┬────────────────────────────────┘
│
┌────────────────────────▼────────────────────────────────┐
│ SERVICIOS (Aplicación) │
│ Orquestan la lógica de negocio. │
│ FinanciamientoService, PagoService, ClienteService │
└────────────────────────┬────────────────────────────────┘
│
┌────────────────────────▼────────────────────────────────┐
│ DOMINIO (Negocio) │
│ Reglas puras: scoring, niveles, conciliación. │
│ No depende de frameworks. │
└────────────────────────┬────────────────────────────────┘
│
┌────────────────────────▼────────────────────────────────┐
│ INFRAESTRUCTURA (Externos) │
│ Twilio, Cloudflare, PostgreSQL, Redis, BCV API. │
└─────────────────────────────────────────────────────────┘

text

## 2. Estructura del Proyecto
backend/
├── app/
│ ├── main.py # Punto de entrada, CORS, middlewares
│ ├── core/ # Configuración, seguridad, base de datos
│ │ ├── config.py # Variables de entorno y settings
│ │ ├── security.py # JWT, bcrypt, rate limiting, Redis
│ │ ├── database.py # SQLAlchemy engine y sesión
│ │ ├── audit.py # Decoradores de auditoría con hash encadenado
│ │ ├── backup.py # Backups cifrados con AES-256
│ │ ├── crypto.py # Cifrado de datos sensibles (PII)
│ │ └── scheduler.py # Programador de backups diarios
│ ├── modules/ # Módulos de dominio (routers + modelos)
│ │ ├── auth/ # Autenticación (login, refresh, logout)
│ │ ├── users/ # Clientes y administradores
│ │ ├── loans/ # Financiamientos y cuotas
│ │ ├── payments/ # Pagos y conciliación
│ │ ├── config/ # Tasas, niveles, métodos de pago
│ │ ├── admin/ # Dashboard y gestión de tiendas/usuarios
│ │ ├── audit/ # Consulta de logs de auditoría
│ │ ├── banks/ # Webhook bancario y conciliación manual
│ │ ├── mobile/ # Endpoints de la app móvil
│ │ └── uploads/ # Subida de comprobantes
│ ├── services/ # Capa de servicios de aplicación
│ │ ├── financiamiento_service.py
│ │ ├── pago_service.py
│ │ └── cliente_service.py
│ ├── domain/ # Lógica de negocio pura
│ │ ├── scoring.py # Cálculo de score crediticio
│ │ ├── niveles.py # Configuración de niveles
│ │ └── conciliacion.py # Procesamiento de conciliación
│ ├── infrastructure/ # Servicios externos
│ │ └── twilio.py # Envío de SMS y WhatsApp
│ └── shared/ # Utilidades compartidas
│ ├── utils.py # Funciones de acceso a datos
│ └── helpers.py # Utilidades puras (teléfono, PIN)
├── tests/ # Tests automatizados (pytest)
├── alembic/ # Migraciones de base de datos
└── requirements.txt

text

## 3. Base de Datos

### Tablas principales

| Tabla | Módulo | Descripción |
|---|---|---|
| `usuarios` | users | Administradores del panel (admin_central, admin_tienda, cajero) |
| `tiendas` | users | Cooperativas afiliadas |
| `clientes` | users | Asociados con scoring crediticio |
| `financiamientos` | loans | Créditos otorgados |
| `cuotas` | loans | Cuotas de cada financiamiento |
| `pagos` | payments | Pagos reportados por asociados |
| `configuracion_pago` | payments | Datos bancarios para recibir pagos |
| `tasa_dolar` | config | Historial de tasa de cambio |
| `niveles_config` | config | Configuración de niveles de scoring |
| `auditoria` | audit | Registro inmutable de todas las acciones |
| `token_blacklist` | auth | Tokens JWT revocados |

### Roles de acceso

| Rol | Permisos |
|---|---|
| `admin_central` | Acceso total. Gestiona tiendas, usuarios, configuración. |
| `admin_tienda` | Solo ve datos de su tienda. Puede conciliar pagos. |
| `cajero` | Solo ve datos de su tienda. Crea financiamientos y registra pagos. |
| `cliente` | Solo ve sus propios datos. Reporta pagos desde la app móvil. |

## 4. Seguridad

### Autenticación
- **JWT** con refresh tokens, blacklist y claims estándar (`aud`, `iss`, `jti`).
- Contraseñas con **bcrypt** (12 rondas) y comparación de tiempo constante.
- PIN de cliente con **bcrypt** (12 rondas).
- **Rate limiting** en endpoints de login (Redis + fallback en memoria).

### Protección de datos
- **Datos sensibles cifrados** (cédula, teléfono, email, dirección) con AES-256 (Fernet).
- Búsqueda de clientes por **hash de cédula** (SHA-256) en lugar de texto plano.
- **Backups cifrados** con AES-256 antes de almacenar en disco.
- **Auditoría inmutable** con hash encadenado (SHA-256).

### Endpoints protegidos
- **CORS** restringido a orígenes específicos.
- **Cabeceras de seguridad HTTP** (HSTS, X-Frame-Options, etc.).
- **Validación automática** con schemas Pydantic en todos los endpoints.

## 5. Flujo de un Crédito
Cajero crea cliente (POST /clientes)

Admin central aprueba cliente (POST /clientes/aprobar)

Cajero crea financiamiento (POST /financiamientos)
→ Validaciones: nivel, score, cuotas vencidas, límite disponible
→ Se generan cuotas automáticamente (cada 15 días)

Cliente reporta pago (POST /pagos/reportar)
→ La cuota pasa a estado "conciliando"

Admin concilia pago (POST /pagos/conciliar)
→ Cuota pasa a "pagada"
→ Si es la última cuota, el financiamiento se completa
→ El score del cliente se actualiza automáticamente

text

## 6. Variables de Entorno Requeridas

| Variable | Descripción |
|---|---|
| `JWT_SECRET_KEY` | Clave de firma de tokens JWT |
| `DATABASE_URL` | URL de conexión a PostgreSQL |
| `DATA_ENCRYPTION_KEY` | Clave Fernet para cifrar datos sensibles |
| `BACKUP_ENCRYPTION_KEY` | Clave Fernet para cifrar backups |
| `BANCO_WEBHOOK_SECRET` | Token compartido para el webhook bancario |
| `REDIS_URL` | URL de conexión a Redis (rate limiting) |
| `TWILIO_ACCOUNT_SID` | Credenciales de Twilio (SMS/WhatsApp) |
| `TWILIO_AUTH_TOKEN` | Credenciales de Twilio |
| `TWILIO_SMS_FROM` | Número Twilio para envío de SMS |
| `CLOUDFLARE_ACCOUNT_ID` | ID de cuenta de Cloudflare Images |
| `CLOUDFLARE_API_TOKEN` | Token de API de Cloudflare Images |

## 7. Tests Automatizados

La suite de tests cubre los flujos críticos del sistema usando **pytest** + **SQLite en memoria**:

- **Autenticación**: login exitoso, credenciales incorrectas, usuario inactivo, token válido.
- **Clientes**: creación exitosa, cédula duplicada.
- **Financiamientos**: creación exitosa, sin autenticación, cliente no aprobado.
- **Pagos**: reporte exitoso, sin autenticación, cuota ya pagada, conciliación, pago en efectivo.
