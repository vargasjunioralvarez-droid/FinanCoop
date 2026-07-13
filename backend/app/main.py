# backend/app/main.py
"""
🔒 FinanCash API - Configuración Principal con Seguridad Hardenizada
"""

import os
import logging
import re
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response
from app.database import engine, Base, get_db
from app.models import NivelConfig, TasaDolar, ConfiguracionPago
from app.config import NIVELES_CONFIG_DEFAULT
from app.routers import (
    clientes_router, financiamientos_router, pagos_router, 
    config_router, app_mobile_router, admin_router, auth_router
)
from datetime import datetime, timezone

# ─────────────────────────────────────────────────────────────
# 📝 LOGGING SEGURO
# ─────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s"
)
logger = logging.getLogger(__name__)

# ─────────────────────────────────────────────────────────────
# 🚀 FASTAPI
# ─────────────────────────────────────────────────────────────
ENV = os.getenv("ENVIRONMENT", "development")
IS_PROD = ENV == "production"

app = FastAPI(
    title="FinanCash API",
    description="API segura para sistema de administración financiera",
    version="4.0.0",
    docs_url="/docs" if not IS_PROD else None,
    redoc_url="/redoc" if not IS_PROD else None,
    openapi_url="/openapi.json" if not IS_PROD else None,
    debug=False
)

# ─────────────────────────────────────────────────────────────
# 🌐 CORS: Orígenes permitidos
# ─────────────────────────────────────────────────────────────
ALLOWED_ORIGINS = [
    "http://localhost:5173",
    "http://localhost:5174",
    "http://localhost:5175",
    "http://127.0.0.1:5173",
    "http://127.0.0.1:5174",
    "http://127.0.0.1:5175",
    "capacitor://localhost",
    "ionic://localhost",
    "http://localhost",
    "https://localhost",
    "https://financash-frontend.onrender.com",
    "https://financash-backend.onrender.com",
    "https://financoop.onrender.com",
    "null",
    "",  # Origen vacío
]

if IS_PROD:
    https_origins = [o for o in ALLOWED_ORIGINS if o.startswith("https://")]
    ALLOWED_ORIGINS = list(set(https_origins + [
        "capacitor://localhost",
        "ionic://localhost",
        "http://localhost",
        "https://localhost",
        "null",
        "",
    ]))
    logger.info(f"🔒 CORS en producción: {ALLOWED_ORIGINS}")

# ─────────────────────────────────────────────────────────────
# 🔥 MIDDLEWARE CORS CUSTOM - CRÍTICO PARA CAPACITOR
# ─────────────────────────────────────────────────────────────
class CustomCORSMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        origin = request.headers.get("origin", "")
        
        # 🔥 FIX: Capacitor en Android/iOS envía origin vacío o "null"
        # También acepta cualquier origen HTTPS en producción
        is_allowed = (
            origin in ALLOWED_ORIGINS or
            not origin or  # Vacío = Capacitor nativo
            origin == "null" or
            (IS_PROD and origin.startswith("https://")) or
            (not IS_PROD and "localhost" in origin)
        )
        
        # Responder a OPTIONS inmediatamente (preflight)
        if request.method == "OPTIONS":
            response = Response(status_code=200)
            response.headers["Access-Control-Allow-Origin"] = origin or "*"
            response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, PATCH, OPTIONS"
            response.headers["Access-Control-Allow-Headers"] = "Authorization, Content-Type, X-Request-ID, X-Requested-With, Accept, Origin"
            response.headers["Access-Control-Allow-Credentials"] = "true"
            response.headers["Access-Control-Max-Age"] = "86400"
            response.headers["Vary"] = "Origin"
            return response
        
        # Procesar request normal
        response = await call_next(request)
        
        if is_allowed:
            response.headers["Access-Control-Allow-Origin"] = origin or "*"
            response.headers["Access-Control-Allow-Credentials"] = "true"
            response.headers["Access-Control-Expose-Headers"] = "X-Request-ID"
            response.headers["Vary"] = "Origin"
        
        return response

# Aplicar el middleware custom PRIMERO (antes que cualquier otro)
app.add_middleware(CustomCORSMiddleware)

# ─────────────────────────────────────────────────────────────
# 🛡️ SECURITY HEADERS
# ─────────────────────────────────────────────────────────────
@app.middleware("http")
async def security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    
    # CSP permisivo para app móvil
    csp = (
        "default-src 'self' https:; "
        "script-src 'self' 'unsafe-inline' 'unsafe-eval'; "
        "style-src 'self' 'unsafe-inline'; "
        "img-src 'self' data: https: blob:; "
        "font-src 'self' data:; "
        "connect-src 'self' https://*.onrender.com https:; "
        "frame-ancestors 'none'; "
        "base-uri 'self'; "
        "form-action 'self'"
    )
    response.headers["Content-Security-Policy"] = csp
    
    if IS_PROD:
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    
    return response

# ─────────────────────────────────────────────────────────────
# 🏠 TRUSTED HOST (solo en prod, muy permisivo para Capacitor)
# ─────────────────────────────────────────────────────────────
if IS_PROD:
    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=[
            "financoop.onrender.com",
            "financash-backend.onrender.com",
            "financash-frontend.onrender.com",
            "localhost",
            "*"  # Permite cualquier host (necesario para Capacitor)
        ]
    )

# ─────────────────────────────────────────────────────────────
# ❌ GLOBAL EXCEPTION HANDLER
# ─────────────────────────────────────────────────────────────
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    request_id = request.headers.get("X-Request-ID", "unknown")
    logger.error(
        f"❌ [Error {request_id}] {type(exc).__name__}: {str(exc)}",
        exc_info=True
    )
    return JSONResponse(
        status_code=500,
        content={
            "detail": "Error interno del servidor",
            "request_id": request_id
        }
    )

# ─────────────────────────────────────────────────────────────
# 🗄️ CREAR TABLAS
# ─────────────────────────────────────────────────────────────
Base.metadata.create_all(bind=engine)

# ─────────────────────────────────────────────────────────────
# 📊 INICIALIZAR DATOS
# ─────────────────────────────────────────────────────────────
def init_db():
    db = next(get_db())
    try:
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

        tasa = db.query(TasaDolar).order_by(TasaDolar.id.desc()).first()
        if not tasa:
            tasa = TasaDolar(tasa=40.0, fuente="manual")
            db.add(tasa)
            logger.info("✅ Tasa dólar inicial creada: 40.0")

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
# 🚀 STARTUP
# ─────────────────────────────────────────────────────────────
@app.on_event("startup")
def startup():
    logger.info(f"🚀 FinanCash API iniciando | Entorno: {ENV}")
    logger.info(f"🌐 CORS orígenes permitidos: {ALLOWED_ORIGINS}")
    init_db()

# ─────────────────────────────────────────────────────────────
# ▶️ EJECUCIÓN
# ─────────────────────────────────────────────────────────────
if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=port,
        reload=not IS_PROD,
        workers=1 if not IS_PROD else None
    )