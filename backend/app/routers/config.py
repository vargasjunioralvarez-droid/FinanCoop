# backend/app/routers/config.py
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session
from datetime import datetime, timezone
import logging
from app.database import get_db
from app.models import TasaDolar, NivelConfig, Financiamiento, Cuota, ConfiguracionPago
from app.config import NIVELES_CONFIG_DEFAULT
from app.auth import get_current_admin
from app.utils import obtener_tasa_actual, get_niveles_config

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/config", tags=["Configuración"])

# ============================================================
# MODELOS
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

class ConfigPagoUpdate(BaseModel):
    banco_pago_movil: str = None
    telefono_pago_movil: str = None
    cedula_pago_movil: str = None
    banco_transferencia: str = None
    cuenta_transferencia: str = None
    correo_zelle: str = None
    correo_binance: str = None

# ============================================================
# TASA DEL DÓLAR
# ============================================================
@router.get("/tasa-dolar")
def obtener_tasa(db: Session = Depends(get_db)):
    """Obtener la tasa de cambio actual y su historial."""
    try:
        tasa = obtener_tasa_actual(db)
        
        historial = db.query(TasaDolar).order_by(TasaDolar.id.desc()).limit(20).all()
        
        return {
            "tasa": tasa,
            "fecha": datetime.now(timezone.utc).isoformat(),
            "historial": [
                {
                    "tasa": h.tasa,
                    "fuente": getattr(h, 'fuente', 'manual'),
                    "actualizado_por": getattr(h, 'actualizado_por', None),
                    "fecha": h.fecha.isoformat() if h.fecha else None
                }
                for h in historial
            ]
        }
    except Exception as e:
        logger.error(f"❌ Error obteniendo tasa: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/tasa-dolar")
