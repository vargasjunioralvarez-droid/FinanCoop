"""
🔒 FinanCoop API - Configuración Principal con Seguridad Hardenizada
"""

import os
import logging
from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse, HTMLResponse
from datetime import datetime, timezone

# ============================================================
# 🔥 IMPORTS ACTUALIZADOS (NUEVA ESTRUCTURA)
# ============================================================

# Core
from app.core.database import engine, Base, get_db

# Models (desde módulos)
from app.modules.config.models import NivelConfig, TasaDolar
from app.modules.payments.models import ConfiguracionPago

# Config
from app.core.config import NIVELES_CONFIG_DEFAULT

# Utils
from app.shared.utils import get_niveles_config

# Routers (desde módulos)
from app.modules.auth.router import router as auth_router
from app.modules.users.router import router as clientes_router
from app.modules.loans.router import router as financiamientos_router
from app.modules.payments.router import router as pagos_router
from app.modules.config.router import router as config_router
from app.modules.mobile.router import router as app_mobile_router
from app.modules.admin.router import router as admin_router
from app.modules.uploads.router import router as upload_router
from app.modules.banks.router import router as bancos_router
from app.modules.audit.router import router as audit_router

# ⏰ Scheduler para backups automáticos
from app.core.scheduler import iniciar_scheduler

# ============================================================
# 📊 INICIALIZACIÓN DE DATOS (NUEVO ARCHIVO)
# ============================================================
from app.core.init_db import init_db


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
    title="FinanCoop API",
    description="API segura para sistema de financiamiento cooperativo",
    version="4.0.0",
    docs_url="/docs" if not IS_PROD else None,
    redoc_url="/redoc" if not IS_PROD else None,
    openapi_url="/openapi.json" if not IS_PROD else None,
)

# ─────────────────────────────────────────────────────────────
# 🌐 CORS CONFIGURACIÓN SEGURA (sin middleware manual inseguro)
# ─────────────────────────────────────────────────────────────
ALLOWED_ORIGINS = [
    # Desarrollo local
    "http://localhost:5173",
    "http://localhost:5174",
    "http://localhost:5175",
    "http://localhost:5176",
    "http://127.0.0.1:5173",
    "http://127.0.0.1:5174",
    "http://127.0.0.1:5175",
    "http://127.0.0.1:5176",
    "http://192.168.10.122:5175",
    "http://192.168.100.26:5175",
    
    # Capacitor APK
    "capacitor://localhost",
    "ionic://localhost",
    "http://localhost",
    "https://localhost",
    "https://financoop.app",
    "capacitor://financoop.app",
    
    # Producción
    "https://financoop.onrender.com",
    "https://financoop-frontend.onrender.com",
    "https://financoop-backend.onrender.com",
    "https://financoop-agd5.onrender.com",
    "https://financoop-frontend-2hvc.onrender.com",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"],  # Restringido
    allow_headers=["Authorization", "Content-Type", "X-Request-ID", "X-Requested-With", "Accept"],  # Restringido
    expose_headers=["X-Request-ID"],
    max_age=86400
)

logger.info(f"🌐 CORS orígenes permitidos: {ALLOWED_ORIGINS}")

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
    response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
    
    if IS_PROD:
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    
    return response

# ─────────────────────────────────────────────────────────────
# 📚 SWAGGER UI PERSONALIZADO
# ─────────────────────────────────────────────────────────────
@app.get("/docs", include_in_schema=False)
async def custom_swagger_ui_html():
    html = """
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <title>FinanCoop API - Swagger UI</title>
        <link rel="stylesheet" type="text/css" href="https://cdn.jsdelivr.net/npm/swagger-ui-dist@5/swagger-ui.css" />
    </head>
    <body>
        <div id="swagger-ui"></div>
        <script src="https://cdn.jsdelivr.net/npm/swagger-ui-dist@5/swagger-ui-bundle.js"></script>
        <script>
            window.onload = function() {
                window.ui = SwaggerUIBundle({
                    url: "/openapi.json",
                    dom_id: "#swagger-ui",
                    deepLinking: true,
                    defaultModelsExpandDepth: -1,
                    docExpansion: "none",
                    persistAuthorization: true,
                    validatorUrl: null,
                });
            };
        </script>
    </body>
    </html>
    """
    return HTMLResponse(content=html)

