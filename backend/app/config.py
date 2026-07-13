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

NIVELES_CONFIG_DEFAULT = {
    "nuevo": {
        "min_score": 0,
        "max_score": 9,           # 👈 Ajustado: 0-9 = nuevo
        "monto_max_usd": 160,
        "entrada_pct": 60,
        "financia_pct": 40,
        "cuotas_base": 3,
        "cuotas_max": 3,
        "mora_diaria": 2.0,
        "aprobacion_extra": False
    },
    "bronce": {
        "min_score": 10,          # 👈 Ajustado: 10-24 = bronce
        "max_score": 24,
        "monto_max_usd": 200,
        "entrada_pct": 50,
        "financia_pct": 50,
        "cuotas_base": 3,
        "cuotas_max": 5,
        "mora_diaria": 1.5,
        "aprobacion_extra": True
    },
    "plata": {
        "min_score": 25,          # 👈 Ajustado: 25-49 = plata
        "max_score": 49,
        "monto_max_usd": 250,
        "entrada_pct": 40,
        "financia_pct": 60,
        "cuotas_base": 6,
        "cuotas_max": 8,
        "mora_diaria": 1.0,
        "aprobacion_extra": True
    },
    "oro": {
        "min_score": 50,          # 👈 Ajustado: 50-99 = oro
        "max_score": 99,
        "monto_max_usd": 350,
        "entrada_pct": 30,
        "financia_pct": 70,
        "cuotas_base": 8,
        "cuotas_max": 12,
        "mora_diaria": 0.5,
        "aprobacion_extra": True
    },
    "platino": {
        "min_score": 100,         # 👈 Ajustado: 100+ = platino
        "max_score": 99999,
        "monto_max_usd": 500,
        "entrada_pct": 20,
        "financia_pct": 80,
        "cuotas_base": 12,
        "cuotas_max": 15,
        "mora_diaria": 0.5,
        "aprobacion_extra": True
    },
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