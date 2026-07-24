# app/modules/auth/schemas.py
from pydantic import BaseModel, Field
from typing import Optional

# ============================================================
# SCHEMAS DE AUTENTICACIÓN
# ============================================================

class LoginApp(BaseModel):
    """Schema para login desde app móvil"""
    cedula: str
    pin: str

class TokenResponse(BaseModel):
    """Schema para respuesta de token"""
    access_token: str
    token_type: str = "bearer"
    user: Optional[dict] = None