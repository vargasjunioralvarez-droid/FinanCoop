# backend/app/domain/conciliacion.py
"""
🧾 Lógica de dominio: Procesamiento de conciliación de pagos.
Centraliza la lógica duplicada entre payments/router.py y banks/router.py.
"""

import logging
from datetime import datetime, timezone

from sqlalchemy.orm import Session
from app.modules.loans.models import Cuota, Financiamiento
from app.modules.payments.models import Pago
from app.modules.users.models import Cliente
from app.shared.utils import actualizar_score_cliente

logger = logging.getLogger(__name__)


def procesar_cuota_pagada(
    db: Session,
    pago: Pago,
    cuota: Cuota,
    monto_confirmado: float,
    conciliado_por: str
) -> dict:
    """
    Marca una cuota como pagada, actualiza el pago, verifica si el
    financiamiento se completa y actualiza el score del cliente.
    
    Retorna un dict con:
    - financiamiento_completado: bool
    - score_actualizado: int (si aplica)
    - nivel_actual: str (si aplica)
    """
    # Marcar pago como conciliado
    pago.monto_confirmado_bs = monto_confirmado
    pago.estado = "conciliado"
    pago.conciliado_por = conciliado_por
    pago.fecha_confirmacion = datetime.now(timezone.utc)

    # Marcar cuota como pagada
    cuota.estado = "pagada"
    cuota.fecha_pago = datetime.now(timezone.utc)
    cuota.monto_pagado = monto_confirmado

    # Verificar si el financiamiento se completa
    fin = db.query(Financiamiento).filter(Financiamiento.id == pago.financiamiento_id).first()
    financiamiento_completado = False
    score_actualizado = None
    nivel_actual = None

    if fin:
        cuotas_pendientes = db.query(Cuota).filter(
            Cuota.financiamiento_id == fin.id,
            Cuota.estado.in_(["pendiente", "conciliando"])
        ).count()

        if cuotas_pendientes == 0:
            fin.estado = "completado"
            fin.fecha_completado = datetime.now(timezone.utc)
            financiamiento_completado = True
            logger.info(f"✅ Financiamiento {fin.codigo} completado")

        # Actualizar score del cliente
        cliente = db.query(Cliente).filter(Cliente.id == fin.cliente_id).first()
        if cliente:
            actualizar_score_cliente(cliente, db)
            db.refresh(cliente)
            score_actualizado = cliente.score
            nivel_actual = cliente.nivel

    db.commit()

    return {
        "financiamiento_completado": financiamiento_completado,
        "score_actualizado": score_actualizado,
        "nivel_actual": nivel_actual
    }