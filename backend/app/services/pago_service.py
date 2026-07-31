# backend/app/services/pago_service.py
"""
Servicio de aplicación para la gestión de pagos.
"""

import json
import logging
from datetime import datetime, timezone
from sqlalchemy.orm import Session

from app.modules.loans.models import Cuota, Financiamiento
from app.modules.payments.models import Pago
from app.domain.conciliacion import procesar_cuota_pagada
from app.core.audit import registrar_auditoria

logger = logging.getLogger(__name__)


class PagoService:
    """Servicio para reportar y conciliar pagos."""

    @staticmethod
    def reportar(
        db: Session,
        cuota_id: int,
        monto_bs: float,
        metodo: str,
        referencia: str,
        banco_origen: str = "",
        telefono_pago: str = "",
        cedula_pago: str = "",
        comprobante: str = "",
        modo_pago: str = "cuota",
        cuotas_incluidas: list = None
    ) -> dict:
        """
        Reporta un pago para una cuota.
        Retorna un diccionario con el resultado.
        """
        cuota = db.query(Cuota).filter(Cuota.id == cuota_id).first()
        if not cuota:
            raise ValueError("Cuota no encontrada")

        if cuota.estado == "pagada":
            raise ValueError("Esta cuota ya fue pagada")

        pago_existente = db.query(Pago).filter(
            Pago.cuota_id == cuota_id,
            Pago.estado == "pendiente"
        ).first()
        if pago_existente:
            raise ValueError(f"Ya existe un pago pendiente para esta cuota (ID: {pago_existente.id})")

        if cuotas_incluidas is None:
            cuotas_incluidas = [cuota_id]

        # Manejo de abono
        if modo_pago == 'abono':
            total_cuota = cuota.monto_total_bs
            if monto_bs >= total_cuota:
                raise ValueError("El monto del abono debe ser menor al total de la cuota")

            nuevo_pago = Pago(
                cuota_id=cuota_id,
                financiamiento_id=cuota.financiamiento_id,
                referencia=referencia,
                metodo=metodo,
                monto_reportado_bs=monto_bs,
                banco_origen=banco_origen,
                telefono_pago=telefono_pago,
                cedula_pago=cedula_pago,
                comprobante=comprobante,
                estado="pendiente",
                fecha_reporte=datetime.now(timezone.utc),
                modo_pago=modo_pago,
                cuotas_incluidas=json.dumps(cuotas_incluidas),
                monto_original_bs=total_cuota
            )
            db.add(nuevo_pago)
            cuota.estado = "conciliando"
            db.commit()
            db.refresh(nuevo_pago)

            return {
                "success": True,
                "pago_id": nuevo_pago.id,
                "estado": "pendiente",
                "modo_pago": modo_pago,
                "monto_abonado": monto_bs,
                "monto_total": total_cuota,
                "saldo_pendiente": round(total_cuota - monto_bs, 2),
                "mensaje": f"Abono de Bs {monto_bs:,.2f} reportado."
            }

        # Pago completo
        nuevo_pago = Pago(
            cuota_id=cuota_id,
            financiamiento_id=cuota.financiamiento_id,
            referencia=referencia,
            metodo=metodo,
            monto_reportado_bs=monto_bs,
            banco_origen=banco_origen,
            telefono_pago=telefono_pago,
            cedula_pago=cedula_pago,
            comprobante=comprobante,
            estado="pendiente",
            fecha_reporte=datetime.now(timezone.utc),
            modo_pago=modo_pago,
            cuotas_incluidas=json.dumps(cuotas_incluidas)
        )
        db.add(nuevo_pago)
        cuota.estado = "conciliando"
        db.commit()
        db.refresh(nuevo_pago)

        logger.info(f"✅ Pago reportado ID: {nuevo_pago.id}")

        return {
            "success": True,
            "pago_id": nuevo_pago.id,
            "estado": "pendiente",
            "modo_pago": modo_pago,
            "mensaje": f"Pago reportado ({modo_pago}). Esperando conciliación."
        }

    @staticmethod
    def conciliar(
        db: Session,
        pago: Pago,
        cuota: Cuota,
        monto_confirmado: float,
        conciliado_por: str,
        admin_id: int = None,
        admin_nombre: str = None,
        admin_rol: str = None
    ) -> dict:
        """
        Concilia un pago completo (no abono).
        Actualiza el estado del pago, la cuota y el financiamiento.
        """
        resultado = procesar_cuota_pagada(
            db=db,
            pago=pago,
            cuota=cuota,
            monto_confirmado=monto_confirmado,
            conciliado_por=conciliado_por
        )

        # Conciliar pagos hijos
        pagos_hijos = db.query(Pago).filter(Pago.pago_padre_id == pago.id).all()
        for ph in pagos_hijos:
            ph.estado = "conciliado"
            ph.fecha_confirmacion = datetime.now(timezone.utc)
            ph.conciliado_por = conciliado_por
            ph.monto_confirmado_bs = ph.monto_reportado_bs

            cuota_hija = db.query(Cuota).filter(Cuota.id == ph.cuota_id).first()
            if cuota_hija:
                cuota_hija.estado = "pagada"
                cuota_hija.fecha_pago = datetime.now(timezone.utc)
                cuota_hija.monto_pagado = ph.monto_reportado_bs

        db.commit()

        # Auditoría
        registrar_auditoria(
            db=db,
            usuario_id=admin_id,
            usuario_nombre=admin_nombre,
            usuario_rol=admin_rol,
            accion="CONCILIAR",
            tabla="pagos",
            registro_id=pago.id,
            detalles=f"Pago #{pago.id} conciliado por {admin_nombre}"
        )

        if resultado["financiamiento_completado"]:
            registrar_auditoria(
                db=db,
                usuario_id=admin_id,
                usuario_nombre=admin_nombre,
                usuario_rol=admin_rol,
                accion="COMPLETAR_FINANCIAMIENTO",
                tabla="financiamientos",
                registro_id=pago.financiamiento_id,
                detalles="Financiamiento completado al conciliar última cuota"
            )

        return {
            "success": True,
            "estado": "conciliado",
            "cuota_pagada": cuota.numero,
            "cuotas_adicionales": len(pagos_hijos),
            "monto_bs": monto_confirmado,
            "score_actualizado": resultado["score_actualizado"],
            "nivel_actual": resultado["nivel_actual"],
            "mensaje": "Pago conciliado correctamente"
        }

    @staticmethod
    def conciliar_abono(
        db: Session,
        pago: Pago,
        cuota: Cuota,
        monto_confirmado: float
    ) -> dict:
        """
        Registra la conciliación de un abono.
        La cuota permanece pendiente hasta completar el monto total.
        """
        cuota.monto_pagado = (cuota.monto_pagado or 0) + monto_confirmado
        cuota.estado = "pendiente"
        db.commit()

        return {
            "success": True,
            "estado": "conciliado",
            "modo_pago": "abono",
            "cuota_pagada": cuota.numero,
            "monto_abonado": monto_confirmado,
            "monto_total_pagado": cuota.monto_pagado,
            "monto_total_cuota": cuota.monto_total_bs,
            "saldo_pendiente": round(cuota.monto_total_bs - cuota.monto_pagado, 2),
            "mensaje": f"Abono de Bs {monto_confirmado:,.2f} conciliado"
        }