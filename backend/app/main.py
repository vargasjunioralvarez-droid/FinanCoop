# backend/app/main.py
"""
🔒 FinanCash API - Configuración Principal con Seguridad Hardenizada
"""

import os
import logging
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from app.database import engine, Base, get_db
from app.models import NivelConfig, TasaDolar, ConfiguracionPago
from app.config import NIVELES_CONFIG_DEFAULT
from app.routers import (
    clientes_router, financiamientos_router, pagos_router, 
    config_router, app_mobile_router, admin_router, auth_router
)
from datetime import datetime, timezone

# ─────────────────────────────────────────────────────────────
# 📝 LOGGING SEGURO (sin exponer tokens ni contraseñas)
# ─────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s"
)
logger = logging.getLogger(__name__)

# ─────────────────────────────────────────────────────────────
# 🚀 FASTAPI CON SEGURIDAD
# ─────────────────────────────────────────────────────────────

# Detectar entorno
ENV = os.getenv("ENVIRONMENT", "development")
IS_PROD = ENV == "production"

app = FastAPI(
    title="FinanCash API",
    description="API segura para sistema de administración financiera",
    version="4.0.0",
    # 🚫 Deshabilitar docs en producción
    docs_url="/docs" if not IS_PROD else None,
    redoc_url="/redoc" if not IS_PROD else None,
    openapi_url="/openapi.json" if not IS_PROD else None,
    debug=False  # 🚫 NUNCA debug=True en producción
)

# ─────────────────────────────────────────────────────────────
# 🛡️ MIDDLEWARE: SECURITY HEADERS
# ─────────────────────────────────────────────────────────────

@app.middleware("http")
async def security_headers(request: Request, call_next):
    """Agrega headers de seguridad a TODAS las respuestas."""
    response = await call_next(request)

    # Prevenir que el navegador adivine el tipo de contenido
    response.headers["X-Content-Type-Options"] = "nosniff"

    # Prevenir clickjacking (tu sitio no puede ir en iframes)
    response.headers["X-Frame-Options"] = "DENY"

    # Protección básica XSS (legacy browsers)
    response.headers["X-XSS-Protection"] = "1; mode=block"

    # Controlar qué info se envía en Referer
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"

    # Restringir permisos del navegador
    response.headers["Permissions-Policy"] = (
        "geolocation=(), microphone=(), camera=(), "
        "payment=(), usb=(), magnetometer=(), gyroscope=()"
    )

    # Forzar HTTPS (HSTS) - solo en producción
    if IS_PROD:
        response.headers["Strict-Transport-Security"] = (
            "max-age=31536000; includeSubDomains; preload"
        )

    # Content Security Policy básico
    response.headers["Content-Security-Policy"] = (
        "default-src 'self'; "
        "script-src 'self'; "
        "style-src 'self' 'unsafe-inline'; "
        "img-src 'self' data: https:; "
        "font-src 'self'; "
        "connect-src 'self' https://financoop.onrender.com https://financash-frontend.onrender.com; "
        "frame-ancestors 'none'; "
        "base-uri 'self'; "
        "form-action 'self'"
    )

    return response

# ─────────────────────────────────────────────────────────────
# 🌐 MIDDLEWARE: CORS RESTRICTIVO
# ─────────────────────────────────────────────────────────────

# Orígenes permitidos (NUNCA usar "*" en producción)
# 🔥 FIX: Agregados orígenes de Capacitor para iOS y Android
ALLOWED_ORIGINS = [
    # Desarrollo local (Vite)
    "http://localhost:5173",
    "http://localhost:5174",
    "http://127.0.0.1:5173",
    "http://127.0.0.1:5174",
    # Capacitor / Ionic (iOS)
    "capacitor://localhost",
    "ionic://localhost",
    # Capacitor / Ionic (Android)
    "http://localhost",
    "https://localhost",
    # Producción
    "https://financash-frontend.onrender.com",
    "https://financash-backend.onrender.com",
    "https://financoop.onrender.com",
]

# 🔥 FIX: En producción, mantener orígenes de Capacitor + HTTPS
if IS_PROD:
    # Orígenes de Capacitor (siempre necesarios para la app móvil)
    capacitor_origins = [
        "capacitor://localhost",
        "ionic://localhost",
        "http://localhost",
        "https://localhost",
    ]
    # Orígenes HTTPS de producción
    https_origins = [o for o in ALLOWED_ORIGINS if o.startswith("https://")]
    # Combinar: HTTPS + Capacitor (la app móvil necesita estos incluso en prod)
    ALLOWED_ORIGINS = list(set(https_origins + capacitor_origins))
    logger.info(f"🔒 CORS en producción: {ALLOWED_ORIGINS}")

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,  # ✅ Necesario para cookies/auth headers
    allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "X-Request-ID"],
    max_age=600,  # Cache preflight 10 minutos
)

