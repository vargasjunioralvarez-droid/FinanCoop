# backend/app/modules/mobile/router.py
from fastapi import APIRouter, Depends, Response, Header, HTTPException, status
from sqlalchemy.orm import Session
from datetime import datetime, timezone
import logging

from app.core.database import get_db
from app.modules.users.models import Cliente
from app.modules.loans.models import Financiamiento, Cuota
from app.modules.payments.models import ConfiguracionPago
from app.shared.utils import (
    generar_token,
    obtener_tasa_actual,
    calcular_usado_disponible,
    actualizar_score_cliente,
    calcular_nivel
)
from app.core.security import (
    get_current_user,
    get_current_cliente,
    verify_pin,
    hash_pin
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/app", tags=["App Móvil"])

def obtener_token(token_query: str = None, authorization: str = Header(None)):
    """Extraer token de query param O header Authorization."""
    if authorization and isinstance(authorization, str) and authorization.startswith("Bearer "):
        return authorization.replace("Bearer ", "").strip()
    if authorization and isinstance(authorization, str) and len(authorization) > 10:
        return authorization.strip()
    if token_query and isinstance(token_query, str):
        return token_query.strip()
    return None

@router.options("/login")
def options_login():
    return Response(status_code=200)

# ============================================================
# MI PERFIL
# ============================================================
@router.get("/mi-perfil")
def mi_perfil(
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Obtener perfil del cliente logueado."""
    try:
        if hasattr(current_user, 'rol') and current_user.rol == "admin":
            raise HTTPException(status_code=403, detail="Endpoint solo para clientes")
        
        cliente_id = current_user.id
        
        cliente = db.query(Cliente).filter(Cliente.id == cliente_id).first()
        if not cliente:
            raise HTTPException(status_code=404, detail="Cliente no encontrado")

        actualizar_score_cliente(cliente, db)
        db.refresh(cliente)

        return {
            "id": cliente.id,
            "nombre": cliente.nombre,
            "cedula": cliente.cedula,
            "telefono": cliente.telefono,
            "email": cliente.email,
            "direccion": cliente.direccion,
            "referencia_nombre": cliente.referencia_nombre,
            "referencia_telefono": cliente.referencia_telefono,
            "referencia_parentesco": cliente.referencia_parentesco,
            "score": cliente.score,
            "nivel": cliente.nivel,
            "total_compras": cliente.total_compras,
            "url_cedula": cliente.url_cedula,
            "estado": cliente.estado or "pendiente"
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ [mi-perfil] Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ============================================================
# MIS DATOS (Dashboard principal de la app)
# ============================================================
@router.get("/mis-datos")
def mis_datos(
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Obtener todos los datos del cliente para el dashboard."""
    try:
        if hasattr(current_user, 'rol') and current_user.rol == "admin":
            raise HTTPException(status_code=403, detail="Endpoint solo para clientes")
        
        cliente_id = current_user.id
        
        cliente = db.query(Cliente).filter(Cliente.id == cliente_id).first()
        if not cliente:
            raise HTTPException(status_code=404, detail="Cliente no encontrado")

        actualizar_score_cliente(cliente, db)
        db.refresh(cliente)

        tasa = obtener_tasa_actual(db)
        disponible = calcular_usado_disponible(cliente.id, db)

        activos = db.query(Financiamiento).filter(
            Financiamiento.cliente_id == cliente.id,
            Financiamiento.estado == "activo"
        ).all()

        hoy = datetime.now(timezone.utc)

        financiamientos_data = []
        for fin in activos:
            cuotas = db.query(Cuota).filter(Cuota.financiamiento_id == fin.id).order_by(Cuota.numero).all()

            cuotas_pendientes = [c for c in cuotas if c.estado in ["pendiente", "conciliando"]]
            cuotas_atrasadas = [c for c in cuotas if c.estado == "pendiente" and hoy > c.fecha_vencimiento]

            proxima_cuota = None
            if cuotas_pendientes:
                proxima = cuotas_pendientes[0]
                dias_para_vencer = (proxima.fecha_vencimiento - hoy).days if proxima.fecha_vencimiento else 0

                proxima_cuota = {
                    "id": proxima.id,
                    "numero": proxima.numero,
                    "monto_bs": round(proxima.monto_total_bs, 2),
                    "monto_usd_ref": round(proxima.monto_total_usd, 2),
                    "fecha_vencimiento": proxima.fecha_vencimiento.isoformat() if proxima.fecha_vencimiento else None,
                    "dias_para_vencer": max(0, dias_para_vencer),
                    "estado": proxima.estado
                }

            financiamientos_data.append({
                "id": fin.id,
                "codigo": fin.codigo,
                "descripcion": fin.descripcion,
                "url_factura": fin.url_factura,
                "numero_factura": fin.numero_factura,
                "monto_total_bs": round(fin.monto_total_bs, 2),
                "monto_total_usd_ref": round(fin.monto_total_usd, 2),
                "monto_entrada_bs": round(fin.monto_entrada_bs, 2),
                "monto_entrada_usd_ref": round(fin.monto_entrada_usd, 2),
                "cuotas_total": fin.cuotas_aprobadas,
                "cuotas_pagadas": len([c for c in cuotas if c.estado == "pagada"]),
                "cuotas_pendientes": len(cuotas_pendientes),
                "cuotas_atrasadas": len(cuotas_atrasadas),
                "proxima_cuota": proxima_cuota,
                "saldo_pendiente_bs": round(sum(c.monto_total_bs for c in cuotas_pendientes), 2),
                "saldo_pendiente_usd_ref": round(sum(c.monto_total_usd for c in cuotas_pendientes), 2)
            })

        config = db.query(ConfiguracionPago).first()

        return {
            "cliente": {
                "id": cliente.id,
                "nombre": cliente.nombre,
                "cedula": cliente.cedula,
                "nivel": cliente.nivel,
                "score": cliente.score,
                "telefono": cliente.telefono,
                "email": cliente.email,
                "direccion": cliente.direccion,
                "url_cedula": cliente.url_cedula,
                "referencia_nombre": cliente.referencia_nombre,
                "referencia_telefono": cliente.referencia_telefono,
                "referencia_parentesco": cliente.referencia_parentesco,
                "estado": cliente.estado
            },
            "limite": disponible,
            "tasa_actual": tasa,
            "financiamientos_activos": financiamientos_data,
            "total_deuda_bs": round(sum(f["saldo_pendiente_bs"] for f in financiamientos_data), 2),
            "total_deuda_usd_ref": round(sum(f["saldo_pendiente_usd_ref"] for f in financiamientos_data), 2),
            "datos_pago": {
                "pago_movil": {
                    "banco": config.banco_pago_movil if config else "",
                    "telefono": config.telefono_pago_movil if config else "",
                    "cedula": config.cedula_pago_movil if config else ""
                },
                "transferencia": {
                    "banco": config.banco_transferencia if config else "",
                    "cuenta": config.cuenta_transferencia if config else ""
                },
                "zelle": getattr(config, 'correo_zelle', None) if config else None,
                "binance": getattr(config, 'correo_binance', None) if config else None
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ [mis-datos] Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ============================================================
# MIS CUOTAS
# ============================================================
@router.get("/mis-cuotas")
def mis_cuotas(
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Obtener todas las cuotas del cliente."""
    try:
        if hasattr(current_user, 'rol') and current_user.rol == "admin":
            raise HTTPException(status_code=403, detail="Endpoint solo para clientes")
        
        cliente_id = current_user.id
        
        cliente = db.query(Cliente).filter(Cliente.id == cliente_id).first()
        if not cliente:
            raise HTTPException(status_code=404, detail="Cliente no encontrado")

        tasa = obtener_tasa_actual(db)

        financiamientos = db.query(Financiamiento).filter(
            Financiamiento.cliente_id == cliente.id
        ).all()

        hoy = datetime.now(timezone.utc)

        todas_cuotas = []
        for fin in financiamientos:
            cuotas = db.query(Cuota).filter(
                Cuota.financiamiento_id == fin.id
            ).order_by(Cuota.numero).all()

            for c in cuotas:
                dias_atraso = 0
                if c.estado == "pendiente" and hoy > c.fecha_vencimiento:
                    dias_atraso = (hoy - c.fecha_vencimiento).days

                todas_cuotas.append({
                    "financiamiento_id": fin.id,
                    "financiamiento_codigo": fin.codigo,
                    "financiamiento_descripcion": fin.descripcion,
                    "cuota_id": c.id,
                    "cuota_numero": c.numero,
                    "monto_base_bs": round(c.monto_base_bs, 2),
                    "monto_interes_bs": round(c.monto_interes_mora_bs, 2),
                    "monto_total_bs": round(c.monto_total_bs, 2),
                    "monto_base_usd_ref": round(c.monto_base_usd, 2),
                    "monto_interes_usd_ref": round(c.monto_interes_mora_usd, 2),
                    "monto_total_usd_ref": round(c.monto_total_usd, 2),
                    "fecha_vencimiento": c.fecha_vencimiento.isoformat() if c.fecha_vencimiento else None,
                    "estado": c.estado,
                    "dias_atraso": dias_atraso,
                    "puede_pagar": c.estado == "pendiente"
                })

        return {
            "cliente": cliente.nombre,
            "tasa_actual": tasa,
            "cuotas": todas_cuotas
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ [mis-cuotas] Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ============================================================
# CONFIGURACIÓN DE PAGOS (PÚBLICA)
# ============================================================
@router.get("/configuracion-pagos")
def configuracion_pagos_publica(db: Session = Depends(get_db)):
    """Obtener métodos de pago configurados (público)."""
    try:
        config = db.query(ConfiguracionPago).first()
        if not config:
            raise HTTPException(status_code=404, detail="Configuración no encontrada")

        return {
            "pago_movil": {
                "banco": config.banco_pago_movil,
                "telefono": config.telefono_pago_movil,
                "cedula": config.cedula_pago_movil
            },
            "transferencia": {
                "banco": config.banco_transferencia,
                "cuenta": config.cuenta_transferencia
            },
            "zelle": getattr(config, 'correo_zelle', None),
            "binance": getattr(config, 'correo_binance', None)
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ [configuracion-pagos] Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ============================================================
# CAMBIAR PIN
# ============================================================
@router.post("/cambiar-pin")
def cambiar_pin(
    data: dict,
    current_user = Depends(get_current_cliente),
    db: Session = Depends(get_db)
):
    """Permite al cliente cambiar su PIN de acceso."""
    pin_actual = data.get("pin_actual")
    pin_nuevo = data.get("pin_nuevo")
    
    if not pin_actual or not pin_nuevo:
        raise HTTPException(status_code=400, detail="PIN actual y nuevo son requeridos")
    
    if len(pin_nuevo) < 4:
        raise HTTPException(status_code=400, detail="El PIN debe tener al menos 4 dígitos")
    
    if not verify_pin(pin_actual, current_user.pin_hash):
        raise HTTPException(status_code=400, detail="PIN actual incorrecto")
    
    current_user.pin_hash = hash_pin(pin_nuevo)
    db.commit()
    
    logger.info(f"🔑 PIN cambiado para cliente {current_user.nombre}")
    
    return {"success": True, "mensaje": "PIN actualizado correctamente"}