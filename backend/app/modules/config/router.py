# backend/app/modules/config/router.py
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session
from datetime import datetime, timezone
import logging
import httpx

from app.core.database import get_db
from app.modules.config.models import TasaDolar, NivelConfig
from app.modules.payments.models import ConfiguracionPago
from app.modules.loans.models import Financiamiento, Cuota
from app.modules.config.schemas import TasaUpdate, NivelConfigUpdate
from app.core.security import get_current_admin
from app.shared.utils import obtener_tasa_actual, get_niveles_config
from app.core.config import NIVELES_CONFIG_DEFAULT
from app.core.audit import audit, registrar_auditoria  # ✅ NUEVO

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
        raise HTTPException(status_code=500, detail="Error interno del servidor")

@router.post("/tasa-dolar")
@audit(accion="ACTUALIZAR_TASA", tabla="tasa_dolar")  # ✅ NUEVO
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
                        c.monto_total_bs = float(c.monto_base_usd) * float(request.tasa)  # ✅ float * float = OK
                        if c.monto_interes_mora_usd:
                            c.monto_interes_mora_bs = c.monto_interes_mora_usd * request.tasa
                        cuotas_recalculadas += 1
        
        db.commit()
        
        logger.info(f"✅ Tasa actualizada a {request.tasa} por {request.actualizado_por}")
        
        # ✅ NUEVO: Registrar auditoría manual
        registrar_auditoria(
            db=db,
            usuario_id=current_user.id,
            usuario_nombre=current_user.nombre,
            usuario_rol=current_user.rol,
            accion="ACTUALIZAR_TASA",
            tabla="tasa_dolar",
            registro_id=nueva_tasa.id,
            detalles=f"Tasa actualizada a {request.tasa} BS/USD, {financiamientos_afectados} financiamientos afectados"
        )
        
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
        raise HTTPException(status_code=500, detail="Error interno del servidor")

