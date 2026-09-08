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
    pago_data: PagoReporte,
    request: Request,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Reporta un pago realizado por el cliente. Requiere sesión activa."""
    try:
        # ✅ Determinar tipo de usuario de forma segura
        es_cliente = not hasattr(current_user, 'rol')
        usuario_id = None if es_cliente else current_user.id
        usuario_nombre = getattr(current_user, 'nombre', getattr(current_user, 'username', 'desconocido'))
        usuario_rol = 'cliente' if es_cliente else current_user.rol
        
        logger.info(f"📝 Reportar pago - Usuario: {usuario_nombre} (rol: {usuario_rol})")

        # Leer el body para obtener campos adicionales
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

        # ✅ Verificar pertenencia de forma segura
        if es_cliente:
            # Es un Cliente (no un Usuario admin)
            if financiamiento.cliente_id != current_user.id:
                raise HTTPException(status_code=403, detail="No tienes permiso para reportar pagos de otro cliente")
        else:
            # Es un Usuario admin/tienda/cajero
            if current_user.rol != "admin_central" and current_user.tienda_id:
                if financiamiento.tienda_id != current_user.tienda_id:
                    raise HTTPException(status_code=403, detail="El financiamiento no pertenece a tu tienda")

        # Delegar al servicio
        from app.services.pago_service import PagoService

        modo_pago = extra_data.get('modo_pago', 'cuota')
        cuotas_incluidas_raw = extra_data.get('cuotas_incluidas', [pago_data.cuota_id])

        if isinstance(cuotas_incluidas_raw, str):
            try:
                cuotas_incluidas = json.loads(cuotas_incluidas_raw)
            except:
                cuotas_incluidas = [pago_data.cuota_id]
        else:
            cuotas_incluidas = cuotas_incluidas_raw if isinstance(cuotas_incluidas_raw, list) else [pago_data.cuota_id]

        resultado = PagoService.reportar(
            db=db,
            cuota_id=pago_data.cuota_id,
            monto_bs=pago_data.monto_bs,
            metodo=pago_data.metodo,
            referencia=pago_data.referencia,
            banco_origen=pago_data.banco_origen or "",
            telefono_pago=pago_data.telefono_pago or "",
            cedula_pago=pago_data.cedula_pago or "",
            comprobante=pago_data.comprobante or "",
            modo_pago=modo_pago,
            cuotas_incluidas=cuotas_incluidas
        )

        # ✅ Registrar auditoría manualmente (evitando el error del decorador)
        try:
            registrar_auditoria(
                db=db,
                usuario_id=usuario_id,
                usuario_nombre=usuario_nombre,
                usuario_rol=usuario_rol,
                accion="REPORTAR_PAGO",
                tabla="pagos",
                registro_id=resultado.get("pago_id") if isinstance(resultado, dict) else None,
                detalles=f"Pago reportado por {usuario_nombre} (rol: {usuario_rol})"
            )
        except Exception as audit_error:
            logger.error(f"⚠️ Error registrando auditoría: {audit_error}")

        return resultado

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
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
            monto_bs = pago.monto_reportado_bs or 0
            monto_usd = round(float(monto_bs) / float(tasa), 2) if float(tasa) > 0 else 0

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

        if conciliacion.estado == "conciliado":
            # Delegar al servicio de pagos
            from app.services.pago_service import PagoService

            if pago.modo_pago == 'abono':
                return PagoService.conciliar_abono(db, pago, cuota, conciliacion.monto_confirmado_bs)

            resultado = PagoService.conciliar(
                db=db,
                pago=pago,
                cuota=cuota,
                monto_confirmado=conciliacion.monto_confirmado_bs,
                conciliado_por=conciliacion.conciliado_por,
                admin_id=current_admin.id,
                admin_nombre=current_admin.nombre,
                admin_rol=current_admin.rol
            )

            return resultado
        else:
            # Rechazar pago
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

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
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


@router.post("/verificar-mercantil")
async def verificar_pago_mercantil(
    request: Request,
    db: Session = Depends(get_db),
    current_admin = Depends(get_current_admin)
):
    """
    Verifica automáticamente un pago con la API de Mercantil Banco.
    Busca la transacción por referencia y monto, y concilia automáticamente.
    """
    from app.services.mercantil_service import MercantilService
    
    try:
        body = await request.json()
        pago_id = body.get('pago_id')
        
        if not pago_id:
            raise HTTPException(status_code=400, detail="pago_id requerido")
        
        pago = db.query(Pago).filter(Pago.id == pago_id).first()
        if not pago:
            raise HTTPException(status_code=404, detail="Pago no encontrado")
        
        if pago.estado != "pendiente":
            raise HTTPException(status_code=400, detail="Este pago ya fue procesado")
        
        # Verificar con Mercantil
        servicio = MercantilService()
        resultado = await servicio.verificar_pago(
            referencia=pago.referencia,
            monto_esperado=float(pago.monto_reportado_bs or 0)
        )
        
        if resultado.get("success"):
            # Marcar como pagado automáticamente
            pago.estado = "conciliado"
            pago.monto_confirmado_bs = resultado.get("monto_real")
            pago.fecha_confirmacion = datetime.now(timezone.utc)
            pago.conciliado_por = "mercantil_auto"
            
            cuota = db.query(Cuota).filter(Cuota.id == pago.cuota_id).first()
            if cuota:
                cuota.estado = "pagada"
                cuota.fecha_pago = datetime.now(timezone.utc)
                cuota.monto_pagado = resultado.get("monto_real")
                
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
            
            db.commit()
            
            registrar_auditoria(
                db=db,
                usuario_id=current_admin.id,
                usuario_nombre=current_admin.nombre,
                usuario_rol=current_admin.rol,
                accion="CONCILIAR_MERCANTIL",
                tabla="pagos",
                registro_id=pago.id,
                detalles=f"Pago verificado automáticamente con Mercantil: ref={pago.referencia}"
            )
            
            return {
                "success": True,
                "mensaje": "Pago verificado y conciliado automáticamente",
                "referencia": pago.referencia,
                "monto_confirmado": resultado.get("monto_real")
            }
        else:
            return {
                "success": False,
                "estado": resultado.get("estado"),
                "mensaje": resultado.get("mensaje")
            }
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error verificando pago Mercantil: {e}")
        raise HTTPException(status_code=500, detail="Error interno")