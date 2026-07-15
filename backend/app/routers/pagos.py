# backend/app/routers/pagos.py
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from datetime import datetime, timezone
from app.database import get_db
from app.models import Cuota, Pago, Financiamiento, Cliente
from app.schemas import PagoReporte, ConciliacionPago
from app.utils import actualizar_score_cliente, calcular_nivel, obtener_tasa_actual
from app.auth import get_current_admin
import json

router = APIRouter(prefix="/pagos", tags=["Pagos"])

# ============================================================
# ✅ REPORTAR PAGO (CON DEBUG DETALLADO)
# ============================================================
@router.post("/reportar")
async def reportar_pago(request: Request, db: Session = Depends(get_db)):
    """
    Recibe el reporte de pago desde la app móvil
    """
    try:
        print("=" * 60)
        print("📝 REPORTAR PAGO - INICIO")
        
        # ✅ 1. LEER BODY RAW
        body = await request.body()
        print(f"📥 Body raw (bytes): {len(body)} bytes")
        print(f"📥 Body raw (texto): {body.decode('utf-8')[:500]}")
        
        # ✅ 2. PARSEAR JSON
        try:
            data = json.loads(body)
            print(f"📥 JSON parseado: {json.dumps(data, indent=2, ensure_ascii=False)}")
        except json.JSONDecodeError as e:
            print(f"❌ Error parseando JSON: {e}")
            raise HTTPException(status_code=400, detail=f"JSON inválido: {str(e)}")
        
        # ✅ 3. VALIDAR CAMPOS OBLIGATORIOS
        campos_requeridos = ['cuota_id', 'monto_bs', 'metodo', 'referencia']
        for campo in campos_requeridos:
            if campo not in data:
                print(f"❌ Campo faltante: {campo}")
                raise HTTPException(status_code=422, detail=f"Campo requerido faltante: {campo}")
        
        # ✅ 4. CONVERTIR TIPOS
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
        
        # ✅ 5. VERIFICAR CUOTA
        cuota = db.query(Cuota).filter(Cuota.id == pago_data.cuota_id).first()
        if not cuota:
            print(f"❌ Cuota no encontrada: {pago_data.cuota_id}")
            return {"error": "Cuota no encontrada"}
        
        print(f"✅ Cuota encontrada: ID {cuota.id}, Número {cuota.numero}")
        
        # ✅ 6. VERIFICAR PAGO DUPLICADO
        pago_existente = db.query(Pago).filter(
            Pago.cuota_id == pago_data.cuota_id,
            Pago.estado == "pendiente"
        ).first()
        
        if pago_existente:
            print(f"⚠️ Pago pendiente existente: {pago_existente.id}")
            return {
                "error": "Ya existe un pago pendiente para esta cuota",
                "pago_id": pago_existente.id
            }
        
        # ✅ 7. CREAR PAGO
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
            fecha_reporte=datetime.now(timezone.utc)
        )
        
        db.add(nuevo_pago)
        cuota.estado = "conciliando"
        db.commit()
        db.refresh(nuevo_pago)
        
        print(f"✅ Pago reportado ID: {nuevo_pago.id}")
        print(f"✅ Comprobante: {nuevo_pago.comprobante[:50] if nuevo_pago.comprobante else 'Sin foto'}")
        print("=" * 60)
        
        return {
            "pago_id": nuevo_pago.id,
            "estado": "pendiente",
            "mensaje": "Pago reportado. Esperando conciliación."
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error reportando pago: {e}")
        import traceback
        traceback.print_exc()
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

# ============================================================
# ✅ PAGOS PENDIENTES DE CONCILIACIÓN
# ============================================================
@router.get("/pendientes")
def pagos_pendientes_conciliacion(
    db: Session = Depends(get_db),
    current_admin = Depends(get_current_admin)
):
    try:
        pagos = db.query(Pago).filter(Pago.estado == "pendiente").all()
        
        resultado = []
        for p in pagos:
            # Obtener cuota
            cuota = None
            if p.cuota_id:
                cuota = db.query(Cuota).filter(Cuota.id == p.cuota_id).first()
            
            # Obtener cliente
            cliente = None
            fin = db.query(Financiamiento).filter(Financiamiento.id == p.financiamiento_id).first()
            if fin:
                cliente = db.query(Cliente).filter(Cliente.id == fin.cliente_id).first()
            
            # Calcular monto en USD si no está
            tasa = obtener_tasa_actual(db)
            monto_bs = p.monto_reportado_bs or p.monto or 0
            monto_usd = round(monto_bs / tasa, 2) if tasa > 0 else 0
            
            resultado.append({
                "id": p.id,
                "pago_id": p.id,
                "fecha_reporte": p.fecha_reporte.isoformat() if p.fecha_reporte else None,
                "cliente_nombre": cliente.nombre if cliente else "Desconocido",
                "cliente_cedula": cliente.cedula if cliente else "",
                "cuota_numero": cuota.numero if cuota else 0,
                "cuota_id": p.cuota_id,
                "monto_reportado_bs": monto_bs,
                "monto_reportado_usd": monto_usd,
                "metodo": p.metodo,
                "referencia": p.referencia,
                "banco_origen": p.banco_origen,
                "telefono_pago": p.telefono_pago,
                "comprobante": p.comprobante,
                "comprobante_url": p.comprobante,
                "estado": p.estado
            })
        
        return resultado
        
    except Exception as e:
        print(f"❌ Error en pagos/pendientes: {e}")
        import traceback
        traceback.print_exc()
        return []

# ============================================================
# ✅ CONCILIAR PAGO
# ============================================================
@router.post("/conciliar")
def conciliar_pago(
    conciliacion: ConciliacionPago, 
    db: Session = Depends(get_db),
    current_admin = Depends(get_current_admin)
):
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
        
        if conciliacion.estado == "conciliado":
            # Aprobar pago
            cuota.estado = "pagada"
            cuota.fecha_pago = datetime.now(timezone.utc)
            cuota.monto_pagado = conciliacion.monto_confirmado_bs
            
            fin = db.query(Financiamiento).filter(Financiamiento.id == pago.financiamiento_id).first()
            if fin:
                cliente = db.query(Cliente).filter(Cliente.id == fin.cliente_id).first()
                
                cuotas_pendientes = db.query(Cuota).filter(
                    Cuota.financiamiento_id == fin.id,
                    Cuota.estado.in_(["pendiente", "conciliando"])
                ).count()
                
                if cuotas_pendientes == 0:
                    fin.estado = "completado"
                    fin.fecha_completado = datetime.now(timezone.utc)
                    db.commit()
                    if cliente:
                        actualizar_score_cliente(cliente, db)
            
            db.commit()
            return {
                "success": True,
                "estado": "conciliado",
                "cuota_pagada": cuota.numero,
                "monto_bs": conciliacion.monto_confirmado_bs,
                "mensaje": "✅ Pago conciliado correctamente"
            }
        else:
            # Rechazar pago
            cuota.estado = "pendiente"
            pago.rechazado_por = conciliacion.conciliado_por
            pago.fecha_rechazo = datetime.now(timezone.utc)
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

# ============================================================
# ✅ PAGAR CUOTA EN EFECTIVO
# ============================================================
@router.post("/cuotas/{id}/pagar-efectivo")
def pagar_cuota_efectivo(
    id: int, 
    db: Session = Depends(get_db),
    current_admin = Depends(get_current_admin)
):
    try:
        cuota = db.query(Cuota).filter(Cuota.id == id).first()
        if not cuota:
            return {"error": "Cuota no encontrada"}
        
        fin = db.query(Financiamiento).filter(Financiamiento.id == cuota.financiamiento_id).first()
        cliente = db.query(Cliente).filter(Cliente.id == fin.cliente_id).first()
        
        hoy = datetime.now(timezone.utc)
        
        # Calcular mora si aplica
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
            cuota_id=cuota.id,
            financiamiento_id=fin.id,
            metodo="efectivo",
            monto_reportado_bs=cuota.monto_total_bs,
            monto_confirmado_bs=cuota.monto_total_bs,
            monto=cuota.monto_total_bs,
            monto_usd=cuota.monto_total_usd,
            estado="conciliado",
            fecha_confirmacion=hoy,
            conciliado_por="sistema"
        )
        db.add(pago)
        db.commit()
        
        cuotas_pendientes = db.query(Cuota).filter(
            Cuota.financiamiento_id == fin.id,
            Cuota.estado.in_(["pendiente", "conciliando"])
        ).count()
        
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
            "financiamiento_estado": fin.estado
        }
    except Exception as e:
        print(f"❌ Error pagando cuota: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))