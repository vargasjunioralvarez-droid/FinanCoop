"""
🔒 FinanCash API - Configuración Principal con Seguridad Hardenizada
"""

import os
import logging
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse, HTMLResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response
from app.database import engine, Base, get_db
from app.models import NivelConfig, TasaDolar, ConfiguracionPago
from app.config import NIVELES_CONFIG_DEFAULT
from app.routers import (
    clientes_router, 
    financiamientos_router, 
    pagos_router, 
    config_router,
    app_mobile_router, 
    admin_router, 
    auth_router,
    upload_router  # ← AGREGADO PARA CLOUDFLARE
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
    "http://localhost:5176",
    "http://127.0.0.1:5173",
    "http://127.0.0.1:5174",
    "http://127.0.0.1:5175",
    "http://127.0.0.1:5176",
    "http://192.168.10.122:5175", 
    "capacitor://localhost",
    "ionic://localhost",
    "http://localhost",
    "https://localhost",
    "https://financoop-frontend.onrender.com",
    "https://financoop-backend.onrender.com",
    "https://financoop.onrender.com",
    "null",
    "",
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
# ✅ CORS NATIVO DE FASTAPI (MÁS CONFIABLE)
# ─────────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"],
    allow_headers=[
        "Authorization", 
        "Content-Type", 
        "X-Request-ID", 
        "X-Requested-With",
        "Accept", 
        "Origin", 
        "Cache-Control", 
        "Pragma", 
        "Expires"
    ],
    expose_headers=["X-Request-ID"],
    max_age=86400
)

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

    csp = (
        "default-src 'self' https: http://localhost:*; "
        "script-src 'self' 'unsafe-inline' 'unsafe-eval' https://cdn.jsdelivr.net; "
        "style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; "
        "img-src 'self' data: https: blob:; "
        "font-src 'self' data: https://cdn.jsdelivr.net; "
        "connect-src 'self' https://*.onrender.com https: http://localhost:*; "
        "frame-ancestors 'none'; "
        "base-uri 'self'; "
        "form-action 'self'"
    )
    response.headers["Content-Security-Policy"] = csp

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
            "financash-backend.onrender.com",
            "financash-frontend.onrender.com",
            "localhost",
            "*"
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
        
        # Verificar Cloudflare
        cloudflare_account_id = os.getenv("CLOUDFLARE_ACCOUNT_ID")
        cloudflare_api_token = os.getenv("CLOUDFLARE_API_TOKEN")
        if cloudflare_account_id and cloudflare_api_token:
            logger.info("✅ Cloudflare Images configurado correctamente")
        else:
            logger.warning("⚠️ Cloudflare Images NO configurado")
            
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
app.include_router(upload_router)  # ← AGREGADO PARA CLOUDFLARE

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