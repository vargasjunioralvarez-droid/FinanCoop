# backend/app/routers/config.py
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from datetime import datetime, timezone
import logging
from app.database import get_db
from app.models import TasaDolar, NivelConfig, Financiamiento, Cuota
from app.config import NIVELES_CONFIG, NIVELES_CONFIG_DEFAULT
from app.auth import get_current_admin
from app.utils import obtener_tasa_actual

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/config", tags=["Configuración"])

# ============================================================
# 📋 MODELOS
# ============================================================

class TasaUpdate(BaseModel):
    tasa: float
    actualizado_por: str = "admin"

class NivelConfigUpdate(BaseModel):
    monto_max_usd: float
    entrada_pct: float
    financia_pct: float
    cuotas_base: int
    cuotas_max: int
    mora_diaria: float
    aprobacion_extra: bool

# ============================================================
# 💰 TASA DEL DÓLAR
# ============================================================

@router.get("/tasa-dolar")
def obtener_tasa(db: Session = Depends(get_db)):
    """Obtener la tasa de cambio actual y su historial"""
    logger.info("=" * 50)
    logger.info("🔍 [tasa-dolar] INICIO")
    
    try:
        # Obtener tasa actual
        tasa = obtener_tasa_actual(db)
        logger.info(f"✅ [tasa-dolar] Tasa actual: {tasa}")
        
        # Obtener historial
        historial = db.query(TasaDolar).order_by(TasaDolar.id.desc()).limit(20).all()
        logger.info(f"✅ [tasa-dolar] Historial obtenido: {len(historial)} registros")
        
        # Construir respuesta
        response = {
            "tasa": tasa,
            "fecha": datetime.now(timezone.utc).isoformat(),
            "historial": []
        }
        
        for h in historial:
            item = {
                "tasa": h.tasa,
                "fuente": getattr(h, 'fuente', 'manual'),
                "fecha": h.fecha.isoformat() if h.fecha else None
            }
            response["historial"].append(item)
        
        logger.info(f"✅ [tasa-dolar] Respuesta construida")
        logger.info("=" * 50)
        return response
        
    except Exception as e:
        logger.error(f"❌ [tasa-dolar] ERROR: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/tasa-dolar")
def actualizar_tasa(
    request: TasaUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_admin)
):
    """Actualizar tasa manualmente y recalcular cuotas"""
    logger.info(f"🚀 [tasa-dolar] Actualizando tasa a {request.tasa} por {request.actualizado_por}")
    
    try:
        # Guardar nueva tasa
        nueva_tasa = TasaDolar(
            tasa=request.tasa,
            fuente="manual"
        )
        db.add(nueva_tasa)
        
        # Recalcular cuotas pendientes
        financiamientos_afectados = 0
        cuotas_recalculadas = 0
        
        financiamientos = db.query(Financiamiento).filter(
            Financiamiento.estado == "activo"
        ).all()
        
        for f in financiamientos:
            cuotas_pendientes = db.query(Cuota).filter(
                Cuota.financiamiento_id == f.id,
                Cuota.estado == "pendiente"
            ).all()
            
            if cuotas_pendientes:
                financiamientos_afectados += 1
                for c in cuotas_pendientes:
                    # Recalcular montos en BS según nueva tasa
                    if hasattr(c, 'monto_base_usd') and c.monto_base_usd:
                        c.monto_total_bs = c.monto_base_usd * request.tasa
                        cuotas_recalculadas += 1
        
        db.commit()
        
        logger.info(f"✅ [tasa-dolar] Tasa actualizada. Financiamientos: {financiamientos_afectados}, Cuotas: {cuotas_recalculadas}")
        
        return {
            "mensaje": "Tasa actualizada correctamente",
            "tasa": request.tasa,
            "financiamientos_afectados": financiamientos_afectados,
            "cuotas_recalculadas": cuotas_recalculadas
        }
        
    except Exception as e:
        db.rollback()
        logger.error(f"❌ [tasa-dolar] ERROR: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/tasa-dolar/bcv")
