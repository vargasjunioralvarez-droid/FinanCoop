# backend/app/config.py
import os
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
# 🏆 NIVELES DE FINANCIAMIENTO - CONFIGURACIÓN POR DEFECTO
# ============================================================
# ⚠️ IMPORTANTE: El orden de los niveles es CRÍTICO.
# "nuevo" SIEMPRE debe ser el primer nivel (min_score = 0)
# Los niveles deben estar en orden ascendente de score.

# backend/app/config.py

NIVELES_CONFIG_DEFAULT = {
    "nuevo": {
        "min_score": 0,
        "max_score": 99,
        "monto_max_usd": 100,
        "entrada_pct": 0.30,
        "financia_pct": 0.70,
        "cuotas_base": 3,
        "cuotas_max": 6,
        "mora_diaria": 0.02,
        "aprobacion_extra": False
    },
    "bronce": {
        "min_score": 100,
        "max_score": 199,
        "monto_max_usd": 200,
        "entrada_pct": 0.25,
        "financia_pct": 0.75,
        "cuotas_base": 4,
        "cuotas_max": 8,
        "mora_diaria": 0.015,
        "aprobacion_extra": False
    },
    "plata": {
        "min_score": 200,
        "max_score": 299,
        "monto_max_usd": 400,
        "entrada_pct": 0.20,
        "financia_pct": 0.80,
        "cuotas_base": 4,
        "cuotas_max": 10,
        "mora_diaria": 0.01,
        "aprobacion_extra": False
    },
    "oro": {
        "min_score": 300,
        "max_score": 399,
        "monto_max_usd": 800,
        "entrada_pct": 0.15,
        "financia_pct": 0.85,
        "cuotas_base": 3,
        "cuotas_max": 12,
        "mora_diaria": 0.01,
        "aprobacion_extra": True
    },
    "platino": {
        "min_score": 400,
        "max_score": 9999,
        "monto_max_usd": 1500,
        "entrada_pct": 0.10,
        "financia_pct": 0.90,
        "cuotas_base": 3,
        "cuotas_max": 15,
        "mora_diaria": 0.005,
        "aprobacion_extra": True
    }
}

# Variable global que se modifica en runtime
NIVELES_CONFIG = dict(NIVELES_CONFIG_DEFAULT)

# ============================================================
# ✅ CONFIGURACIÓN DE CLOUDFLARE IMAGES
# ============================================================

CLOUDFLARE_ACCOUNT_ID = os.getenv("CLOUDFLARE_ACCOUNT_ID", "")
CLOUDFLARE_API_TOKEN = os.getenv("CLOUDFLARE_API_TOKEN", "")
CLOUDFLARE_IMAGES_URL = f"https://api.cloudflare.com/client/v4/accounts/{CLOUDFLARE_ACCOUNT_ID}/images/v1"
CLOUDFLARE_DELIVERY_URL = f"https://imagedelivery.net/{CLOUDFLARE_ACCOUNT_ID}"
CLOUDFLARE_CONFIGURADO = bool(CLOUDFLARE_ACCOUNT_ID and CLOUDFLARE_API_TOKEN)

if CLOUDFLARE_CONFIGURADO:
    print("✅ Cloudflare Images configurado correctamente")
else:
    print("⚠️ Cloudflare Images NO configurado (faltan credenciales)")