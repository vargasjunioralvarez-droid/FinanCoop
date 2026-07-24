# backend/app/routers/bancos.py
"""
🏦 Router para conciliación bancaria automática
Recibe notificaciones del banco y concilia pagos automáticamente
"""

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from datetime import datetime, timezone
from typing import Optional
import logging
import json

from app.core.database import get_db
from app.modules.payments.models import Pago
from app.modules.loans.models import Cuota, Financiamiento
from app.modules.users.models import Cliente
from app.shared.utils import actualizar_score_cliente, obtener_tasa_actual
from app.modules.config.models import LogsConciliacion

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/bancos", tags=["Conciliación Bancaria"])

# ============================================================
# MODELO Pydantic para el webhook del banco
# ============================================================
from pydantic import BaseModel

class PagoBancoWebhook(BaseModel):
    referencia: str
    monto: float
    banco_origen: Optional[str] = None
    telefono_origen: Optional[str] = None
    cedula_origen: Optional[str] = None
    fecha_pago: Optional[str] = None
    transaccion_id: Optional[str] = None

# ============================================================
# 📥 WEBHOOK: El banco notifica un pago
# ============================================================

@router.post("/webhook")
async def recibir_webhook_banco(
    request: Request,
    db: Session = Depends(get_db)
):
    """
    Endpoint que el banco llama cuando detecta un pago.
    Busca la referencia en pagos pendientes y concilia automáticamente.
    """
    try:
        # Leer el body que envía el banco
        body = await request.body()
        data = json.loads(body)
        
        logger.info(f"🏦 [Banco] Webhook recibido: {json.dumps(data, ensure_ascii=False)[:300]}")
        
        # Extraer datos
        referencia = str(data.get('referencia', '')).strip()
        monto_banco = float(data.get('monto', 0))
        banco_origen = data.get('banco_origen', data.get('banco', ''))
        telefono_origen = data.get('telefono_origen', data.get('telefono', ''))
        transaccion_id = data.get('transaccion_id', data.get('id', ''))
        
        if not referencia or monto_banco <= 0:
            logger.warning(f"🏦 [Banco] Datos inválidos: ref={referencia}, monto={monto_banco}")
            return {"status": "error", "mensaje": "Datos inválidos"}
        
        # 🔍 Buscar pago pendiente con esa referencia
        pago = db.query(Pago).filter(
            Pago.referencia == referencia,
            Pago.estado == "pendiente"
        ).first()
        
        if not pago:
            # Guardar en log para revisión manual
            guardar_log(db, referencia, monto_banco, 0, "no_encontrado", 
                       f"Referencia no encontrada. Transacción: {transaccion_id}")
            logger.warning(f"🏦 [Banco] Referencia '{referencia}' no encontrada en pagos pendientes")
            return {"status": "no_encontrado", "mensaje": "Referencia no encontrada"}
        
        # ✅ Verificar montos
        monto_reportado = pago.monto_reportado_bs or pago.monto or 0
        diferencia = abs(monto_banco - monto_reportado)
        
        if diferencia <= 1.0:  # Tolerancia de 1 Bs
            # ¡CONCILIAR AUTOMÁTICAMENTE!
            pago.monto_confirmado_bs = monto_banco
            pago.estado = "conciliado"
            pago.conciliado_por = "banco_automatico"
            pago.fecha_confirmacion = datetime.now(timezone.utc)
            
            # Marcar cuota como pagada
            cuota = db.query(Cuota).filter(Cuota.id == pago.cuota_id).first()
            if cuota:
                cuota.estado = "pagada"
                cuota.fecha_pago = datetime.now(timezone.utc)
                cuota.monto_pagado = monto_banco
                
                # Verificar si el financiamiento se completa
                fin = db.query(Financiamiento).filter(Financiamiento.id == pago.financiamiento_id).first()
                if fin:
                    cuotas_pendientes = db.query(Cuota).filter(
                        Cuota.financiamiento_id == fin.id,
                        Cuota.estado.in_(["pendiente", "conciliando"])
                    ).count()
                    
                    if cuotas_pendientes == 0:
                        fin.estado = "completado"
                        fin.fecha_completado = datetime.now(timezone.utc)
                        logger.info(f"✅ Financiamiento {fin.codigo} completado automáticamente")
                    
                    # Actualizar score del cliente
                    cliente = db.query(Cliente).filter(Cliente.id == fin.cliente_id).first()
                    if cliente:
                        actualizar_score_cliente(cliente, db)
            
            db.commit()
            
            guardar_log(db, referencia, monto_banco, monto_reportado, "conciliado",
                       f"Conciliado automáticamente. Transacción: {transaccion_id}")
            
            logger.info(f"✅ [Banco] Pago conciliado automáticamente: ref={referencia}, monto={monto_banco}")
            
            return {
                "status": "conciliado",
                "mensaje": "Pago conciliado automáticamente",
                "referencia": referencia,
                "monto": monto_banco
            }
        else:
            # Hay diferencia en montos - revisión manual
            guardar_log(db, referencia, monto_banco, monto_reportado, "diferencia",
                       f"Diferencia de {diferencia:.2f} Bs. Transacción: {transaccion_id}")
            
            logger.warning(f"⚠️ [Banco] Diferencia en montos: ref={referencia}, banco={monto_banco}, reportado={monto_reportado}")
            
            return {
                "status": "diferencia",
                "mensaje": f"Diferencia de {diferencia:.2f} Bs. Requiere revisión manual.",
                "monto_banco": monto_banco,
                "monto_reportado": monto_reportado
            }
    
    except json.JSONDecodeError:
        logger.error("🏦 [Banco] Error decodificando JSON del webhook")
        return {"status": "error", "mensaje": "JSON inválido"}
    except Exception as e:
        logger.error(f"🏦 [Banco] Error en webhook: {e}")
        db.rollback()
        return {"status": "error", "mensaje": str(e)}

