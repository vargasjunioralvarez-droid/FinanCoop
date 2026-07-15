# backend/app/routers/financiamientos.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import Cliente, Financiamiento, Cuota, Pago
from app.schemas import FinanciamientoCreate, AprobacionExtra
from app.utils import calcular_nivel, actualizar_score_cliente, calcular_usado_disponible, obtener_tasa_actual
from app.auth import get_current_admin
from datetime import datetime, timedelta, timezone
import random

router = APIRouter(prefix="/financiamientos", tags=["Financiamientos"])

@router.post("")
def crear_financiamiento(f: FinanciamientoCreate, db: Session = Depends(get_db)):
    cliente = db.query(Cliente).filter(Cliente.id == f.cliente_id).first()
    if not cliente:
        return {"error": "Cliente no encontrado"}
    
    hoy = datetime.now(timezone.utc)
    deudas_vencidas = db.query(Cuota).join(Financiamiento).filter(
        Financiamiento.cliente_id == f.cliente_id,
        Cuota.estado == "pendiente",
        Cuota.fecha_vencimiento < hoy
    ).count()
    
    if deudas_vencidas > 0:
        return {
            "error": "BLOQUEADO",
            "mensaje": f"Tiene {deudas_vencidas} cuota(s) vencida(s). Debe pagar antes de comprar.",
            "deudas_vencidas": deudas_vencidas
        }
    
    disponible = calcular_usado_disponible(f.cliente_id, db)
    if not disponible["puede_comprar"]:
        return {
            "error": "LÍMITE AGOTADO",
            "mensaje": "Ha usado todo su límite de financiamiento",
            "limite_usd": disponible["limite_usd"],
            "usado_usd": disponible["usado_usd"]
        }
    
    tasa = obtener_tasa_actual(db)
    nivel, config = calcular_nivel(cliente.score)
    
    monto_total_usd = f.monto_total_bs / tasa
    
    if monto_total_usd > disponible["disponible_usd"]:
        return {
            "error": "Monto excede disponible",
            "disponible_usd": disponible["disponible_usd"],
            "disponible_bs": disponible["disponible_bs"]
        }
    
    if monto_total_usd > config["monto_max_usd"]:
        return {
            "error": "Monto excede límite",
            "monto_maximo_usd": config["monto_max_usd"],
            "monto_maximo_bs": round(config["monto_max_usd"] * tasa, 2)
        }
    
    if f.cuotas_solicitadas > config["cuotas_max"]:
        return {
            "error": "Cuotas exceden límite",
            "cuotas_maximas": config["cuotas_max"]
        }
    
    requiere_aprobacion = f.cuotas_solicitadas > config["cuotas_base"] and config["aprobacion_extra"]
    cuotas_aprobadas = f.cuotas_solicitadas
    
    entrada_bs = f.monto_total_bs * (config["entrada_pct"] / 100)
    financia_bs = f.monto_total_bs - entrada_bs
    monto_cuota_bs = financia_bs / cuotas_aprobadas
    
    monto_total_usd_ref = f.monto_total_bs / tasa
    entrada_usd_ref = entrada_bs / tasa
    financia_usd_ref = financia_bs / tasa
    monto_cuota_usd_ref = monto_cuota_bs / tasa
    
    codigo = f"F-{random.randint(100000, 999999)}"
    fecha_primera = datetime.now(timezone.utc) + timedelta(days=15)
    
    fin = Financiamiento(
        cliente_id=f.cliente_id,
        codigo=codigo,
        descripcion=f.descripcion,
        monto_total_bs=f.monto_total_bs,
        monto_entrada_bs=entrada_bs,
        monto_financia_bs=financia_bs,
        monto_cuota_bs=monto_cuota_bs,
        monto_total_usd=monto_total_usd_ref,
        monto_entrada_usd=entrada_usd_ref,
        monto_financia_usd=financia_usd_ref,
        monto_cuota_usd=monto_cuota_usd_ref,
        tasa_aplicada=tasa,
        nivel_aplicado=nivel,
        cuotas_solicitadas=f.cuotas_solicitadas,
        cuotas_aprobadas=cuotas_aprobadas,
        requiere_aprobacion=requiere_aprobacion,
        entrada_pct=config["entrada_pct"],
        financia_pct=config["financia_pct"],
        fecha_primera_cuota=fecha_primera
    )
    db.add(fin)
    db.commit()
    db.refresh(fin)
    
    for i in range(1, cuotas_aprobadas + 1):
        cuota = Cuota(
            financiamiento_id=fin.id,
            numero=i,
            monto_base_bs=monto_cuota_bs,
            monto_total_bs=monto_cuota_bs,
            monto_base_usd=monto_cuota_usd_ref,
            monto_total_usd=monto_cuota_usd_ref,
            fecha_vencimiento=fecha_primera + timedelta(days=15 * (i - 1))
        )
        db.add(cuota)
    db.commit()
    
    cliente.total_monto_comprado_usd += monto_total_usd
    db.commit()
    
    return {
        "financiamiento": {
            "id": fin.id,
            "codigo": fin.codigo,
            "monto_total_bs": round(fin.monto_total_bs, 2),
            "monto_total_usd": round(fin.monto_total_usd, 2),
            "monto_entrada_bs": round(fin.monto_entrada_bs, 2),
            "monto_entrada_usd": round(fin.monto_entrada_usd, 2),
            "monto_cuota_bs": round(fin.monto_cuota_bs, 2),
            "monto_cuota_usd": round(fin.monto_cuota_usd, 2),
            "tasa_aplicada": fin.tasa_aplicada,
            "cuotas_aprobadas": fin.cuotas_aprobadas,
            "requiere_aprobacion": fin.requiere_aprobacion
        },
        "mensaje": f"Entrada de BS {entrada_bs:.2f} pagada. {cuotas_aprobadas} cuotas quincenales de BS {monto_cuota_bs:.2f}",
        "advertencia": "Requiere aprobación del establecimiento" if requiere_aprobacion else None
    }

