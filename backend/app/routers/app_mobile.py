# backend/app/routers/app_mobile.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import Cliente, Financiamiento, Cuota, TasaDolar, ConfiguracionPago
from app.utils import obtener_tasa_actual, actualizar_score_cliente
from app.auth import get_current_cliente
from datetime import datetime, timezone  # 👈 AGREGAR timezone
import random
import string

router = APIRouter(prefix="/app", tags=["App Móvil"])

# ============================================================
# ✅ LOGIN PARA CLIENTES (APP MÓVIL)
# ============================================================
@router.post("/login")
def app_login(cedula: str, pin: str, db: Session = Depends(get_db)):
    cliente = db.query(Cliente).filter(Cliente.cedula == cedula).first()
    
    if not cliente:
        return {"error": "Cliente no encontrado"}
    
    if cliente.pin != pin:
        return {"error": "PIN incorrecto"}
    
    # Actualizar último acceso
    cliente.ultimo_acceso = datetime.now(timezone.utc)  # 👈 CORREGIDO
    db.commit()
    
    # Generar token de app
    token = ''.join(random.choices(string.ascii_letters + string.digits, k=32))
    cliente.token_app = token
    db.commit()
    
    return {
        "success": True,
        "token": token,
        "cliente": {
            "id": cliente.id,
            "nombre": cliente.nombre,
            "cedula": cliente.cedula,
            "nivel": cliente.nivel,
            "score": cliente.score
        }
    }

# ============================================================
# ✅ MIS DATOS
# ============================================================
@router.get("/mis-datos")
def mis_datos(
    current_user = Depends(get_current_cliente),
    db: Session = Depends(get_db)
):
    cliente = current_user
    
    # Actualizar score
    actualizar_score_cliente(cliente, db)
    db.refresh(cliente)
    
    # Obtener financiamientos activos
    financiamientos = db.query(Financiamiento).filter(
        Financiamiento.cliente_id == cliente.id,
        Financiamiento.estado == "activo"
    ).all()
    
    # Obtener todas las cuotas pendientes
    cuotas = db.query(Cuota).join(Financiamiento).filter(
        Financiamiento.cliente_id == cliente.id,
        Cuota.estado == "pendiente"
    ).all()
    
    # Calcular cuotas atrasadas - ✅ CORREGIDO
    hoy = datetime.now(timezone.utc)  # 👈 CORREGIDO
    cuotas_atrasadas = [c for c in cuotas if c.estado == "pendiente" and hoy > c.fecha_vencimiento]
    
    # Obtener tasa actual
    tasa = obtener_tasa_actual(db)
    
    # Obtener configuración de pago
    config_pago = db.query(ConfiguracionPago).first()
    
    return {
        "cliente": {
            "id": cliente.id,
            "nombre": cliente.nombre,
            "cedula": cliente.cedula,
            "telefono": cliente.telefono,
            "email": cliente.email,
            "direccion": cliente.direccion,
            "nivel": cliente.nivel,
            "score": cliente.score,
            "total_compras": cliente.total_compras,
            "total_monto_comprado_usd": cliente.total_monto_comprado_usd,
            "cuotas_pagadas_tiempo": cliente.cuotas_pagadas_tiempo,
            "cuotas_con_mora": cliente.cuotas_con_mora
        },
        "financiamientos_activos": [
            {
                "id": f.id,
                "codigo": f.codigo,
                "monto_total_bs": f.monto_total_bs,
                "monto_total_usd": f.monto_total_usd,
                "monto_cuota_bs": f.monto_cuota_bs,
                "monto_cuota_usd": f.monto_cuota_usd,
                "cuotas_aprobadas": f.cuotas_aprobadas,
                "cuotas_pagadas": db.query(Cuota).filter(
                    Cuota.financiamiento_id == f.id,
                    Cuota.estado == "pagada"
                ).count(),
                "cuotas_restantes": f.cuotas_aprobadas - db.query(Cuota).filter(
                    Cuota.financiamiento_id == f.id,
                    Cuota.estado == "pagada"
                ).count(),
                "proxima_cuota": db.query(Cuota).filter(
                    Cuota.financiamiento_id == f.id,
                    Cuota.estado == "pendiente"
                ).order_by(Cuota.fecha_vencimiento).first()
            } for f in financiamientos
        },
        "cuotas_atrasadas": len(cuotas_atrasadas),
        "tasa_actual": tasa,
        "datos_pago": {
            "banco_pago_movil": config_pago.banco_pago_movil if config_pago else None,
            "telefono_pago_movil": config_pago.telefono_pago_movil if config_pago else None,
            "cedula_pago_movil": config_pago.cedula_pago_movil if config_pago else None,
            "banco_transferencia": config_pago.banco_transferencia if config_pago else None,
            "cuenta_transferencia": config_pago.cuenta_transferencia if config_pago else None
        }
    }

# ============================================================
# ✅ MIS CUOTAS
# ============================================================
@router.get("/mis-cuotas")
def mis_cuotas(
    current_user = Depends(get_current_cliente),
    db: Session = Depends(get_db)
):
    cliente = current_user
    
    cuotas = db.query(Cuota).join(Financiamiento).filter(
        Financiamiento.cliente_id == cliente.id
    ).order_by(Cuota.fecha_vencimiento).all()
    
    hoy = datetime.now(timezone.utc)  # 👈 CORREGIDO
    
    return {
        "cuotas": [
            {
                "id": c.id,
                "financiamiento_id": c.financiamiento_id,
                "financiamiento_codigo": c.financiamiento.codigo,
                "numero": c.numero,
                "monto_base_bs": c.monto_base_bs,
                "monto_interes_mora_bs": c.monto_interes_mora_bs,
                "monto_total_bs": c.monto_total_bs,
                "monto_base_usd": c.monto_base_usd,
                "monto_interes_mora_usd": c.monto_interes_mora_usd,
                "monto_total_usd": c.monto_total_usd,
                "fecha_vencimiento": c.fecha_vencimiento.isoformat() if c.fecha_vencimiento else None,
                "estado": c.estado,
                "dias_atraso": (hoy - c.fecha_vencimiento).days if c.estado == "pendiente" and hoy > c.fecha_vencimiento else 0
            } for c in cuotas
        ]
    }