# ============================================================
# 📊 CONSULTAR LOGS DE CONCILIACIÓN
# ============================================================

@router.get("/logs")
def ver_logs_conciliacion(
    skip: int = 0,
    limit: int = 50,
    estado: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Ver historial de conciliaciones bancarias"""
    from app.models import LogsConciliacion
    
    query = db.query(LogsConciliacion)
    
    if estado:
        query = query.filter(LogsConciliacion.estado == estado)
    
    total = query.count()
    logs = query.order_by(LogsConciliacion.id.desc()).offset(skip).limit(limit).all()
    
    return {
        "total": total,
        "logs": [
            {
                "id": l.id,
                "referencia": l.referencia,
                "monto_banco": l.monto_banco,
                "monto_reportado": l.monto_reportado,
                "estado": l.estado,
                "respuesta_banco": l.respuesta_banco,
                "fecha": l.fecha.isoformat() if l.fecha else None
            }
            for l in logs
        ]
    }

# ============================================================
# 🔄 CONCILIACIÓN MANUAL ASISTIDA
# ============================================================

@router.post("/conciliar-manual")
def conciliar_pago_manual(
    pago_id: int,
    db: Session = Depends(get_db)
):
    """Forzar conciliación manual de un pago"""
    pago = db.query(Pago).filter(Pago.id == pago_id).first()
    if not pago:
        raise HTTPException(status_code=404, detail="Pago no encontrado")
    
    pago.estado = "conciliado"
    pago.fecha_confirmacion = datetime.now(timezone.utc)
    pago.conciliado_por = "manual"
    
    cuota = db.query(Cuota).filter(Cuota.id == pago.cuota_id).first()
    if cuota:
        cuota.estado = "pagada"
        cuota.fecha_pago = datetime.now(timezone.utc)
    
    db.commit()
    
    return {"status": "conciliado", "mensaje": "Pago conciliado manualmente"}

# ============================================================
# 🛠️ FUNCIÓN AUXILIAR
# ============================================================

def guardar_log(db: Session, referencia: str, monto_banco: float, 
                monto_reportado: float, estado: str, respuesta: str):
    """Guarda un registro en logs_conciliacion"""
    from app.models import LogsConciliacion
    
    log = LogsConciliacion(
        referencia=referencia,
        monto_banco=monto_banco,
        monto_reportado=monto_reportado,
        estado=estado,
        respuesta_banco=respuesta,
        fecha=datetime.now(timezone.utc)
    )
    db.add(log)
    db.commit()