# ─────────────────────────────────────────────────────────────
# 🏠 TRUSTED HOST
# ─────────────────────────────────────────────────────────────
if IS_PROD:
    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=[
            "financoop.onrender.com",
            "financoop-backend.onrender.com",
            "financoop-frontend.onrender.com",
            "financoop-agd5.onrender.com",
            "financoop-frontend-2hvc.onrender.com",
            "localhost",
            "*.onrender.com"
        ]
    )

# ─────────────────────────────────────────────────────────────
# ❌ GLOBAL EXCEPTION HANDLER
# ─────────────────────────────────────────────────────────────
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    request_id = request.headers.get("X-Request-ID", "unknown")
    logger.error(f"❌ [Error {request_id}] {type(exc).__name__}: {str(exc)}")
    return JSONResponse(
        status_code=500,
        content={"detail": "Error interno del servidor", "request_id": request_id}
    )

# ─────────────────────────────────────────────────────────────
# ❤️ HEALTH CHECK
# ─────────────────────────────────────────────────────────────
@app.get("/health", include_in_schema=False)
def health_check():
    """Endpoint de monitoreo para balanceadores de carga."""
    try:
        from app.core.database import SessionLocal
        db = SessionLocal()
        db.execute("SELECT 1")
        db.close()
        return {"status": "healthy", "database": "connected"}
    except Exception as e:
        return JSONResponse(
            status_code=503,
            content={"status": "unhealthy", "database": "disconnected", "error": str(e)}
        )

# ─────────────────────────────────────────────────────────────
# 🗄️ CREAR TABLAS
# ─────────────────────────────────────────────────────────────
import app.modules.users.models as _users_models
import app.modules.loans.models as _loans_models
import app.modules.payments.models as _payments_models
import app.modules.config.models as _config_models
import app.modules.auth.models as _auth_models
import app.modules.audit.models as _audit_models
if not os.getenv("SKIP_DB_INIT"):
    Base.metadata.create_all(bind=engine, checkfirst=True)

# ─────────────────────────────────────────────────────────────
# 🔌 ROUTERS CON PREFIJO /api/v1
# ─────────────────────────────────────────────────────────────
API_PREFIX = "/api/v1"

app.include_router(auth_router, prefix=API_PREFIX)
app.include_router(clientes_router, prefix=API_PREFIX)
app.include_router(financiamientos_router, prefix=API_PREFIX)
app.include_router(pagos_router, prefix=API_PREFIX)
app.include_router(config_router, prefix=API_PREFIX)
app.include_router(app_mobile_router, prefix=API_PREFIX)
app.include_router(admin_router, prefix=API_PREFIX)
app.include_router(upload_router, prefix=API_PREFIX)
app.include_router(bancos_router, prefix=API_PREFIX)
app.include_router(audit_router, prefix=API_PREFIX)

# ─────────────────────────────────────────────────────────────
# 🚀 STARTUP
# ─────────────────────────────────────────────────────────────
@app.on_event("startup")
def startup():
    logger.info(f"🚀 FinanCoop API iniciando | Entorno: {ENV}")
    
    # ✅ Inicializar datos mínimos (niveles, tasa, configuraciones)
    try:
        init_db()
    except Exception as e:
        logger.error(f"❌ Error inicializando datos: {e}")
    
    # ✅ Cargar niveles desde BD al iniciar
    try:
        get_niveles_config(next(get_db()))
        logger.info("✅ Niveles cargados desde BD")
    except Exception as e:
        logger.warning(f"⚠️ No se pudieron cargar niveles: {e}")
    
    # ✅ INICIAR SCHEDULER (solo en producción)
    if IS_PROD:
        iniciar_scheduler()
        logger.info("⏰ Scheduler de backups iniciado")

# ─────────────────────────────────────────────────────────────
# ▶️ EJECUCIÓN
# ─────────────────────────────────────────────────────────────
if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=port,
        reload=not IS_PROD,
        workers=1 if not IS_PROD else None
    )