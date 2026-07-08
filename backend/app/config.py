# app/config.py
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

NIVELES_CONFIG_DEFAULT = {
    "nuevo": {
        "min_score": 0, "max_score": 2,
        "monto_max_usd": 160,
        "entrada_pct": 60, "financia_pct": 40,
        "cuotas_base": 3, "cuotas_max": 3,
        "mora_diaria": 2.0,
        "aprobacion_extra": False
    },
    "bronce": {
        "min_score": 3, "max_score": 5,
        "monto_max_usd": 200,
        "entrada_pct": 50, "financia_pct": 50,
        "cuotas_base": 3, "cuotas_max": 5,
        "mora_diaria": 1.5,
        "aprobacion_extra": True
    },
    "plata": {
        "min_score": 6, "max_score": 10,
        "monto_max_usd": 250,
        "entrada_pct": 40, "financia_pct": 60,
        "cuotas_base": 6, "cuotas_max": 8,
        "mora_diaria": 1.0,
        "aprobacion_extra": True
    },
    "oro": {
        "min_score": 11, "max_score": 20,
        "monto_max_usd": 350,
        "entrada_pct": 30, "financia_pct": 70,
        "cuotas_base": 8, "cuotas_max": 12,
        "mora_diaria": 0.5,
        "aprobacion_extra": True
    },
    "platino": {
        "min_score": 21, "max_score": 999,
        "monto_max_usd": 500,
        "entrada_pct": 20, "financia_pct": 80,
        "cuotas_base": 12, "cuotas_max": 15,
        "mora_diaria": 0.5,
        "aprobacion_extra": True
    },
}

# Variable global que se modifica en runtime
NIVELES_CONFIG = dict(NIVELES_CONFIG_DEFAULT)