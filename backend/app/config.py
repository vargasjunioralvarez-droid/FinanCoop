# backend/app/routers/config.py
"""
🔧 FinanCoop - Configuración Dinámica de Niveles
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import NivelConfig
from app.auth import get_current_user
from pydantic import BaseModel, Field
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/config", tags=["Configuración"])

# ============================================================
# 📊 OBTENER NIVELES (público para app móvil)
# ============================================================

@router.get("/niveles")
def obtener_niveles(db: Session = Depends(get_db)):
    """
    Devuelve la configuración actual de niveles de crédito.
    Usado por la app móvil para mostrar límites dinámicos.
    """
    niveles = db.query(NivelConfig).all()
    
    if not niveles:
        logger.warning("⚠️ No hay niveles configurados en la base de datos")
        raise HTTPException(status_code=404, detail="Configuración de niveles no encontrada")
    
    resultado = {}
    for nivel in niveles:
        resultado[nivel.nivel] = {
            "min_score": nivel.min_score,
            "max_score": nivel.max_score,
            "monto_max_usd": nivel.monto_max_usd,
            "entrada_pct": nivel.entrada_pct,
            "financia_pct": nivel.financia_pct,
            "cuotas_base": nivel.cuotas_base,
            "cuotas_max": nivel.cuotas_max,
            "mora_diaria": nivel.mora_diaria,
            "aprobacion_extra": nivel.aprobacion_extra
        }
    
    logger.info(f"📊 Niveles enviados: {list(resultado.keys())}")
    return resultado  # ← SIN WRAPPER "niveles"

# ============================================================
# 📝 ACTUALIZAR NIVEL (solo admin)
# ============================================================

class NivelUpdateRequest(BaseModel):
    monto_max_usd: float = Field(..., gt=0)
    entrada_pct: float = Field(..., ge=0, le=100)
    financia_pct: float = Field(..., ge=0, le=100)
    cuotas_base: int = Field(..., ge=1)
    cuotas_max: int = Field(..., ge=1)
    mora_diaria: float = Field(..., ge=0)
    aprobacion_extra: bool = False

@router.put("/niveles/{nivel_key}")
def actualizar_nivel(
    nivel_key: str,
    request: NivelUpdateRequest,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Actualiza un nivel de crédito. Requiere rol admin.
    """
    if current_user.rol != "admin":
        logger.warning(f"🚫 Usuario {current_user.username} intentó modificar niveles sin permisos")
        raise HTTPException(status_code=403, detail="Permisos insuficientes")
    
    nivel = db.query(NivelConfig).filter(NivelConfig.nivel == nivel_key).first()
    if not nivel:
        raise HTTPException(status_code=404, detail=f"Nivel '{nivel_key}' no encontrado")
    
    nivel.monto_max_usd = request.monto_max_usd
    nivel.entrada_pct = request.entrada_pct
    nivel.financia_pct = request.financia_pct
    nivel.cuotas_base = request.cuotas_base
    nivel.cuotas_max = request.cuotas_max
    nivel.mora_diaria = request.mora_diaria
    nivel.aprobacion_extra = request.aprobacion_extra
    
    db.commit()
    db.refresh(nivel)
    
    logger.info(f"✅ Nivel '{nivel_key}' actualizado por {current_user.username}")
    
    return {
        "mensaje": f"Nivel '{nivel_key}' actualizado",
        "nivel": nivel_key,
        "monto_max_usd": nivel.monto_max_usd
    }