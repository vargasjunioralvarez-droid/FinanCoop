# app/core/config.py
import os
from dotenv import load_dotenv
from typing import Dict, Any, Optional
from pathlib import Path

# Cargar variables de entorno
load_dotenv()

# ============================================================
# 🔥 ENUMS (los mantenemos exactamente igual)
# ============================================================

import enum

class EstadoFinanciamiento(str, enum.Enum):
    ACTIVO = "activo"
    COMPLETADO = "completado"
    CANCELADO = "cancelado"
    MORA = "mora"

class EstadoCuota(str, enum.Enum):
    PENDIENTE = "pendiente"
    PAGADA = "pagada"
    ATRASADA = "atrasada"
    CONCILIANDO = "conciliando"

class MetodoPago(str, enum.Enum):
    PAGO_MOVIL = "pago_movil"
    TRANSFERENCIA = "transferencia"
    ZELLE = "zelle"
    BINANCE = "binance"
    EFECTIVO = "efectivo"
    PUNTO_VENTA = "punto_venta"

class Nivel(str, enum.Enum):
    NUEVO = "nuevo"
    BRONCE = "bronce"
    PLATA = "plata"
    ORO = "oro"
    PLATINO = "platino"


# ============================================================
# 🔥 CONFIGURACIÓN DE NIVELES (mantenemos exactamente igual)
# ============================================================

# ⚠️ IMPORTANTE: El orden de los niveles es CRÍTICO.
# "nuevo" SIEMPRE debe ser el primer nivel (min_score = 0)
# Los niveles deben estar en orden ascendente de score.

NIVELES_CONFIG_DEFAULT = {
    "nuevo": {
        "min_score": 0,
        "max_score": 99,
        "monto_max_usd": 100,
        "entrada_pct": 30,    # ✅ 30% (entero)
        "financia_pct": 70,   # ✅ 70% (entero)
        "cuotas_base": 3,
        "cuotas_max": 6,
        "mora_diaria": 2,     # ✅ 2% (entero)
        "aprobacion_extra": False
    },
    "bronce": {
        "min_score": 100,
        "max_score": 199,
        "monto_max_usd": 200,
        "entrada_pct": 25,    # ✅ 25%
        "financia_pct": 75,   # ✅ 75%
        "cuotas_base": 4,
        "cuotas_max": 8,
        "mora_diaria": 1.5,   # ✅ 1.5%
        "aprobacion_extra": False
    },
    "plata": {
        "min_score": 200,
        "max_score": 299,
        "monto_max_usd": 400,
        "entrada_pct": 20,    # ✅ 20%
        "financia_pct": 80,   # ✅ 80%
        "cuotas_base": 4,
        "cuotas_max": 10,
        "mora_diaria": 1,     # ✅ 1%
        "aprobacion_extra": False
    },
    "oro": {
        "min_score": 300,
        "max_score": 399,
        "monto_max_usd": 800,
        "entrada_pct": 15,    # ✅ 15%
        "financia_pct": 85,   # ✅ 85%
        "cuotas_base": 3,
        "cuotas_max": 12,
        "mora_diaria": 1,     # ✅ 1%
        "aprobacion_extra": True
    },
    "platino": {
        "min_score": 400,
        "max_score": 9999,
        "monto_max_usd": 1500,
        "entrada_pct": 10,    # ✅ 10%
        "financia_pct": 90,   # ✅ 90%
        "cuotas_base": 3,
        "cuotas_max": 15,
        "mora_diaria": 0.5,   # ✅ 0.5%
        "aprobacion_extra": True
    }
}

# Variable global que se modifica en runtime
NIVELES_CONFIG = dict(NIVELES_CONFIG_DEFAULT)


# ============================================================
# ✅ CONFIGURACIÓN DE CLOUDFLARE IMAGES (mantenemos igual)
# ============================================================

CLOUDFLARE_ACCOUNT_ID = os.getenv("CLOUDFLARE_ACCOUNT_ID", "")
CLOUDFLARE_API_TOKEN = os.getenv("CLOUDFLARE_API_TOKEN", "")
CLOUDFLARE_IMAGES_URL = f"https://api.cloudflare.com/client/v4/accounts/{CLOUDFLARE_ACCOUNT_ID}/images/v1"
CLOUDFLARE_DELIVERY_URL = f"https://imagedelivery.net/{CLOUDFLARE_ACCOUNT_ID}"
CLOUDFLARE_CONFIGURADO = bool(CLOUDFLARE_ACCOUNT_ID and CLOUDFLARE_API_TOKEN)


