# backend/app/routers/pagos.py
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from datetime import datetime, timezone
from app.database import get_db
from app.models import Cuota, Pago, Financiamiento, Cliente
from app.schemas import PagoReporte, ConciliacionPago
from app.utils import actualizar_score_cliente, calcular_nivel, obtener_tasa_actual, enviar_notificacion_generica
from app.auth import get_current_admin
import json

router = APIRouter(prefix="/pagos", tags=["Pagos"])

@router.post("/reportar")
async def reportar_pago(request: Request, db: Session = Depends(get_db)):
    try:
        print("=" * 60)
        print("📝 REPORTAR PAGO - INICIO")
        body = await request.body()
        print(f"📥 Body raw (bytes): {len(body)} bytes")
        print(f"📥 Body raw (texto): {body.decode('utf-8')[:500]}")
        try:
            data = json.loads(body)
            print(f"📥 JSON parseado: {json.dumps(data, indent=2, ensure_ascii=False)}")
        except json.JSONDecodeError as e:
            print(f"❌ Error parseando JSON: {e}")
            raise HTTPException(status_code=400, detail=f"JSON inválido: {str(e)}")

        campos_requeridos = ['cuota_id', 'monto_bs', 'metodo', 'referencia', 'banco_origen']
        for campo in campos_requeridos:
            if campo not in data or not str(data.get(campo, '')).strip():
                print(f"❌ Campo faltante o vacío: {campo}")
                raise HTTPException(status_code=422, detail=f"Campo requerido faltante: {campo}")

        try:
            pago_data = PagoReporte(
                cuota_id=int(data['cuota_id']),
                monto_bs=float(data['monto_bs']),
                metodo=str(data['metodo']),
                referencia=str(data['referencia']),
                banco_origen=str(data.get('banco_origen', '')),
                telefono_pago=str(data.get('telefono_pago', '')),
                cedula_pago=str(data.get('cedula_pago', '')),
                comprobante=str(data.get('comprobante', ''))
            )
            print(f"✅ PagoReporte validado: {pago_data.dict()}")
        except (ValueError, TypeError) as e:
            print(f"❌ Error de tipo en campos: {e}")
            raise HTTPException(status_code=422, detail=f"Error de tipo en campos: {str(e)}")

        cuota = db.query(Cuota).filter(Cuota.id == pago_data.cuota_id).first()
        if not cuota:
            print(f"❌ Cuota no encontrada: {pago_data.cuota_id}")
            return {"error": "Cuota no encontrada"}
        print(f"✅ Cuota encontrada: ID {cuota.id}, Número {cuota.numero}")

        pago_existente = db.query(Pago).filter(Pago.cuota_id == pago_data.cuota_id, Pago.estado == "pendiente").first()
        if pago_existente:
            print(f"⚠️ Pago pendiente existente: {pago_existente.id}")
            return {"error": "Ya existe un pago pendiente para esta cuota", "pago_id": pago_existente.id}

        # ⚡ SOPORTE PARA MÚLTIPLES CUOTAS (adelantar/liquidar/abono)
        cuotas_incluidas_raw = data.get('cuotas_incluidas', [pago_data.cuota_id])
        modo_pago = data.get('modo_pago', 'cuota')
        monto_original = data.get('monto_original')  # Para abono: monto total de la cuota

        # Asegurar que cuotas_incluidas sea una lista
        if isinstance(cuotas_incluidas_raw, str):
            try:
                cuotas_incluidas = json.loads(cuotas_incluidas_raw)
            except:
                cuotas_incluidas = [pago_data.cuota_id]
        else:
            cuotas_incluidas = cuotas_incluidas_raw if isinstance(cuotas_incluidas_raw, list) else [pago_data.cuota_id]

        print(f"📋 Modo de pago: {modo_pago}")
        print(f"📋 Cuotas incluidas: {cuotas_incluidas}")

        # 💰 MANEJO ESPECIAL PARA ABONO
        if modo_pago == 'abono':
            # Verificar que el monto abonado sea menor al total
            total_cuota = monto_original or cuota.monto_total_bs
            if pago_data.monto_bs >= total_cuota:
                return {"error": "El monto del abono debe ser menor al total de la cuota. Use 'Pagar cuota completa'"}

            # Crear pago de abono
            nuevo_pago = Pago(
                cuota_id=pago_data.cuota_id,
                financiamiento_id=cuota.financiamiento_id,
                referencia=pago_data.referencia,
                metodo=pago_data.metodo,
                monto_reportado_bs=pago_data.monto_bs,
                monto=pago_data.monto_bs,
                banco_origen=pago_data.banco_origen,
                telefono_pago=pago_data.telefono_pago,
                cedula_pago=pago_data.cedula_pago,
                comprobante=pago_data.comprobante,
                estado="pendiente",
                fecha_reporte=datetime.now(timezone.utc),
                modo_pago=modo_pago,
                cuotas_incluidas=json.dumps(cuotas_incluidas),
                monto_original_bs=total_cuota  # Guardar monto original para referencia
            )
            db.add(nuevo_pago)
            # La cuota queda en estado "conciliando" hasta que se apruebe el abono
            cuota.estado = "conciliando"

            db.commit()
            db.refresh(nuevo_pago)

            return {
                "pago_id": nuevo_pago.id,
                "estado": "pendiente",
                "modo_pago": modo_pago,
                "monto_abonado": pago_data.monto_bs,
                "monto_total": total_cuota,
                "saldo_pendiente": round(total_cuota - pago_data.monto_bs, 2),
                "mensaje": f"Abono de BS {pago_data.monto_bs} reportado. Esperando conciliación. Saldo pendiente: BS {round(total_cuota - pago_data.monto_bs, 2)}"
            }

        # Crear pago principal (para cuota, adelantar, liquidar)
        nuevo_pago = Pago(
            cuota_id=pago_data.cuota_id,
            financiamiento_id=cuota.financiamiento_id,
            referencia=pago_data.referencia,
            metodo=pago_data.metodo,
            monto_reportado_bs=pago_data.monto_bs,
            monto=pago_data.monto_bs,
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

        # Crear pagos adicionales para cuotas incluidas (adelantar/liquidar)
        pagos_creados = 1
        for cid in cuotas_incluidas:
            if cid == pago_data.cuota_id:
                continue

            cuota_extra = db.query(Cuota).filter(Cuota.id == cid).first()
            if cuota_extra and cuota_extra.estado == 'pendiente':
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
        print(f"✅ Pago reportado ID: {nuevo_pago.id}")
        print(f"✅ Total pagos creados: {pagos_creados}")
        print("=" * 60)

        return {
            "pago_id": nuevo_pago.id,
            "estado": "pendiente",
            "modo_pago": modo_pago,
            "cuotas_afectadas": pagos_creados,
            "mensaje": f"Pago reportado ({modo_pago}). Esperando conciliación."
        }

    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error reportando pago: {e}")
        import traceback
        traceback.print_exc()
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/pendientes")
def pagos_pendientes_conciliacion(db: Session = Depends(get_db), current_admin = Depends(get_current_admin)):
    try:
        pagos = db.query(Pago).filter(Pago.estado == "pendiente").all()
        resultado = []
        for p in pagos:
            cuota = None
            if p.cuota_id:
                cuota = db.query(Cuota).filter(Cuota.id == p.cuota_id).first()
            cliente = None
            fin = db.query(Financiamiento).filter(Financiamiento.id == p.financiamiento_id).first()
            if fin:
                cliente = db.query(Cliente).filter(Cliente.id == fin.cliente_id).first()
            tasa = obtener_tasa_actual(db)
            monto_bs = p.monto_reportado_bs or p.monto or 0
            monto_usd = round(monto_bs / tasa, 2) if tasa > 0 else 0

            # Parsear cuotas incluidas
            cuotas_incl = []
            try:
                if p.cuotas_incluidas:
                    cuotas_incl = json.loads(p.cuotas_incluidas)
            except:
                pass

            resultado.append({
                "id": p.id, "pago_id": p.id,
                "fecha_reporte": p.fecha_reporte.isoformat() if p.fecha_reporte else None,
                "cliente_nombre": cliente.nombre if cliente else "Desconocido",
                "cliente_cedula": cliente.cedula if cliente else "",
                "cuota_numero": cuota.numero if cuota else 0,
                "cuota_id": p.cuota_id,
                "monto_reportado_bs": monto_bs,
                "monto_reportado_usd": monto_usd,
                "metodo": p.metodo, "referencia": p.referencia,
                "banco_origen": p.banco_origen, "telefono_pago": p.telefono_pago,
                "comprobante": p.comprobante, "comprobante_url": p.comprobante,
                "estado": p.estado,
                "modo_pago": p.modo_pago or "cuota",
                "cuotas_incluidas": cuotas_incl,
                "es_pago_padre": p.pago_padre_id is None,
                "monto_original_bs": p.monto_original_bs  # Para abonos
            })
        return resultado
    except Exception as e:
        print(f"❌ Error en pagos/pendientes: {e}")
        import traceback
        traceback.print_exc()
        return []

@router.post("/conciliar")
def conciliar_pago(conciliacion: ConciliacionPago, db: Session = Depends(get_db), current_admin = Depends(get_current_admin)):
    try:
        print(f"📝 Conciliando pago: {conciliacion.dict()}")
        pago = db.query(Pago).filter(Pago.id == conciliacion.pago_id).first()
        if not pago:
            raise HTTPException(status_code=404, detail="Pago no encontrado")
        if pago.estado != "pendiente":
            raise HTTPException(status_code=400, detail="Este pago ya fue procesado")

        pago.monto_confirmado_bs = conciliacion.monto_confirmado_bs
        pago.estado = conciliacion.estado
        pago.conciliado_por = conciliacion.conciliado_por
        pago.fecha_confirmacion = datetime.now(timezone.utc)

        cuota = db.query(Cuota).filter(Cuota.id == pago.cuota_id).first()
        if not cuota:
            raise HTTPException(status_code=404, detail="Cuota no encontrada")

        fin = db.query(Financiamiento).filter(Financiamiento.id == pago.financiamiento_id).first()
        cliente = None
        if fin:
            cliente = db.query(Cliente).filter(Cliente.id == fin.cliente_id).first()

        # ⚡ CONCILIAR TAMBIÉN LOS PAGOS HIJOS (cuotas incluidas)
        pagos_hijos = db.query(Pago).filter(Pago.pago_padre_id == pago.id).all()

        if conciliacion.estado == "conciliado":
            # 💰 MANEJO ESPECIAL PARA ABONO
            if pago.modo_pago == 'abono':
                # El abono se registra pero la cuota sigue pendiente
                cuota.monto_pagado = (cuota.monto_pagado or 0) + conciliacion.monto_confirmado_bs
                cuota.estado = "pendiente"  # Sigue pendiente hasta pagar completo

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
                    "mensaje": f"✅ Abono de BS {conciliacion.monto_confirmado_bs} conciliado. Saldo pendiente: BS {round(cuota.monto_total_bs - cuota.monto_pagado, 2)}"
                }

            # Pago completo (cuota, adelantar, liquidar)
            cuota.estado = "pagada"
            cuota.fecha_pago = datetime.now(timezone.utc)
            cuota.monto_pagado = conciliacion.monto_confirmado_bs

            # Conciliar pagos hijos
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

            cuotas_pendientes = db.query(Cuota).filter(
                Cuota.financiamiento_id == fin.id, 
                Cuota.estado.in_(["pendiente", "conciliando"])
            ).count()
            if cuotas_pendientes == 0:
                fin.estado = "completado"
                fin.fecha_completado = datetime.now(timezone.utc)
                print(f"✅ Financiamiento {fin.codigo} completado")

            db.commit()

            if cliente:
                actualizar_score_cliente(cliente, db)
                print(f"🎯 Score actualizado: {cliente.score} pts | Nivel: {cliente.nivel}")

            return {
                "success": True, "estado": "conciliado",
                "cuota_pagada": cuota.numero,
                "cuotas_adicionales": len(pagos_hijos),
                "monto_bs": conciliacion.monto_confirmado_bs,
                "score_actualizado": cliente.score if cliente else None,
                "nivel_actual": cliente.nivel if cliente else None,
                "mensaje": "✅ Pago conciliado correctamente"
            }
        else:
            # Rechazado
            cuota.estado = "pendiente"
            pago.rechazado_por = conciliacion.conciliado_por
            pago.fecha_rechazo = datetime.now(timezone.utc)

            # Rechazar pagos hijos también
            for ph in pagos_hijos:
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
                "mensaje": "❌ Pago rechazado. Cuota vuelve a pendiente."
            }
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error conciliando pago: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/cuotas/{id}/pagar-efectivo")
def pagar_cuota_efectivo(id: int, db: Session = Depends(get_db), current_admin = Depends(get_current_admin)):
    try:
        cuota = db.query(Cuota).filter(Cuota.id == id).first()
        if not cuota:
            return {"error": "Cuota no encontrada"}
        fin = db.query(Financiamiento).filter(Financiamiento.id == cuota.financiamiento_id).first()
        cliente = db.query(Cliente).filter(Cliente.id == fin.cliente_id).first()
        hoy = datetime.now(timezone.utc)

        interes_bs = 0
        interes_usd = 0
        if hoy > cuota.fecha_vencimiento:
            dias_atraso = (hoy - cuota.fecha_vencimiento).days
            dias_gracia = 3
            if dias_atraso > dias_gracia:
                nivel, config = calcular_nivel(cliente.score)
                tasa_mora = config["mora_diaria"]
                tasa = obtener_tasa_actual(db)
                dias_efectivos = dias_atraso - dias_gracia
                interes_bs = cuota.monto_base_bs * (tasa_mora / 100) * dias_efectivos
                interes_usd = interes_bs / tasa if tasa else 0
                cuota.monto_interes_mora_bs = round(interes_bs, 2)
                cuota.monto_interes_mora_usd = round(interes_usd, 2)
                cuota.monto_total_bs = round(cuota.monto_base_bs + interes_bs, 2)
                cuota.monto_total_usd = round(cuota.monto_base_usd + interes_usd, 2)
                if hasattr(cliente, 'cuotas_con_mora'):
                    cliente.cuotas_con_mora += 1
            else:
                cuota.monto_total_bs = cuota.monto_base_bs
                cuota.monto_total_usd = cuota.monto_base_usd
        else:
            cuota.monto_total_bs = cuota.monto_base_bs
            cuota.monto_total_usd = cuota.monto_base_usd

        cuota.estado = "pagada"
        cuota.fecha_pago = hoy
        cuota.monto = cuota.monto_total_bs
        cuota.monto_usd = cuota.monto_total_usd

        pago = Pago(
            cuota_id=cuota.id, financiamiento_id=fin.id, metodo="efectivo",
            monto_reportado_bs=cuota.monto_total_bs, monto_confirmado_bs=cuota.monto_total_bs,
            monto=cuota.monto_total_bs, monto_usd=cuota.monto_total_usd,
            estado="conciliado", fecha_confirmacion=hoy, conciliado_por="sistema",
            modo_pago="cuota"
        )
        db.add(pago)
        db.commit()

        cuotas_pendientes = db.query(Cuota).filter(Cuota.financiamiento_id == fin.id, Cuota.estado.in_(["pendiente", "conciliando"])).count()
        if cuotas_pendientes == 0:
            fin.estado = "completado"
            fin.fecha_completado = hoy
            db.commit()

        actualizar_score_cliente(cliente, db)

        return {
            "cuota_pagada": cuota.numero,
            "monto_base_bs": cuota.monto_base_bs,
            "interes_mora_bs": cuota.monto_interes_mora_bs,
            "total_pagado_bs": cuota.monto_total_bs,
            "score_actualizado": cliente.score,
            "nivel_actual": cliente.nivel,
            "financiamiento_estado": fin.estado
        }
    except Exception as e:
        print(f"❌ Error pagando cuota: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))