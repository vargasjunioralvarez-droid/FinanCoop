# app/modules/loans/schemas.py
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

# ============================================================
# SCHEMAS DE FINANCIAMIENTOS
# ============================================================

class FinanciamientoCreate(BaseModel):
    """Schema para crear un financiamiento"""
    cliente_id: int
    descripcion: str = ""
    monto_total_bs: float
    cuotas_solicitadas: int
    numero_factura: Optional[str] = None

class FinanciamientoUpdate(BaseModel):
    """Schema para actualizar un financiamiento"""
    descripcion: Optional[str] = None
    monto_total_bs: Optional[float] = None
    cuotas_solicitadas: Optional[int] = None
    estado: Optional[str] = None

class AprobacionExtra(BaseModel):
    """Schema para aprobación extra de financiamiento"""
    financiamiento_id: int
    cuotas_aprobadas: int
    aprobado_por: str

class FinanciamientoResponse(BaseModel):
    """Schema para respuesta de financiamiento"""
    id: int
    cliente_id: int
    codigo: Optional[str]
    descripcion: Optional[str]
    monto_total_bs: float
    monto_total_usd: float
    cuotas_solicitadas: int
    cuotas_aprobadas: int
    estado: str
    creado_en: datetime
    
    class Config:
        from_attributes = True