# ============================================================
# 🆕 NUEVAS MEJORAS (sin romper lo existente)
# ============================================================

class Settings:
    """Configuración centralizada del backend"""
    
    # App
    APP_NAME: str = "FinanCash API"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = os.getenv("DEBUG", "False").lower() == "true"
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")
    
    # Server
    HOST: str = os.getenv("HOST", "0.0.0.0")
    PORT: int = int(os.getenv("PORT", "8000"))
    
    # Database
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./financash.db")
    
    # JWT
    JWT_SECRET_KEY: str = os.getenv("JWT_SECRET_KEY", "your-secret-key-change-in-production")
    JWT_ALGORITHM: str = os.getenv("JWT_ALGORITHM", "HS256")
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("JWT_ACCESS_TOKEN_EXPIRE_MINUTES", "30"))
    REFRESH_TOKEN_EXPIRE_DAYS: int = int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", "7"))
    
    # CORS
    CORS_ORIGINS: list = os.getenv("CORS_ORIGINS", "http://localhost:5173,http://localhost:3000").split(",")
    
    # Upload
    UPLOAD_DIR: str = os.getenv("UPLOAD_DIR", "./uploads")
    MAX_UPLOAD_SIZE: int = int(os.getenv("MAX_UPLOAD_SIZE", "5242880"))  # 5MB
    
    # Cloudflare (referencia a las variables existentes)
    CLOUDFLARE_ACCOUNT_ID: str = CLOUDFLARE_ACCOUNT_ID
    CLOUDFLARE_API_TOKEN: str = CLOUDFLARE_API_TOKEN
    CLOUDFLARE_IMAGES_URL: str = CLOUDFLARE_IMAGES_URL
    CLOUDFLARE_DELIVERY_URL: str = CLOUDFLARE_DELIVERY_URL
    CLOUDFLARE_CONFIGURADO: bool = CLOUDFLARE_CONFIGURADO
    
    @property
    def is_development(self) -> bool:
        return self.ENVIRONMENT == "development"
    
    @property
    def is_production(self) -> bool:
        return self.ENVIRONMENT == "production"
    
    @property
    def is_testing(self) -> bool:
        return self.ENVIRONMENT == "testing"

# Instancia única para usar en toda la app
settings = Settings()

# ============================================================
# 🔥 MANTENER COMPATIBILIDAD CON CÓDIGO EXISTENTE
# ============================================================
# Para que `from app.config import NIVELES_CONFIG` siga funcionando
# Exportamos todo al nivel raíz

# Enums
EstadoFinanciamiento = EstadoFinanciamiento
EstadoCuota = EstadoCuota
MetodoPago = MetodoPago
Nivel = Nivel

# Configuración de niveles
NIVELES_CONFIG_DEFAULT = NIVELES_CONFIG_DEFAULT
NIVELES_CONFIG = NIVELES_CONFIG

# Cloudflare
CLOUDFLARE_ACCOUNT_ID = CLOUDFLARE_ACCOUNT_ID
CLOUDFLARE_API_TOKEN = CLOUDFLARE_API_TOKEN
CLOUDFLARE_IMAGES_URL = CLOUDFLARE_IMAGES_URL
CLOUDFLARE_DELIVERY_URL = CLOUDFLARE_DELIVERY_URL
CLOUDFLARE_CONFIGURADO = CLOUDFLARE_CONFIGURADO

# Variables de entorno (para compatibilidad)
DATABASE_URL = settings.DATABASE_URL
JWT_SECRET_KEY = settings.JWT_SECRET_KEY
JWT_ALGORITHM = settings.JWT_ALGORITHM
JWT_ACCESS_TOKEN_EXPIRE_MINUTES = settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES
REFRESH_TOKEN_EXPIRE_DAYS = settings.REFRESH_TOKEN_EXPIRE_DAYS
CORS_ORIGINS = settings.CORS_ORIGINS
UPLOAD_DIR = settings.UPLOAD_DIR
MAX_UPLOAD_SIZE = settings.MAX_UPLOAD_SIZE
DEBUG = settings.DEBUG

print(f"✅ Configuración cargada - Entorno: {settings.ENVIRONMENT}")
if CLOUDFLARE_CONFIGURADO:
    print("✅ Cloudflare Images configurado correctamente")
else:
    print("⚠️ Cloudflare Images NO configurado (faltan credenciales)")