def actualizar_tasa(
    request: TasaUpdate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_admin)
):
    """Actualizar tasa manualmente y recalcular cuotas pendientes."""
    try:
        if request.tasa <= 0:
            raise HTTPException(status_code=400, detail="La tasa debe ser mayor a 0")
        
        nueva_tasa = TasaDolar(
            tasa=request.tasa,
            fuente="manual",
            actualizado_por=request.actualizado_por
        )
        db.add(nueva_tasa)
        
        financiamientos_afectados = 0
        cuotas_recalculadas = 0
        
        financiamientos = db.query(Financiamiento).filter(
            Financiamiento.estado == "activo"
        ).all()
        
        for f in financiamientos:
            cuotas_pendientes = db.query(Cuota).filter(
                Cuota.financiamiento_id == f.id,
                Cuota.estado.in_(["pendiente", "conciliando"])
            ).all()
            
            if cuotas_pendientes:
                financiamientos_afectados += 1
                for c in cuotas_pendientes:
                    if c.monto_base_usd:
                        c.monto_total_bs = c.monto_base_usd * request.tasa
                        if c.monto_interes_mora_usd:
                            c.monto_interes_mora_bs = c.monto_interes_mora_usd * request.tasa
                        cuotas_recalculadas += 1
        
        db.commit()
        
        logger.info(f"✅ Tasa actualizada a {request.tasa} por {request.actualizado_por}")
        
        return {
            "success": True,
            "mensaje": "Tasa actualizada correctamente",
            "tasa": request.tasa,
            "financiamientos_afectados": financiamientos_afectados,
            "cuotas_recalculadas": cuotas_recalculadas
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error actualizando tasa: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

# ============================================================
# NIVELES DE FINANCIAMIENTO
# ============================================================
@router.get("/niveles")
def obtener_niveles(db: Session = Depends(get_db)):
    """Obtener configuración de niveles."""
    try:
        get_niveles_config(db)
        niveles_db = db.query(NivelConfig).all()
        
        if not niveles_db:
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
        
        niveles_ordenados = dict(sorted(
            niveles.items(),
            key=lambda x: x[1]["min_score"]
        ))
        
        return {"niveles": niveles_ordenados}
    except Exception as e:
        logger.error(f"❌ Error obteniendo niveles: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/niveles/{nivel}")
def actualizar_nivel(
    nivel: str,
    request: NivelConfigUpdate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_admin)
):
    """Actualizar configuración de un nivel."""
    try:
        config = db.query(NivelConfig).filter(NivelConfig.nivel == nivel).first()
        if not config:
            raise HTTPException(status_code=404, detail=f"Nivel '{nivel}' no encontrado")
        
        # ✅ CORREGIDO: validar suma = 100% (enteros, no decimales)
        if request.entrada_pct + request.financia_pct != 100:
            raise HTTPException(
                status_code=400, 
                detail=f"La suma de entrada ({request.entrada_pct}%) + financiamiento ({request.financia_pct}%) debe ser 100%"
            )
        
        config.monto_max_usd = request.monto_max_usd
        config.entrada_pct = request.entrada_pct
        config.financia_pct = request.financia_pct
        config.cuotas_base = request.cuotas_base
        config.cuotas_max = request.cuotas_max
        config.mora_diaria = request.mora_diaria
        config.aprobacion_extra = request.aprobacion_extra
        
        db.commit()
        get_niveles_config(db)
        
        logger.info(f"✅ Nivel '{nivel}' actualizado")
        return {"success": True, "mensaje": f"Nivel '{nivel}' actualizado correctamente"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error actualizando nivel: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/niveles/reset")
def reset_niveles(
    db: Session = Depends(get_db),
    current_user = Depends(get_current_admin)
):
    """Restaurar niveles a valores por defecto."""
    try:
        db.query(NivelConfig).delete()
        
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
        get_niveles_config(db)
        
        logger.info("✅ Niveles restaurados a valores por defecto")
        return {"success": True, "mensaje": "Niveles restaurados a valores por defecto"}
    except Exception as e:
        logger.error(f"❌ Error reseteando niveles: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

# ============================================================
# CONFIGURACIÓN DE PAGOS
# ============================================================
@router.get("/pago")
def obtener_config_pago(db: Session = Depends(get_db)):
    """Obtener métodos de pago configurados."""
    try:
        config = db.query(ConfiguracionPago).first()
        if not config:
            raise HTTPException(status_code=404, detail="Configuración no encontrada")
        
        return {
            "pago_movil": {
                "banco": config.banco_pago_movil,
                "telefono": config.telefono_pago_movil,
                "cedula": config.cedula_pago_movil
            },
            "transferencia": {
                "banco": config.banco_transferencia,
                "cuenta": config.cuenta_transferencia
            },
            "zelle": config.correo_zelle,
            "binance": config.correo_binance
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error obteniendo config pago: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/pago")
def actualizar_config_pago(
    request: ConfigPagoUpdate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_admin)
):
    """Actualizar métodos de pago."""
    try:
        config = db.query(ConfiguracionPago).first()
        if not config:
            config = ConfiguracionPago()
            db.add(config)
        
        if request.banco_pago_movil is not None:
            config.banco_pago_movil = request.banco_pago_movil
        if request.telefono_pago_movil is not None:
            config.telefono_pago_movil = request.telefono_pago_movil
        if request.cedula_pago_movil is not None:
            config.cedula_pago_movil = request.cedula_pago_movil
        if request.banco_transferencia is not None:
            config.banco_transferencia = request.banco_transferencia
        if request.cuenta_transferencia is not None:
            config.cuenta_transferencia = request.cuenta_transferencia
        if request.correo_zelle is not None:
            config.correo_zelle = request.correo_zelle
        if request.correo_binance is not None:
            config.correo_binance = request.correo_binance
        
        db.commit()
        
        logger.info(f"✅ Configuración de pagos actualizada por {current_user.username}")
        return {"success": True, "mensaje": "Configuración de pagos actualizada"}
    except Exception as e:
        logger.error(f"❌ Error actualizando config pago: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))