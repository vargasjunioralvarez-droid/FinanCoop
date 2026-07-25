from datetime import datetime
from pydantic import BaseModel, Field
from typing import Optional

# ============================================================
# SCHEMAS DE CONFIGURACIÓN
# ============================================================

class TasaUpdate(BaseModel):
    """Schema para actualizar la tasa del dólar"""
    tasa: float
    actualizado_por: str = "admin"

class TasaResponse(BaseModel):
    """Schema para respuesta de tasa del dólar"""
    id: int
    tasa: float
    fuente: str
    fecha: datetime
    
    class Config:
        from_attributes = True

class NivelConfigUpdate(BaseModel):
    """Schema para actualizar configuración de niveles"""
    monto_max_usd: float
    entrada_pct: float
    financia_pct: float
    cuotas_base: int
    cuotas_max: int
    mora_diaria: float
    aprobacion_extra: bool

class NivelConfigResponse(BaseModel):
    """Schema para respuesta de configuración de niveles"""
    id: int
    nivel: str
    min_score: int
    max_score: int
    monto_max_usd: float
    entrada_pct: float
    financia_pct: float
    cuotas_base: int
    cuotas_max: int
    mora_diaria: float
    aprobacion_extra: bool
    
    class Config:
        from_attributes = True