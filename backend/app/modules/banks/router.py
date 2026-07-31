"""
🏦 Router para conciliación bancaria automática
Recibe notificaciones del banco y concilia pagos automáticamente
"""

import os
import json
import logging
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.core.database import get_db
from app.modules.payments.models import Pago
from app.modules.loans.models import Cuota, Financiamiento
from app.modules.users.models import Cliente
from app.shared.utils import actualizar_score_cliente, obtener_tasa_actual
from app.modules.config.models import LogsConciliacion
from app.core.security import get_current_admin

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/bancos", tags=["Conciliación Bancaria"])

BANCO_WEBHOOK_SECRET = os.getenv("BANCO_WEBHOOK_SECRET", "")


class PagoBancoWebhook(BaseModel):
    referencia: str
    monto: float
    banco_origen: Optional[str] = None
    telefono_origen: Optional[str] = None
    cedula_origen: Optional[str] = None
    fecha_pago: Optional[str] = None
    transaccion_id: Optional[str] = None


@router.post("/webhook")
async def recibir_webhook_banco(
    data: PagoBancoWebhook,  # ✅ FastAPI valida automáticamente
    request: Request,
    db: Session = Depends(get_db)
):
    token_recibido = request.headers.get("X-Webhook-Token", "")
    if not BANCO_WEBHOOK_SECRET or token_recibido != BANCO_WEBHOOK_SECRET:
        logger.warning(f"🏦 [Banco] Intento de webhook no autorizado. Token: {token_recibido[:10]}...")
        return {"status": "ok", "mensaje": "Recibido"}

    try:
        logger.info(f"🏦 [Banco] Webhook recibido: {data.json()[:300]}")

        referencia = data.referencia.strip()
        monto_banco = data.monto
        banco_origen = data.banco_origen
        telefono_origen = data.telefono_origen
        transaccion_id = data.transaccion_id

        if not referencia or monto_banco <= 0:
            logger.warning(f"🏦 [Banco] Datos inválidos: ref={referencia}, monto={monto_banco}")
            return {"status": "error", "mensaje": "Datos inválidos"}

        pago = db.query(Pago).filter(
            Pago.referencia == referencia,
            Pago.estado == "pendiente"
        ).first()

        if not pago:
            guardar_log(db, referencia, monto_banco, 0, "no_encontrado",
                       f"Referencia no encontrada. Transacción: {transaccion_id}")
            logger.warning(f"🏦 [Banco] Referencia '{referencia}' no encontrada en pagos pendientes")
            return {"status": "no_encontrado", "mensaje": "Referencia no encontrada"}

        monto_reportado = pago.monto_reportado_bs or pago.monto or 0
        diferencia = abs(monto_banco - monto_reportado)

        if diferencia <= 1.0:
            from app.domain.conciliacion import procesar_cuota_pagada

            cuota = db.query(Cuota).filter(Cuota.id == pago.cuota_id).first()
            if cuota:
                resultado = procesar_cuota_pagada(
                    db=db,
                    pago=pago,
                    cuota=cuota,
                    monto_confirmado=monto_banco,
                    conciliado_por="banco_automatico"
                )

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
            guardar_log(db, referencia, monto_banco, monto_reportado, "diferencia",
                       f"Diferencia de {diferencia:.2f} Bs. Transacción: {transaccion_id}")

            logger.warning(f"⚠️ [Banco] Diferencia en montos: ref={referencia}, banco={monto_banco}, reportado={monto_reportado}")

            return {
                "status": "diferencia",
                "mensaje": f"Diferencia de {diferencia:.2f} Bs. Requiere revisión manual.",
                "monto_banco": monto_banco,
                "monto_reportado": monto_reportado
            }

    except Exception as e:
        logger.error(f"🏦 [Banco] Error en webhook: {e}")
        db.rollback()
        return {"status": "error", "mensaje": str(e)}


@router.get("/logs")
def ver_logs_conciliacion(
    skip: int = 0,
    limit: int = 50,
    estado: Optional[str] = None,
    db: Session = Depends(get_db)
):
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


@router.post("/conciliar-manual")
def conciliar_pago_manual(
    pago_id: int,
    db: Session = Depends(get_db),
    current_admin = Depends(get_current_admin)
):
    pago = db.query(Pago).filter(Pago.id == pago_id).first()
    if not pago:
        raise HTTPException(status_code=404, detail="Pago no encontrado")

    if current_admin.rol != "admin_central":
        financiamiento = db.query(Financiamiento).filter(Financiamiento.id == pago.financiamiento_id).first()
        if financiamiento and current_admin.tienda_id and financiamiento.tienda_id != current_admin.tienda_id:
            raise HTTPException(status_code=403, detail="El pago no pertenece a tu tienda")

    from app.domain.conciliacion import procesar_cuota_pagada

    cuota = db.query(Cuota).filter(Cuota.id == pago.cuota_id).first()
    if not cuota:
        raise HTTPException(status_code=404, detail="Cuota no encontrada")

    resultado = procesar_cuota_pagada(
        db=db,
        pago=pago,
        cuota=cuota,
        monto_confirmado=pago.monto_reportado_bs or pago.monto or 0,
        conciliado_por=current_admin.username if hasattr(current_admin, 'username') else "admin"
    )

    return {
        "status": "conciliado",
        "mensaje": "Pago conciliado manualmente",
        "financiamiento_completado": resultado["financiamiento_completado"]
    }


def guardar_log(db: Session, referencia: str, monto_banco: float,
                monto_reportado: float, estado: str, respuesta: str):
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