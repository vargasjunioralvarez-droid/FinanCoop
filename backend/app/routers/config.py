# routers/config.py
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import TasaDolar, NivelConfig, Financiamiento
from app.models import TasaDolar, NivelConfig
from app.schemas import TasaUpdate, NivelConfigUpdate
from app.utils import obtener_tasa_actual, recalcular_cuotas_pendientes, get_niveles_config, init_niveles_db
from datetime import datetime

router = APIRouter(prefix="/config", tags=["Configuración"])

@router.get("/tasa-dolar")
def obtener_tasa(db: Session = Depends(get_db)):
    tasa = obtener_tasa_actual(db)
    historial = db.query(TasaDolar).order_by(TasaDolar.id.desc()).limit(10).all()
    
    return {
        "tasa": tasa,
        "fecha": datetime.now().isoformat(),
        "historial": [
            {
                "tasa": h.tasa,
                "fecha": h.fecha_actualizacion.isoformat() if h.fecha_actualizacion else None,
                "fuente": h.fuente,
                "actualizado_por": h.actualizado_por
            } for h in historial
        ]
    }

@router.post("/tasa-dolar")
def actualizar_tasa_manual(tasa_update: TasaUpdate, db: Session = Depends(get_db)):
    nueva_tasa = tasa_update.tasa
    
    tasa = TasaDolar(
        tasa=nueva_tasa, 
        fuente="manual", 
        actualizado_por=tasa_update.actualizado_por
    )
    db.add(tasa)
    db.commit()
    
    recalculados = recalcular_cuotas_pendientes(db, nueva_tasa)
    
    return {
        "mensaje": f"Tasa actualizada a {nueva_tasa} BS/$",
        "tasa": nueva_tasa,
        "fuente": "manual",
        "financiamientos_afectados": db.query(Financiamiento).filter(
            Financiamiento.estado == "activo"
        ).count(),
        "cuotas_recalculadas": recalculados
    }

@router.get("/historial-tasas")
def historial_tasas(db: Session = Depends(get_db)):
    tasas = db.query(TasaDolar).order_by(TasaDolar.id.desc()).limit(50).all()
    return [
        {
            "id": t.id,
            "tasa": t.tasa,
            "fecha_actualizacion": t.fecha_actualizacion.isoformat() if t.fecha_actualizacion else None,
            "fuente": t.fuente,
            "actualizado_por": t.actualizado_por
        } for t in tasas
    ]

@router.get("/niveles")
def obtener_niveles(db: Session = Depends(get_db)):
    niveles = get_niveles_config(db)
    return {
        "niveles": niveles,
        "tasa_actual": obtener_tasa_actual(db)
    }

@router.put("/niveles/{nivel}")
def actualizar_nivel(nivel: str, config: NivelConfigUpdate, db: Session = Depends(get_db)):
    nc = db.query(NivelConfig).filter(NivelConfig.nivel == nivel).first()
    if not nc:
        raise HTTPException(status_code=404, detail="Nivel no encontrado")
    
    nc.monto_max_usd = config.monto_max_usd
    nc.entrada_pct = config.entrada_pct
    nc.financia_pct = config.financia_pct
    nc.cuotas_base = config.cuotas_base
    nc.cuotas_max = config.cuotas_max
    nc.mora_diaria = config.mora_diaria
    nc.aprobacion_extra = config.aprobacion_extra
    
    db.commit()
    get_niveles_config(db)
    
    return {"mensaje": f"Nivel {nivel} actualizado", "config": NIVELES_CONFIG[nivel]}

@router.post("/niveles/reset")
def reset_niveles(db: Session = Depends(get_db)):
    db.query(NivelConfig).delete()
    db.commit()
    init_niveles_db(db)
    get_niveles_config(db)
    return {"mensaje": "Niveles restaurados a valores por defecto"}