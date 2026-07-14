# backend/app/routers/app_mobile.py
from fastapi import APIRouter, Depends, Response, Header, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import Cliente, Financiamiento, Cuota, ConfiguracionPago
from app.schemas import LoginApp
from app.utils import generar_token, obtener_tasa_actual, calcular_usado_disponible
from datetime import datetime, timezone

router = APIRouter(prefix="/app", tags=["App Móvil"])

def obtener_token(token_query: str = None, authorization: str = Header(None)):
    """🔥 FIX: Extraer token de query param O header Authorization"""
    if authorization and authorization.startswith("Bearer "):
        return authorization.replace("Bearer ", "")
    return token_query

@router.options("/login")
def options_login():
    return Response(status_code=200)

@router.post("/login")
def login_app(login: LoginApp, db: Session = Depends(get_db)):
    cliente = db.query(Cliente).filter(Cliente.cedula == login.cedula).first()
    if not cliente:
        return {"error": "Cliente no encontrado"}
    
    if cliente.pin != login.pin:
        return {"error": "PIN incorrecto"}
    
    cliente.token_app = generar_token()
    cliente.ultimo_acceso = datetime.now(timezone.utc)
    db.commit()
    
    return {
        "token": cliente.token_app,
        "cliente": {
            "id": cliente.id,
            "nombre": cliente.nombre,
            "nivel": cliente.nivel,
            "score": cliente.score
        }
    }

@router.get("/mi-perfil")
def mi_perfil(
    token: str = None,
    authorization: str = Header(None),
    db: Session = Depends(get_db)
):
    """Obtener perfil del cliente logueado (para app móvil)"""
    token_final = obtener_token(token, authorization)
    
    if not token_final:
        return {"error": "Token no proporcionado"}
    
    cliente = db.query(Cliente).filter(Cliente.token_app == token_final).first()
    if not cliente:
        return {"error": "Sesión no válida"}
    
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
        "estado": cliente.estado or "pendiente",
        "pin": cliente.pin
    }

@router.get("/mis-datos")
def mis_datos(
    token: str = None,
    authorization: str = Header(None),
    db: Session = Depends(get_db)
):
    # 🔥 FIX: Aceptar token de query O header
    token_final = obtener_token(token, authorization)
    
    if not token_final:
        return {"error": "Token no proporcionado"}
    
    cliente = db.query(Cliente).filter(Cliente.token_app == token_final).first()
    if not cliente:
        return {"error": "Sesión no válida"}
    
    tasa = obtener_tasa_actual(db)
    disponible = calcular_usado_disponible(cliente.id, db)
    
    activos = db.query(Financiamiento).filter(
        Financiamiento.cliente_id == cliente.id,
        Financiamiento.estado == "activo"
    ).all()
    
    hoy = datetime.now(timezone.utc)
    
    financiamientos_data = []
    for fin in activos:
        cuotas = db.query(Cuota).filter(Cuota.financiamiento_id == fin.id).all()
        
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
            "telefono": cliente.telefono
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

@router.get("/mis-cuotas")
def mis_cuotas(
    token: str = None,
    authorization: str = Header(None),
    db: Session = Depends(get_db)
):
    # 🔥 FIX: Aceptar token de query O header
    token_final = obtener_token(token, authorization)
    
    if not token_final:
        return {"error": "Token no proporcionado"}
    
    cliente = db.query(Cliente).filter(Cliente.token_app == token_final).first()
    if not cliente:
        return {"error": "Sesión no válida"}
    
    tasa = obtener_tasa_actual(db)
    
    financiamientos = db.query(Financiamiento).filter(
        Financiamiento.cliente_id == cliente.id
    ).all()
    
    hoy = datetime.now(timezone.utc)
    
    todas_cuotas = []
    for fin in financiamientos:
        cuotas = db.query(Cuota).filter(Cuota.financiamiento_id == fin.id).order_by(Cuota.numero).all()
        
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

@router.get("/configuracion-pagos")
def configuracion_pagos_publica(db: Session = Depends(get_db)):
    config = db.query(ConfiguracionPago).first()
    if not config:
        return {"error": "Configuración no encontrada"}
    
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