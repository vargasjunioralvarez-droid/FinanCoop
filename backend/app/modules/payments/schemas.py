# app/modules/payments/schemas.py
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional
from datetime import datetime

# ============================================================
# SCHEMAS DE PAGOS
# ============================================================

class PagoReporte(BaseModel):
    """Schema para reportar un pago"""
    cuota_id: int
    monto_bs: float
    metodo: str
    referencia: str
    banco_origen: str = ""
    telefono_pago: str = ""
    cedula_pago: str = ""
    comprobante: str = ""

class PagoConfirmacion(BaseModel):
    """Schema para confirmar un pago"""
    pago_id: int
    monto_confirmado_bs: float
    conciliado_por: str

class ConciliacionPago(BaseModel):
    """Schema para conciliación de pago"""
    pago_id: int
    monto_confirmado_bs: float
    estado: str
    conciliado_por: str

class PagoResponse(BaseModel):
    """Schema para respuesta de pago"""
    id: int
    financiamiento_id: int
    cuota_id: Optional[int]
    monto: float
    monto_usd: float
    metodo: str
    referencia: Optional[str]
    estado: str
    fecha_reporte: datetime
    
    model_config = ConfigDict(from_attributes=True)