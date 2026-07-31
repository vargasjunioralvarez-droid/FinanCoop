from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session
from datetime import datetime, timezone
from typing import Optional
import json
import logging

from app.core.database import get_db
from app.modules.loans.models import Cuota, Financiamiento
from app.modules.payments.models import Pago
from app.modules.users.models import Cliente
from app.modules.payments.schemas import PagoReporte, ConciliacionPago
from app.shared.utils import (
    actualizar_score_cliente,
    calcular_nivel,
    obtener_tasa_actual,
    enviar_notificacion_generica
)
from app.core.security import get_current_admin, get_current_user, get_current_tienda
from app.core.audit import audit, registrar_auditoria

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/pagos", tags=["Pagos"])


@router.post("/reportar")
@audit(accion="REPORTAR_PAGO", tabla="pagos")
async def reportar_pago(
    pago_data: PagoReporte,  # ✅ FastAPI valida automáticamente
    request: Request,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Reporta un pago realizado por el cliente. Requiere sesión activa."""
    try:
        logger.info(f"📝 Reportar pago - Usuario: {getattr(current_user, 'username', current_user.id)}")

        # Leer el body para obtener campos adicionales que no están en PagoReporte
        body = await request.body()
        try:
            extra_data = json.loads(body)
        except json.JSONDecodeError:
            raise HTTPException(status_code=400, detail="JSON inválido en el cuerpo de la solicitud")

        cuota = db.query(Cuota).filter(Cuota.id == pago_data.cuota_id).first()
        if not cuota:
            raise HTTPException(status_code=404, detail="Cuota no encontrada")

        financiamiento = db.query(Financiamiento).filter(Financiamiento.id == cuota.financiamiento_id).first()
        if not financiamiento:
            raise HTTPException(status_code=404, detail="Financiamiento no encontrado")

        if current_user.rol == "cliente":
            if financiamiento.cliente_id != current_user.id:
                raise HTTPException(status_code=403, detail="No tienes permiso para reportar pagos de otro cliente")
        else:
            if current_user.rol != "admin_central" and current_user.tienda_id:
                if financiamiento.tienda_id != current_user.tienda_id:
                    raise HTTPException(status_code=403, detail="El financiamiento no pertenece a tu tienda")

        if cuota.estado == "pagada":
            raise HTTPException(status_code=400, detail="Esta cuota ya fue pagada")

        pago_existente = db.query(Pago).filter(
            Pago.cuota_id == pago_data.cuota_id,
            Pago.estado == "pendiente"
        ).first()
        if pago_existente:
            raise HTTPException(
                status_code=409,
                detail=f"Ya existe un pago pendiente para esta cuota (ID: {pago_existente.id})"
            )

        cuotas_incluidas_raw = extra_data.get('cuotas_incluidas', [pago_data.cuota_id])
        modo_pago = extra_data.get('modo_pago', 'cuota')
        monto_original = extra_data.get('monto_original')

        if isinstance(cuotas_incluidas_raw, str):
            try:
                cuotas_incluidas = json.loads(cuotas_incluidas_raw)
            except:
                cuotas_incluidas = [pago_data.cuota_id]
        else:
            cuotas_incluidas = cuotas_incluidas_raw if isinstance(cuotas_incluidas_raw, list) else [pago_data.cuota_id]

        logger.info(f"📋 Modo de pago: {modo_pago}, Cuotas: {cuotas_incluidas}")

        if modo_pago == 'abono':
            total_cuota = monto_original or cuota.monto_total_bs
            if pago_data.monto_bs >= total_cuota:
                raise HTTPException(
                    status_code=400,
                    detail="El monto del abono debe ser menor al total de la cuota. Use 'Pagar cuota completa'"
                )

            nuevo_pago = Pago(
                cuota_id=pago_data.cuota_id,
                financiamiento_id=cuota.financiamiento_id,
                referencia=pago_data.referencia,
                metodo=pago_data.metodo,
                monto_reportado_bs=pago_data.monto_bs,
                banco_origen=pago_data.banco_origen,
                telefono_pago=pago_data.telefono_pago,
                cedula_pago=pago_data.cedula_pago,
                comprobante=pago_data.comprobante,
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
                "monto_abonado": pago_data.monto_bs,
                "monto_total": total_cuota,
                "saldo_pendiente": round(total_cuota - pago_data.monto_bs, 2),
                "mensaje": f"Abono de Bs {pago_data.monto_bs:,.2f} reportado. Saldo pendiente: Bs {round(total_cuota - pago_data.monto_bs, 2):,.2f}"
            }

        nuevo_pago = Pago(
            cuota_id=pago_data.cuota_id,
            financiamiento_id=cuota.financiamiento_id,
            referencia=pago_data.referencia,
            metodo=pago_data.metodo,
            monto_reportado_bs=pago_data.monto_bs,
            banco_origen=pago_data.banco_origen,
            telefono_pago=pago_data.telefono_pago,
            cedula_pago=pago_data.cedula_pago,
            comprobante=pago_data.comprobante,
            estado="pendiente",
            fecha_reporte=datetime.now(timezone.utc),
            modo_pago=modo_pago,
            cuotas_incluidas=json.dumps(cuotas_incluidas)
        )
        db.add(nuevo_pago)
        cuota.estado = "conciliando"

        pagos_creados = 1
        for cid in cuotas_incluidas:
            if cid == pago_data.cuota_id:
                continue

            cuota_extra = db.query(Cuota).filter(Cuota.id == cid).first()
            if cuota_extra and cuota_extra.estado == 'pendiente':
                fin_extra = db.query(Financiamiento).filter(Financiamiento.id == cuota_extra.financiamiento_id).first()
                if current_user.rol == "cliente" and fin_extra.cliente_id != current_user.id:
                    continue
                if current_user.rol != "admin_central" and current_user.tienda_id and fin_extra.tienda_id != current_user.tienda_id:
                    continue

                pago_extra = Pago(
                    cuota_id=cid,
                    financiamiento_id=cuota_extra.financiamiento_id,
                    referencia=pago_data.referencia + f"-C{cid}",
                    metodo=pago_data.metodo,
                    monto_reportado_bs=cuota_extra.monto_total_bs,
                    monto=cuota_extra.monto_total_bs,
                    banco_origen=pago_data.banco_origen,
                    telefono_pago=pago_data.telefono_pago,
                    cedula_pago=pago_data.cedula_pago,
                    comprobante=pago_data.comprobante,
                    estado="pendiente",
                    fecha_reporte=datetime.now(timezone.utc),
                    modo_pago=modo_pago,
                    pago_padre_id=nuevo_pago.id,
                    cuotas_incluidas=json.dumps([cid])
                )
                db.add(pago_extra)
                cuota_extra.estado = "conciliando"
                pagos_creados += 1

        db.commit()
        db.refresh(nuevo_pago)

        logger.info(f"✅ Pago reportado ID: {nuevo_pago.id}, Cuotas afectadas: {pagos_creados}")

        return {
            "success": True,
            "pago_id": nuevo_pago.id,
            "estado": "pendiente",
            "modo_pago": modo_pago,
            "cuotas_afectadas": pagos_creados,
            "mensaje": f"Pago reportado ({modo_pago}). Esperando conciliación."
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error reportando pago: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail="Error interno del servidor")


@router.get("/pendientes")
def pagos_pendientes_conciliacion(
    db: Session = Depends(get_db),
    current_admin = Depends(get_current_admin),
    tienda_id: Optional[int] = Depends(get_current_tienda)
):
    """Lista pagos pendientes de conciliación con una sola consulta optimizada."""
    try:
        # Obtener la tasa UNA SOLA VEZ
        tasa = obtener_tasa_actual(db)

        # Consulta base con JOINs para traer todo en una sola ida a la BD
        query = db.query(Pago, Cuota, Financiamiento, Cliente).join(
            Cuota, Pago.cuota_id == Cuota.id, isouter=True
        ).join(
            Financiamiento, Pago.financiamiento_id == Financiamiento.id
        ).join(
            Cliente, Financiamiento.cliente_id == Cliente.id
        ).filter(Pago.estado == "pendiente")

        # Filtrar por tienda si aplica
        if tienda_id:
            query = query.filter(Financiamiento.tienda_id == tienda_id)

        resultados = query.order_by(Pago.fecha_reporte.desc()).all()

        pagos_lista = []
        for pago, cuota, fin, cliente in resultados:
            monto_bs = p.monto_reportado_bs or 0
            monto_usd = round(monto_bs / tasa, 2) if tasa > 0 else 0

            cuotas_incl = []
            try:
                if pago.cuotas_incluidas:
                    cuotas_incl = json.loads(pago.cuotas_incluidas)
            except:
                pass

            pagos_lista.append({
                "id": pago.id,
                "fecha_reporte": pago.fecha_reporte.isoformat() if pago.fecha_reporte else None,
                "cliente_nombre": cliente.nombre if cliente else "Desconocido",
                "cliente_cedula": cliente.cedula if cliente else "",
                "cuota_numero": cuota.numero if cuota else 0,
                "cuota_id": pago.cuota_id,
                "monto_reportado_bs": monto_bs,
                "monto_reportado_usd": monto_usd,
                "metodo": pago.metodo,
                "referencia": pago.referencia,
                "banco_origen": pago.banco_origen,
                "telefono_pago": pago.telefono_pago,
                "comprobante": pago.comprobante,
                "estado": pago.estado,
                "modo_pago": pago.modo_pago or "cuota",
                "cuotas_incluidas": cuotas_incl,
                "es_pago_padre": pago.pago_padre_id is None,
                "monto_original_bs": pago.monto_original_bs,
                "tienda_nombre": fin.tienda.nombre if fin and fin.tienda else None
            })

        return {"total": len(pagos_lista), "pagos": pagos_lista}

    except Exception as e:
        logger.error(f"❌ Error listando pagos pendientes: {e}")
        raise HTTPException(status_code=500, detail="Error interno del servidor")


@router.post("/conciliar")
@audit(accion="CONCILIAR", tabla="pagos")
def conciliar_pago(
    conciliacion: ConciliacionPago,
    db: Session = Depends(get_db),
    current_admin = Depends(get_current_admin)
):
    try:
        logger.info(f"📝 Conciliando pago: {conciliacion.pago_id}")

        pago = db.query(Pago).filter(Pago.id == conciliacion.pago_id).first()
        if not pago:
            raise HTTPException(status_code=404, detail="Pago no encontrado")

        if pago.estado != "pendiente":
            raise HTTPException(status_code=400, detail="Este pago ya fue procesado")

        cuota = db.query(Cuota).filter(Cuota.id == pago.cuota_id).first()
        if not cuota:
            raise HTTPException(status_code=404, detail="Cuota no encontrada")

        fin = db.query(Financiamiento).filter(Financiamiento.id == pago.financiamiento_id).first()

        if conciliacion.estado == "conciliado":
            if pago.modo_pago == 'abono':
                cuota.monto_pagado = (cuota.monto_pagado or 0) + conciliacion.monto_confirmado_bs
                cuota.estado = "pendiente"
                db.commit()

                return {
                    "success": True,
                    "estado": "conciliado",
                    "modo_pago": "abono",
                    "cuota_pagada": cuota.numero,
                    "monto_abonado": conciliacion.monto_confirmado_bs,
                    "monto_total_pagado": cuota.monto_pagado,
                    "monto_total_cuota": cuota.monto_total_bs,
                    "saldo_pendiente": round(cuota.monto_total_bs - cuota.monto_pagado, 2),
                    "mensaje": f"Abono de Bs {conciliacion.monto_confirmado_bs:,.2f} conciliado"
                }

            # Pago completo - Usar la función centralizada
            from app.domain.conciliacion import procesar_cuota_pagada

            resultado = procesar_cuota_pagada(
                db=db,
                pago=pago,
                cuota=cuota,
                monto_confirmado=conciliacion.monto_confirmado_bs,
                conciliado_por=conciliacion.conciliado_por
            )

            pagos_hijos = db.query(Pago).filter(Pago.pago_padre_id == pago.id).all()
            for ph in pagos_hijos:
                ph.estado = "conciliado"
                ph.fecha_confirmacion = datetime.now(timezone.utc)
                ph.conciliado_por = conciliacion.conciliado_por
                ph.monto_confirmado_bs = ph.monto_reportado_bs

                cuota_hija = db.query(Cuota).filter(Cuota.id == ph.cuota_id).first()
                if cuota_hija:
                    cuota_hija.estado = "pagada"
                    cuota_hija.fecha_pago = datetime.now(timezone.utc)
                    cuota_hija.monto_pagado = ph.monto_reportado_bs

            db.commit()

            registrar_auditoria(
                db=db,
                usuario_id=current_admin.id,
                usuario_nombre=current_admin.nombre,
                usuario_rol=current_admin.rol,
                accion="CONCILIAR",
                tabla="pagos",
                registro_id=pago.id,
                detalles=f"Pago #{pago.id} conciliado por {current_admin.nombre}"
            )

            if resultado["financiamiento_completado"]:
                registrar_auditoria(
                    db=db,
                    usuario_id=current_admin.id,
                    usuario_nombre=current_admin.nombre,
                    usuario_rol=current_admin.rol,
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
                "monto_bs": conciliacion.monto_confirmado_bs,
                "score_actualizado": resultado["score_actualizado"],
                "nivel_actual": resultado["nivel_actual"],
                "mensaje": "Pago conciliado correctamente"
            }
        else:
            cuota.estado = "pendiente"
            pago.rechazado_por = conciliacion.conciliado_por
            pago.fecha_rechazo = datetime.now(timezone.utc)

            for ph in db.query(Pago).filter(Pago.pago_padre_id == pago.id).all():
                ph.estado = "rechazado"
                ph.fecha_rechazo = datetime.now(timezone.utc)
                ph.rechazado_por = conciliacion.conciliado_por

                cuota_hija = db.query(Cuota).filter(Cuota.id == ph.cuota_id).first()
                if cuota_hija:
                    cuota_hija.estado = "pendiente"

            db.commit()

            return {
                "success": True,
                "estado": "rechazado",
                "mensaje": "Pago rechazado. Cuota vuelve a pendiente."
            }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error conciliando pago: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail="Error interno del servidor")


@router.post("/cuotas/{id}/pagar-efectivo")
@audit(accion="PAGAR_EFECTIVO", tabla="cuotas")
def pagar_cuota_efectivo(
    id: int,
    db: Session = Depends(get_db),
    current_admin = Depends(get_current_admin)
):
    try:
        cuota = db.query(Cuota).filter(Cuota.id == id).first()
        if not cuota:
            raise HTTPException(status_code=404, detail="Cuota no encontrada")

        if cuota.estado == "pagada":
            raise HTTPException(status_code=400, detail="Esta cuota ya fue pagada")

        fin = db.query(Financiamiento).filter(Financiamiento.id == cuota.financiamiento_id).first()
        if not fin:
            raise HTTPException(status_code=404, detail="Financiamiento no encontrado")

        cliente = db.query(Cliente).filter(Cliente.id == fin.cliente_id).first()
        hoy = datetime.now(timezone.utc)

        # Forzar timezone en fecha_vencimiento si no la tiene (compatibilidad SQLite)
        if cuota.fecha_vencimiento and cuota.fecha_vencimiento.tzinfo is None:
            cuota.fecha_vencimiento = cuota.fecha_vencimiento.replace(tzinfo=timezone.utc)

        interes_bs = 0
        if hoy > cuota.fecha_vencimiento:
            dias_atraso = (hoy - cuota.fecha_vencimiento).days
            dias_gracia = 3
            if dias_atraso > dias_gracia and cliente:
                nivel, config = calcular_nivel(cliente.score)
                tasa_mora = config["mora_diaria"]
                dias_efectivos = dias_atraso - dias_gracia
                interes_bs = cuota.monto_base_bs * (tasa_mora / 100) * dias_efectivos
                cuota.monto_interes_mora_bs = round(interes_bs, 2)
                cuota.monto_total_bs = round(cuota.monto_base_bs + interes_bs, 2)
                if hasattr(cliente, 'cuotas_con_mora'):
                    cliente.cuotas_con_mora = (cliente.cuotas_con_mora or 0) + 1
        else:
            cuota.monto_total_bs = cuota.monto_base_bs

        from app.domain.conciliacion import procesar_cuota_pagada

        pago = Pago(
            cuota_id=cuota.id,
            financiamiento_id=fin.id,
            metodo="efectivo",
            monto_reportado_bs=cuota.monto_total_bs,
            monto_confirmado_bs=cuota.monto_total_bs,
            estado="conciliado",
            fecha_confirmacion=hoy,
            conciliado_por=current_admin.username if hasattr(current_admin, 'username') else "admin",
            modo_pago="cuota"
        )
        db.add(pago)
        db.flush()

        resultado = procesar_cuota_pagada(
            db=db,
            pago=pago,
            cuota=cuota,
            monto_confirmado=cuota.monto_total_bs,
            conciliado_por=current_admin.username if hasattr(current_admin, 'username') else "admin"
        )

        if resultado["financiamiento_completado"]:
            registrar_auditoria(
                db=db,
                usuario_id=current_admin.id,
                usuario_nombre=current_admin.nombre,
                usuario_rol=current_admin.rol,
                accion="COMPLETAR_FINANCIAMIENTO",
                tabla="financiamientos",
                registro_id=fin.id,
                detalles=f"Financiamiento #{fin.codigo} completado al pagar última cuota en efectivo"
            )

        return {
            "success": True,
            "cuota_pagada": cuota.numero,
            "monto_base_bs": cuota.monto_base_bs,
            "interes_mora_bs": cuota.monto_interes_mora_bs or 0,
            "total_pagado_bs": cuota.monto_total_bs,
            "score_actualizado": resultado["score_actualizado"],
            "nivel_actual": resultado["nivel_actual"],
            "financiamiento_estado": "completado" if resultado["financiamiento_completado"] else "activo"
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error pagando cuota en efectivo: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail="Error interno del servidor")