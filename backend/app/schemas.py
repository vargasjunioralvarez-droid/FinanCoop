# backend/app/schemas.py
from pydantic import BaseModel, Field
from typing import Optional

class ClienteCreate(BaseModel):
    nombre: str
    cedula: str
    telefono: str
    email: str = ""
    direccion: str = ""
    referencia_nombre: str = ""
    referencia_telefono: str = ""
    referencia_parentesco: str = ""

class LoginApp(BaseModel):
    cedula: str
    pin: str

class PagoReporte(BaseModel):
    cuota_id: int
    monto_bs: float
    metodo: str
    referencia: str
    banco_origen: str = ""
    telefono_pago: str = ""
    cedula_pago: str = ""
    comprobante: str = ""

class ConciliacionPago(BaseModel):
    pago_id: int
    monto_confirmado_bs: float
    estado: str
    conciliado_por: str

class TasaUpdate(BaseModel):
    tasa: float
    actualizado_por: str = "admin"

class AprobacionExtra(BaseModel):
    financiamiento_id: int
    cuotas_aprobadas: int
    aprobado_por: str

class FinanciamientoCreate(BaseModel):
    cliente_id: int
    descripcion: str = ""
    monto_total_bs: float
    cuotas_solicitadas: int
    numero_factura: Optional[str] = None  # ✅ NUEVO

class NivelConfigUpdate(BaseModel):
    monto_max_usd: float
    entrada_pct: float
    financia_pct: float
    cuotas_base: int
    cuotas_max: int
    mora_diaria: float
    aprobacion_extra: bool