# backend/app/routers/pagos.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime, timezone
from app.database import get_db
from app.models import Cuota, Pago, Financiamiento, Cliente
from app.schemas import PagoReporte, ConciliacionPago
from app.utils import actualizar_score_cliente, calcular_nivel, obtener_tasa_actual
from app.auth import get_current_admin

router = APIRouter(prefix="/pagos", tags=["Pagos"])

# ============================================================
# ✅ REPORTAR PAGO
# ============================================================
@router.post("/reportar")
def reportar_pago(pago: PagoReporte, db: Session = Depends(get_db)):
    try:
        cuota = db.query(Cuota).filter(Cuota.id == pago.cuota_id).first()
        if not cuota:
            return {"error": "Cuota no encontrada"}
        
        nuevo_pago = Pago(
            cuota_id=pago.cuota_id,
            financiamiento_id=cuota.financiamiento_id,
            referencia=pago.referencia,
            metodo=pago.metodo,
            monto_reportado_bs=pago.monto_bs,
            monto=pago.monto_bs,
            banco_origen=pago.banco_origen,
            telefono_pago=pago.telefono_pago,
            cedula_pago=pago.cedula_pago,
            comprobante=pago.comprobante,
            estado="pendiente",
            fecha_reporte=datetime.now(timezone.utc)
        )
        
        db.add(nuevo_pago)
        cuota.estado = "conciliando"
        db.commit()
        
        return {
            "pago_id": nuevo_pago.id,
            "estado": "pendiente",
            "mensaje": "Pago reportado. Esperando conciliación."
        }
    except Exception as e:
        print(f"❌ Error reportando pago: {e}")
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

# ============================================================
# ✅ OBTENER PAGOS DE UN FINANCIAMIENTO
# ============================================================
@router.get("/financiamiento/{financiamiento_id}")
def obtener_pagos_financiamiento(
    financiamiento_id: int,
    db: Session = Depends(get_db),
    current_admin = Depends(get_current_admin)
):
    pagos = db.query(Pago).filter(Pago.financiamiento_id == financiamiento_id).all()
    
    return [
        {
            "id": p.id,
            "cuota_id": p.cuota_id,
            "metodo": p.metodo,
            "monto_bs": p.monto_confirmado_bs or p.monto_reportado_bs or p.monto,
            "referencia": p.referencia,
            "estado": p.estado,
            "fecha_reporte": p.fecha_reporte.isoformat() if p.fecha_reporte else None,
            "fecha_confirmacion": p.fecha_confirmacion.isoformat() if p.fecha_confirmacion else None
        }
        for p in pagos
    ]