@router.post("/tasa-dolar/bcv")
@audit(accion="ACTUALIZAR_TASA_BCV", tabla="tasa_dolar")  # ✅ NUEVO
async def actualizar_tasa_bcv(db: Session = Depends(get_db), current_user = Depends(get_current_admin)):
    """Consultar tasa del BCV y actualizar automáticamente."""
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.get("https://bcv-api.deno.dev/v1/rates")
            if response.status_code != 200:
                raise HTTPException(status_code=500, detail="No se pudo consultar el BCV")
            
            data = response.json()
            tasa_bcv = data.get("rates", {}).get("USD", 0)
            
            if not tasa_bcv or tasa_bcv <= 0:
                raise HTTPException(status_code=500, detail="Tasa BCV no válida")
        
        nueva_tasa = TasaDolar(
            tasa=float(tasa_bcv),
            fuente="bcv",
            actualizado_por="auto"
        )
        db.add(nueva_tasa)
        
        # Recalcular cuotas pendientes
        financiamientos = db.query(Financiamiento).filter(
            Financiamiento.estado == "activo"
        ).all()
        
        for f in financiamientos:
            cuotas_pendientes = db.query(Cuota).filter(
                Cuota.financiamiento_id == f.id,
                Cuota.estado.in_(["pendiente", "conciliando"])
            ).all()
            
            for c in cuotas_pendientes:
                if c.monto_base_usd:
                    c.monto_total_bs = c.monto_base_usd * tasa_bcv
                    if c.monto_interes_mora_usd:
                        c.monto_interes_mora_bs = c.monto_interes_mora_usd * tasa_bcv
        
        db.commit()
        
        logger.info(f"✅ Tasa BCV actualizada automáticamente: {tasa_bcv} BS/$")
        
        # ✅ NUEVO: Registrar auditoría manual
        registrar_auditoria(
            db=db,
            usuario_id=current_user.id,
            usuario_nombre=current_user.nombre,
            usuario_rol=current_user.rol,
            accion="ACTUALIZAR_TASA_BCV",
            tabla="tasa_dolar",
            registro_id=nueva_tasa.id,
            detalles=f"Tasa BCV actualizada a {tasa_bcv} BS/USD"
        )
        
        return {
            "success": True,
            "tasa": tasa_bcv,
            "mensaje": f"Tasa BCV actualizada: {tasa_bcv} BS/$"
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error consultando BCV: {e}")
        raise HTTPException(status_code=500, detail="Error interno del servidor")

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
        raise HTTPException(status_code=500, detail="Error interno del servidor")

@router.put("/niveles/{nivel}")
@audit(accion="ACTUALIZAR_NIVEL", tabla="niveles_config")  # ✅ NUEVO
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
        
        if request.entrada_pct + request.financia_pct != 100:
            raise HTTPException(
                status_code=400, 
                detail=f"La suma de entrada ({request.entrada_pct}%) + financiamiento ({request.financia_pct}%) debe ser 100%"
            )
        
        # Guardar datos antes
        datos_antes = {
            "monto_max_usd": config.monto_max_usd,
            "entrada_pct": config.entrada_pct,
            "financia_pct": config.financia_pct,
            "cuotas_base": config.cuotas_base,
            "cuotas_max": config.cuotas_max,
            "mora_diaria": config.mora_diaria,
            "aprobacion_extra": config.aprobacion_extra
        }
        
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
        
        # ✅ NUEVO: Registrar auditoría manual
        registrar_auditoria(
            db=db,
            usuario_id=current_user.id,
            usuario_nombre=current_user.nombre,
            usuario_rol=current_user.rol,
            accion="ACTUALIZAR_NIVEL",
            tabla="niveles_config",
            registro_id=config.id,
            datos_antes=datos_antes,
            detalles=f"Nivel '{nivel}' actualizado por {current_user.nombre}"
        )
        
        return {"success": True, "mensaje": f"Nivel '{nivel}' actualizado correctamente"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error actualizando nivel: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail="Error interno del servidor")

@router.post("/niveles/reset")
@audit(accion="RESET_NIVELES", tabla="niveles_config")  # ✅ NUEVO
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
        
        # ✅ NUEVO: Registrar auditoría manual
        registrar_auditoria(
            db=db,
            usuario_id=current_user.id,
            usuario_nombre=current_user.nombre,
            usuario_rol=current_user.rol,
            accion="RESET_NIVELES",
            tabla="niveles_config",
            detalles=f"Niveles restaurados a valores por defecto por {current_user.nombre}"
        )
        
        return {"success": True, "mensaje": "Niveles restaurados a valores por defecto"}
    except Exception as e:
        logger.error(f"❌ Error reseteando niveles: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail="Error interno del servidor")

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
        raise HTTPException(status_code=500, detail="Error interno del servidor")

@router.put("/pago")
@audit(accion="ACTUALIZAR_CONFIG_PAGO", tabla="configuracion_pago")  # ✅ NUEVO
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
        
        # Guardar datos antes
        datos_antes = {
            "banco_pago_movil": config.banco_pago_movil,
            "telefono_pago_movil": config.telefono_pago_movil,
            "cedula_pago_movil": config.cedula_pago_movil,
            "banco_transferencia": config.banco_transferencia,
            "cuenta_transferencia": config.cuenta_transferencia,
            "correo_zelle": config.correo_zelle,
            "correo_binance": config.correo_binance
        }
        
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
        
        # ✅ NUEVO: Registrar auditoría manual
        registrar_auditoria(
            db=db,
            usuario_id=current_user.id,
            usuario_nombre=current_user.nombre,
            usuario_rol=current_user.rol,
            accion="ACTUALIZAR_CONFIG_PAGO",
            tabla="configuracion_pago",
            registro_id=config.id,
            datos_antes=datos_antes,
            detalles=f"Configuración de pagos actualizada por {current_user.nombre}"
        )
        
        return {"success": True, "mensaje": "Configuración de pagos actualizada"}
    except Exception as e:
        logger.error(f"❌ Error actualizando config pago: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail="Error interno del servidor")