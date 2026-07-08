# routers/pagos.py
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import Cuota, Pago, Financiamiento, Cliente
from app.schemas import PagoReporte, ConciliacionPago
from app.utils import actualizar_score_cliente, calcular_nivel
from datetime import datetime

router = APIRouter(prefix="/pagos", tags=["Pagos"])

@router.post("/reportar")
def reportar_pago(pago: PagoReporte, db: Session = Depends(get_db)):
    cuota = db.query(Cuota).filter(Cuota.id == pago.cuota_id).first()
    if not cuota:
        return {"error": "Cuota no encontrada"}
    
    nuevo_pago = Pago(
        cuota_id=pago.cuota_id,
        financiamiento_id=cuota.financiamiento_id,
        referencia=pago.referencia,
        metodo=pago.metodo,
        monto_reportado_bs=pago.monto_bs,
        banco_origen=pago.banco_origen,
        telefono_pago=pago.telefono_pago,
        cedula_pago=pago.cedula_pago,
        comprobante=pago.comprobante,
        estado="pendiente"
    )
    
    db.add(nuevo_pago)
    cuota.estado = "conciliando"
    db.commit()
    
    return {
        "pago_id": nuevo_pago.id,
        "estado": "pendiente",
        "mensaje": "Pago reportado. Esperando conciliación."
    }

@router.get("/pendientes")
def pagos_pendientes_conciliacion(db: Session = Depends(get_db)):
    pagos = db.query(Pago).filter(Pago.estado == "pendiente").all()
    
    resultado = []
    for p in pagos:
        cuota = db.query(Cuota).filter(Cuota.id == p.cuota_id).first()
        cliente = db.query(Cliente).join(Financiamiento).filter(
            Financiamiento.id == p.financiamiento_id
        ).first()
        
        resultado.append({
            "pago_id": p.id,
            "fecha_reporte": p.fecha_reporte.isoformat(),
            "cliente": cliente.nombre if cliente else "Desconocido",
            "cedula": cliente.cedula if cliente else "",
            "cuota_numero": cuota.numero if cuota else 0,
            "monto_reportado_bs": p.monto_reportado_bs,
            "metodo": p.metodo,
            "referencia": p.referencia,
            "banco_origen": p.banco_origen,
            "telefono_pago": p.telefono_pago,
            "comprobante": p.comprobante
        })
    
    return resultado

@router.post("/conciliar")
def conciliar_pago(conciliacion: ConciliacionPago, db: Session = Depends(get_db)):
    pago = db.query(Pago).filter(Pago.id == conciliacion.pago_id).first()
    if not pago:
        return {"error": "Pago no encontrado"}
    
    pago.monto_confirmado_bs = conciliacion.monto_confirmado_bs
    pago.estado = conciliacion.estado
    pago.conciliado_por = conciliacion.conciliado_por
    pago.fecha_confirmacion = datetime.now()
    
    cuota = db.query(Cuota).filter(Cuota.id == pago.cuota_id).first()
    
    if conciliacion.estado == "conciliado":
        cuota.estado = "pagada"
        cuota.fecha_pago = datetime.now()
        
        fin = db.query(Financiamiento).filter(Financiamiento.id == pago.financiamiento_id).first()
        cliente = db.query(Cliente).filter(Cliente.id == fin.cliente_id).first()
        
        cuotas_pendientes = db.query(Cuota).filter(
            Cuota.financiamiento_id == fin.id,
            Cuota.estado.in_(["pendiente", "conciliando"])
        ).count()
        
        if cuotas_pendientes == 0:
            fin.estado = "completado"
            fin.fecha_completado = datetime.now()
            db.commit()
            actualizar_score_cliente(cliente, db)
        
        return {
            "estado": "conciliado",
            "cuota_pagada": cuota.numero,
            "monto_bs": conciliacion.monto_confirmado_bs,
            "mensaje": "Pago conciliado correctamente"
        }
    else:
        cuota.estado = "pendiente"
        db.commit()
        return {
            "estado": "rechazado",
            "mensaje": "Pago rechazado. Cuota vuelve a pendiente."
        }

@router.post("/cuotas/{id}/pagar-efectivo")
def pagar_cuota_efectivo(id: int, db: Session = Depends(get_db)):
    cuota = db.query(Cuota).filter(Cuota.id == id).first()
    if not cuota:
        return {"error": "Cuota no encontrada"}
    
    fin = db.query(Financiamiento).filter(Financiamiento.id == cuota.financiamiento_id).first()
    cliente = db.query(Cliente).filter(Cliente.id == fin.cliente_id).first()
    
    hoy = datetime.now()
    
    if hoy > cuota.fecha_vencimiento:
        dias_atraso = (hoy - cuota.fecha_vencimiento).days
        dias_gracia = 3
        
        if dias_atraso > dias_gracia:
            nivel, config = calcular_nivel(cliente.score)
            tasa_mora = config["mora_diaria"]
            from app.utils import obtener_tasa_actual
            tasa = obtener_tasa_actual(db)
            
            dias_efectivos = dias_atraso - dias_gracia
            interes_bs = cuota.monto_base_bs * (tasa_mora / 100) * dias_efectivos
            interes_usd_ref = interes_bs / tasa
            
            cuota.monto_interes_mora_bs = round(interes_bs, 2)
            cuota.monto_interes_mora_usd = round(interes_usd_ref, 2)
            cuota.monto_total_bs = round(cuota.monto_base_bs + interes_bs, 2)
            cuota.monto_total_usd = round(cuota.monto_base_usd + interes_usd_ref, 2)
            cliente.cuotas_con_mora += 1
        else:
            cuota.monto_total_bs = cuota.monto_base_bs
            cuota.monto_total_usd = cuota.monto_base_usd
    else:
        cuota.monto_total_bs = cuota.monto_base_bs
        cuota.monto_total_usd = cuota.monto_base_usd
    
    cuota.estado = "pagada"
    cuota.fecha_pago = hoy
    
    pago = Pago(
        cuota_id=cuota.id,
        financiamiento_id=fin.id,
        metodo="efectivo",
        monto_reportado_bs=cuota.monto_total_bs,
        monto_confirmado_bs=cuota.monto_total_bs,
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