def actualizar_tasa_bcv(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_admin)
):
    """Consultar tasa del BCV y actualizar"""
    logger.info("🌐 [tasa-dolar] Consultando BCV...")
    
    try:
        # Aquí iría la lógica real de consulta al BCV
        # Por ahora, simulamos que no se pudo obtener
        tasa_actual = obtener_tasa_actual(db)
        
        return {
            "error": True,
            "mensaje": "Servicio BCV no disponible. Usando tasa manual.",
            "tasa_actual": tasa_actual,
            "cuotas_recalculadas": 0
        }
        
    except Exception as e:
        logger.error(f"❌ [tasa-dolar/bcv] ERROR: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ============================================================
# 🏆 NIVELES DE FINANCIAMIENTO
# ============================================================

@router.get("/niveles")
def obtener_niveles(db: Session = Depends(get_db)):
    """Obtener configuración de niveles"""
    logger.info("📋 [niveles] Obteniendo configuración")
    
    try:
        niveles_db = db.query(NivelConfig).all()
        
        if not niveles_db:
            # Inicializar con defaults
            for nivel_key, config in NIVELES_CONFIG_DEFAULT.items():
                nc = NivelConfig(
                    nivel=nivel_key,
                    min_score=config["min_score"],
                    max_score=config["max_score"],
                    monto_max_usd=config["monto_max_usd"],
                    entrada_pct=config["entrada_pct"],
                    financia_pct=config["financia_pct"],
                    cuotas_base=config["cuotas_base"],
                    cuotas_max=config["cuotas_max"],
                    mora_diaria=config["mora_diaria"],
                    aprobacion_extra=config["aprobacion_extra"]
                )
                db.add(nc)
            db.commit()
            niveles_db = db.query(NivelConfig).all()
        
        # Convertir a dict
        niveles = {}
        for n in niveles_db:
            niveles[n.nivel] = {
                "min_score": n.min_score,
                "max_score": n.max_score,
                "monto_max_usd": n.monto_max_usd,
                "entrada_pct": n.entrada_pct,
                "financia_pct": n.financia_pct,
                "cuotas_base": n.cuotas_base,
                "cuotas_max": n.cuotas_max,
                "mora_diaria": n.mora_diaria,
                "aprobacion_extra": n.aprobacion_extra
            }
        
        return {"niveles": niveles}
        
    except Exception as e:
        logger.error(f"❌ [niveles] ERROR: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/niveles/{nivel}")
def actualizar_nivel(
    nivel: str,
    request: NivelConfigUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_admin)
):
    """Actualizar configuración de un nivel"""
    logger.info(f"🚀 [niveles] Actualizando nivel: {nivel}")
    
    try:
        config = db.query(NivelConfig).filter(NivelConfig.nivel == nivel).first()
        
        if not config:
            raise HTTPException(status_code=404, detail=f"Nivel {nivel} no encontrado")
        
        config.monto_max_usd = request.monto_max_usd
        config.entrada_pct = request.entrada_pct
        config.financia_pct = request.financia_pct
        config.cuotas_base = request.cuotas_base
        config.cuotas_max = request.cuotas_max
        config.mora_diaria = request.mora_diaria
        config.aprobacion_extra = request.aprobacion_extra
        
        db.commit()
        
        logger.info(f"✅ [niveles] Nivel {nivel} actualizado")
        return {"mensaje": f"Nivel {nivel} actualizado correctamente"}
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"❌ [niveles] ERROR: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/niveles/reset")
def reset_niveles(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_admin)
):
    """Restaurar niveles a valores por defecto"""
    logger.info("🔄 [niveles] Restaurando valores por defecto")
    
    try:
        # Borrar existentes
        db.query(NivelConfig).delete()
        
        # Crear defaults
        for nivel_key, config in NIVELES_CONFIG_DEFAULT.items():
            nc = NivelConfig(
                nivel=nivel_key,
                min_score=config["min_score"],
                max_score=config["max_score"],
                monto_max_usd=config["monto_max_usd"],
                entrada_pct=config["entrada_pct"],
                financia_pct=config["financia_pct"],
                cuotas_base=config["cuotas_base"],
                cuotas_max=config["cuotas_max"],
                mora_diaria=config["mora_diaria"],
                aprobacion_extra=config["aprobacion_extra"]
            )
            db.add(nc)
        
        db.commit()
        
        logger.info("✅ [niveles] Valores restaurados")
        return {"mensaje": "Niveles restaurados a valores por defecto"}
        
    except Exception as e:
        db.rollback()
        logger.error(f"❌ [niveles] ERROR: {e}")
        raise HTTPException(status_code=500, detail=str(e))