@router.post("/{id}/aprobar")
def aprobar_financiamiento(id: int, aprobacion: AprobacionExtra, db: Session = Depends(get_db)):
    fin = db.query(Financiamiento).filter(Financiamiento.id == id).first()
    if not fin:
        return {"error": "Financiamiento no encontrado"}
    
    if not fin.requiere_aprobacion:
        return {"error": "Este financiamiento no requiere aprobación"}
    
    fin.cuotas_aprobadas = aprobacion.cuotas_aprobadas
    fin.aprobado_por = aprobacion.aprobado_por
    db.commit()
    
    return {
        "mensaje": f"Financiamiento aprobado con {aprobacion.cuotas_aprobadas} cuotas",
        "aprobado_por": aprobacion.aprobado_por
    }

@router.get("")
def listar_financiamientos(db: Session = Depends(get_db)):
    return db.query(Financiamiento).all()

@router.get("/{id}")
def obtener_financiamiento(id: int, db: Session = Depends(get_db)):
    fin = db.query(Financiamiento).filter(Financiamiento.id == id).first()
    if not fin:
        return {"error": "No encontrado"}
    
    cliente = db.query(Cliente).filter(Cliente.id == fin.cliente_id).first()
    
    return {
        "financiamiento": fin,
        "cliente": {
            "nombre": cliente.nombre,
            "telefono": cliente.telefono
        }
    }

@router.get("/{id}/cuotas")
def ver_cuotas(id: int, db: Session = Depends(get_db)):
    cuotas = db.query(Cuota).filter(Cuota.financiamiento_id == id).all()
    
    hoy = datetime.now(timezone.utc)
    
    resultado = []
    
    for c in cuotas:
        data = {
            "id": c.id,
            "numero": c.numero,
            "monto_base_bs": round(c.monto_base_bs, 2),
            "monto_interes_mora_bs": round(c.monto_interes_mora_bs, 2),
            "monto_total_bs": round(c.monto_total_bs, 2),
            "monto_base_usd": round(c.monto_base_usd, 2),
            "monto_interes_mora_usd": round(c.monto_interes_mora_usd, 2),
            "monto_total_usd": round(c.monto_total_usd, 2),
            "fecha_vencimiento": c.fecha_vencimiento.isoformat() if c.fecha_vencimiento else None,
            "estado": c.estado,
            "dias_atraso": 0
        }
        
        if c.estado == "pendiente" and hoy > c.fecha_vencimiento:
            dias_atraso = (hoy - c.fecha_vencimiento).days
            data["dias_atraso"] = dias_atraso
        
        resultado.append(data)
    
    return resultado

# ============================================================
# ✅ ELIMINAR FINANCIAMIENTO - NUEVO ENDPOINT
# ============================================================
@router.delete("/{id}")
def eliminar_financiamiento(
    id: int,
    db: Session = Depends(get_db),
    current_admin = Depends(get_current_admin)
):
    financiamiento = db.query(Financiamiento).filter(Financiamiento.id == id).first()
    if not financiamiento:
        raise HTTPException(status_code=404, detail="Financiamiento no encontrado")
    
    # Eliminar en orden: pagos → cuotas → financiamiento
    db.query(Pago).filter(Pago.financiamiento_id == id).delete(synchronize_session=False)
    db.query(Cuota).filter(Cuota.financiamiento_id == id).delete(synchronize_session=False)
    
    db.delete(financiamiento)
    db.commit()
    
    return {
        "success": True,
        "mensaje": f"Financiamiento #{id} eliminado correctamente"
    }