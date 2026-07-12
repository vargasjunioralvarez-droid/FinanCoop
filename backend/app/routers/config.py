# app/routers/config.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime
import logging
from app.database import get_db
from app.models import TasaDolar, NivelConfig, Financiamiento
from app.schemas import TasaUpdate, NivelConfigUpdate
from app.utils import obtener_tasa_actual, recalcular_cuotas_pendientes, get_niveles_config, init_niveles_db
from app.config import NIVELES_CONFIG

# Configurar logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/config", tags=["Configuración"])

@router.get("/tasa-dolar")
def obtener_tasa(db: Session = Depends(get_db)):
    """Obtener la tasa de cambio actual y su historial"""
    logger.info("=" * 50)
    logger.info("🔍 [tasa-dolar] INICIO")
    
    try:
        # 1. Obtener tasa actual
        logger.info("📡 [tasa-dolar] Obteniendo tasa actual...")
        tasa = obtener_tasa_actual(db)
        logger.info(f"✅ [tasa-dolar] Tasa actual: {tasa}")
        
        # 2. Obtener historial
        logger.info("📡 [tasa-dolar] Obteniendo historial...")
        historial = db.query(TasaDolar).order_by(TasaDolar.id.desc()).limit(10).all()
        logger.info(f"✅ [tasa-dolar] Historial obtenido: {len(historial)} registros")
        
        # 3. Construir respuesta
        response = {
            "tasa": tasa,
            "fecha": datetime.now().isoformat(),
            "historial": []
        }
        
        for h in historial:
            try:
                item = {
                    "tasa": h.tasa,
                    "fuente": h.fuente if hasattr(h, 'fuente') else "manual"
                }
                # Verificar si tiene fecha
                if hasattr(h, 'fecha') and h.fecha:
                    item["fecha"] = h.fecha.isoformat()
                elif hasattr(h, 'fecha_actualizacion') and h.fecha_actualizacion:
                    item["fecha"] = h.fecha_actualizacion.isoformat()
                else:
                    item["fecha"] = None
                
                response["historial"].append(item)
            except Exception as e:
                logger.error(f"❌ [tasa-dolar] Error procesando historial item: {e}")
                continue
        
        logger.info(f"✅ [tasa-dolar] Respuesta construida: {response}")
        logger.info("=" * 50)
        return response
        
    except Exception as e:
        logger.error(f"❌ [tasa-dolar] ERROR: {e}")
        logger.error(f"❌ [tasa-dolar] Tipo de error: {type(e)}")
        import traceback
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))