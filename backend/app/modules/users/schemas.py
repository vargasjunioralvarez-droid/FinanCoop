# app/modules/users/schemas.py
from pydantic import BaseModel, Field
from typing import Optional

# ============================================================
# SCHEMAS DE CLIENTES
# ============================================================

class ClienteCreate(BaseModel):
    """Schema para crear un cliente"""
    nombre: str
    cedula: str
    telefono: str
    email: str = ""
    direccion: str = ""
    referencia_nombre: str = ""
    referencia_telefono: str = ""
    referencia_parentesco: str = ""

class ClienteUpdate(BaseModel):
    """Schema para actualizar un cliente"""
    nombre: Optional[str] = None
    telefono: Optional[str] = None
    email: Optional[str] = None
    direccion: Optional[str] = None
    referencia_nombre: Optional[str] = None
    referencia_telefono: Optional[str] = None
    referencia_parentesco: Optional[str] = None

class ClienteResponse(BaseModel):
    """Schema para respuesta de cliente"""
    id: int
    nombre: str
    cedula: str
    telefono: Optional[str]
    email: Optional[str]
    direccion: Optional[str]
    score: int
    nivel: str
    estado: str
    
    class Config:
        from_attributes = True