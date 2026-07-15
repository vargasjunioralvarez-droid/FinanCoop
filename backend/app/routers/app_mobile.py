# backend/app/routers/app_mobile.py
from fastapi import APIRouter, Depends, Response, Header, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import Cliente, Financiamiento, Cuota, ConfiguracionPago, NivelConfig
from app.schemas import LoginApp
from app.utils import generar_token, obtener_tasa_actual, calcular_usado_disponible, actualizar_score_cliente, calcular_nivel
from app.auth import create_access_token, get_current_user  # ← IMPORTAR JWT
from datetime import datetime, timezone
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/app", tags=["App Móvil"])

def obtener_token(token_query: str = None, authorization: str = Header(None)):
    """Extraer token de query param O header Authorization"""
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
# ✅ LOGIN - GENERA JWT
# ============================================================
@router.post("/login")
def login_app(login: LoginApp, db: Session = Depends(get_db)):
    try:
        print(f"🔑 [login] Intentando login para cédula: {login.cedula}")
        
        cliente = db.query(Cliente).filter(Cliente.cedula == login.cedula).first()
        if not cliente:
            print(f"❌ [login] Cliente no encontrado: {login.cedula}")
            return {"error": "Cliente no encontrado"}

        if cliente.pin != login.pin:
            print(f"❌ [login] PIN incorrecto para: {login.cedula}")
            return {"error": "PIN incorrecto"}

        if cliente.estado != "aprobado":
            print(f"❌ [login] Cliente no aprobado: {login.cedula}")
            return {"error": "Tu cuenta está pendiente de aprobación. Contacta a la cooperativa."}

        # ✅ RECALCULAR NIVEL Y SCORE
        actualizar_score_cliente(cliente, db)
        db.refresh(cliente)
        print(f"🔄 [login] Cliente {cliente.nombre} - Nivel: {cliente.nivel}")

        # ✅ GENERAR JWT (NO UUID)
        token_data = {
            "sub": str(cliente.id),  # ID del cliente como subject
            "rol": "cliente",
            "nombre": cliente.nombre,
            "cedula": cliente.cedula
        }
        
        # Usar create_access_token de auth.py
        token = create_access_token(token_data)
        print(f"✅ [login] JWT generado para {cliente.nombre} (ID: {cliente.id})")
        print(f"✅ [login] Token: {token[:50]}...")

        # Actualizar último acceso
        cliente.ultimo_acceso = datetime.now(timezone.utc)
        db.commit()

        return {
            "token": token,
            "cliente": {
                "id": cliente.id,
                "nombre": cliente.nombre,
                "cedula": cliente.cedula,
                "nivel": cliente.nivel,
                "score": cliente.score,
                "telefono": cliente.telefono
            }
        }
        
    except Exception as e:
        print(f"❌ [login] Error: {e}")
        import traceback
        traceback.print_exc()
        return {"error": str(e)}

# ============================================================
# ✅ MI PERFIL - USANDO get_current_user
# ============================================================
@router.get("/mi-perfil")
def mi_perfil(
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Obtener perfil del cliente logueado (para app móvil)"""
    try:
        # Verificar que sea un cliente (no admin)
        if hasattr(current_user, 'rol') and current_user.rol == "admin":
            return {"error": "Endpoint solo para clientes"}
        
        cliente_id = current_user.id
        
        cliente = db.query(Cliente).filter(Cliente.id == cliente_id).first()
        if not cliente:
            return {"error": "Cliente no encontrado"}

        # ✅ RECALCULAR AL OBTENER PERFIL
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
            "estado": cliente.estado or "pendiente",
            "pin": cliente.pin
        }
    except Exception as e:
        print(f"❌ [mi-perfil] Error: {e}")
        return {"error": str(e)}

# ============================================================
# ✅ MIS DATOS - USANDO get_current_user
# ============================================================
@router.get("/mis-datos")
def mis_datos(
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    try:
        # Verificar que sea un cliente (no admin)
        if hasattr(current_user, 'rol') and current_user.rol == "admin":
            return {"error": "Endpoint solo para clientes"}
        
        cliente_id = current_user.id
        
        cliente = db.query(Cliente).filter(Cliente.id == cliente_id).first()
        if not cliente:
            return {"error": "Cliente no encontrado"}

        # ✅ RECALCULAR NIVEL Y SCORE
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
    except Exception as e:
        print(f"❌ [mis-datos] Error: {e}")
        import traceback
        traceback.print_exc()
        return {"error": str(e)}

# ============================================================
# ✅ MIS CUOTAS - USANDO get_current_user
# ============================================================
@router.get("/mis-cuotas")
def mis_cuotas(
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    try:
        # Verificar que sea un cliente (no admin)
        if hasattr(current_user, 'rol') and current_user.rol == "admin":
            return {"error": "Endpoint solo para clientes"}
        
        cliente_id = current_user.id
        
        cliente = db.query(Cliente).filter(Cliente.id == cliente_id).first()
        if not cliente:
            return {"error": "Cliente no encontrado"}

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
    except Exception as e:
        print(f"❌ [mis-cuotas] Error: {e}")
        return {"error": str(e)}

# ============================================================
# ✅ CONFIGURACIÓN DE PAGOS (PÚBLICA)
# ============================================================
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