# ─────────────────────────────────────────────────────────────
# 🏠 MIDDLEWARE: TRUSTED HOST (previene Host Header Injection)
# ─────────────────────────────────────────────────────────────

if IS_PROD:
    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=[
            "financoop.onrender.com",
            "financash-backend.onrender.com",
            "financash-frontend.onrender.com",
            "localhost",  # solo para desarrollo local
        ]
    )

# ─────────────────────────────────────────────────────────────
# ❌ MANEJADOR GLOBAL DE ERRORES (sin leak de información)
# ─────────────────────────────────────────────────────────────

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """
    Captura TODOS los errores no manejados.
    NUNCA expone detalles internos al cliente.
    """
    request_id = request.headers.get("X-Request-ID", "unknown")

    # Loggear el error completo internamente (con traceback)
    logger.error(
        f"❌ [Error {request_id}] {type(exc).__name__}: {str(exc)}",
        exc_info=True
    )

    # Responder con mensaje genérico
    return JSONResponse(
        status_code=500,
        content={
            "detail": "Error interno del servidor",
            "request_id": request_id  # Para debugging interno
        }
    )

# ─────────────────────────────────────────────────────────────
# 🗄️ CREAR TABLAS
# ─────────────────────────────────────────────────────────────
Base.metadata.create_all(bind=engine)

# ─────────────────────────────────────────────────────────────
# 📊 INICIALIZAR DATOS POR DEFECTO
# ─────────────────────────────────────────────────────────────

def init_db():
    db = next(get_db())

    try:
        # Niveles de configuración
        for nivel_key, config in NIVELES_CONFIG_DEFAULT.items():
            existe = db.query(NivelConfig).filter(NivelConfig.nivel == nivel_key).first()
            if not existe:
                nc = NivelConfig(
                    nivel=nivel_key,
                    min_score=config["min_score"],
                    max_score=config["max_score"],
                    monto_max_usd=config["monto_max_usd"],
                    entrada_pct=config["entrada_pct"],
                    financia_pct=config["financia_pct"],
                    cuotas_base=config["cuotas_base"],
                    cuotas_max=config["cuotas_max"],
                    mora_diaria=config["mora_diaria"],
                    aprobacion_extra=config["aprobacion_extra"]
                )
                db.add(nc)
                logger.info(f"✅ Nivel creado: {nivel_key}")

        # Tasa del dólar por defecto
        tasa = db.query(TasaDolar).order_by(TasaDolar.id.desc()).first()
        if not tasa:
            tasa = TasaDolar(tasa=40.0, fuente="manual")
            db.add(tasa)
            logger.info("✅ Tasa dólar inicial creada: 40.0")

        # Configuración de pagos por defecto
        config_pago = db.query(ConfiguracionPago).first()
        if not config_pago:
            config_pago = ConfiguracionPago(
                banco_pago_movil="Banco de Venezuela",
                telefono_pago_movil="04121234567",
                cedula_pago_movil="V12345678",
                banco_transferencia="Banco Mercantil",
                cuenta_transferencia="01051234567890123456"
            )
            db.add(config_pago)
            logger.info("✅ Configuración de pagos inicial creada")

        db.commit()
        logger.info("🚀 Base de datos inicializada correctamente")

    except Exception as e:
        db.rollback()
        logger.error(f"❌ Error inicializando BD: {e}")
        raise
    finally:
        db.close()

# ─────────────────────────────────────────────────────────────
# 🔌 ROUTERS
# ─────────────────────────────────────────────────────────────

app.include_router(clientes_router)
app.include_router(financiamientos_router)
app.include_router(pagos_router)
app.include_router(config_router)
app.include_router(app_mobile_router)
app.include_router(admin_router)
app.include_router(auth_router)

# ─────────────────────────────────────────────────────────────
# 🚀 EVENTO STARTUP
# ─────────────────────────────────────────────────────────────

@app.on_event("startup")
def startup():
    logger.info(f"🚀 FinanCash API iniciando | Entorno: {ENV}")
    logger.info(f"🌐 CORS orígenes permitidos: {ALLOWED_ORIGINS}")
    init_db()

# ─────────────────────────────────────────────────────────────
# ▶️ EJECUCIÓN DIRECTA
# ─────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=port,
        reload=not IS_PROD,  # 🚫 Reload solo en desarrollo
        workers=1 if not IS_PROD else None
    )