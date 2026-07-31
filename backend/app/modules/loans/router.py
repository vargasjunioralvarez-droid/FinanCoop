# backend/app/modules/loans/router.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Optional
from datetime import datetime, timedelta, timezone
import random
import logging

from app.core.database import get_db
from app.modules.users.models import Cliente
from app.modules.loans.models import Financiamiento, Cuota
from app.modules.payments.models import Pago
from app.modules.loans.schemas import FinanciamientoCreate, AprobacionExtra
from app.shared.utils import (
    calcular_nivel,
    actualizar_score_cliente,
    calcular_usado_disponible,
    obtener_tasa_actual
)
from app.core.security import get_current_admin, get_current_user, get_current_tienda
from app.core.audit import audit, registrar_auditoria  # ✅ NUEVO

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/financiamientos", tags=["Financiamientos"])

MAX_CREDITOS_ACTIVOS = 3


@router.post("")
@audit(accion="CREAR_FINANCIAMIENTO", tabla="financiamientos")
def crear_financiamiento(
    f: FinanciamientoCreate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    try:
        # Verificar permisos según rol
        if current_user.rol == "cliente":
            if f.cliente_id != current_user.id:
                raise HTTPException(status_code=403, detail="No puedes crear un financiamiento para otro cliente")
        else:
            if current_user.rol != "admin_central" and current_user.tienda_id:
                cliente_verif = db.query(Cliente).filter(Cliente.id == f.cliente_id).first()
                if not cliente_verif:
                    raise HTTPException(status_code=404, detail="Cliente no encontrado")
                if cliente_verif.tienda_id != current_user.tienda_id:
                    raise HTTPException(status_code=403, detail="El cliente no pertenece a tu tienda")

        # Delegar la lógica de negocio al servicio
        from app.services.financiamiento_service import FinanciamientoService

        tienda_id = None
        if hasattr(current_user, 'tienda_id') and current_user.tienda_id:
            tienda_id = current_user.tienda_id

        resultado = FinanciamientoService.crear(
            db=db,
            cliente_id=f.cliente_id,
            monto_total_bs=f.monto_total_bs,
            cuotas_solicitadas=f.cuotas_solicitadas,
            descripcion=f.descripcion,
            numero_factura=f.numero_factura,
            tienda_id=tienda_id,
            usuario_rol=current_user.rol,
            usuario_tienda_id=getattr(current_user, 'tienda_id', None),
            usuario_id=current_user.id
        )

        return resultado

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail="Error interno del servidor")


@router.post("/{id}/aprobar")
@audit(accion="APROBAR_FINANCIAMIENTO", tabla="financiamientos")  # ✅ NUEVO
def aprobar_financiamiento(
    id: int, 
    aprobacion: AprobacionExtra, 
    db: Session = Depends(get_db), 
    current_admin = Depends(get_current_admin)
):
    try:
        fin = db.query(Financiamiento).filter(Financiamiento.id == id).first()
        if not fin: 
            raise HTTPException(status_code=404, detail="Financiamiento no encontrado")
        if not fin.requiere_aprobacion: 
            raise HTTPException(status_code=400, detail="No requiere aprobación")
        
        fin.cuotas_aprobadas = aprobacion.cuotas_aprobadas
        fin.aprobado_por = aprobacion.aprobado_por
        fin.requiere_aprobacion = False
        
        db.query(Cuota).filter(Cuota.financiamiento_id == fin.id).delete()
        monto_cuota_bs = fin.monto_financia_bs / aprobacion.cuotas_aprobadas if aprobacion.cuotas_aprobadas > 0 else 0
        monto_cuota_usd = fin.monto_financia_usd / aprobacion.cuotas_aprobadas if aprobacion.cuotas_aprobadas > 0 else 0
        
        for i in range(1, aprobacion.cuotas_aprobadas + 1):
            cuota = Cuota(
                financiamiento_id=fin.id, 
                numero=i, 
                monto_base_bs=monto_cuota_bs, 
                monto_total_bs=monto_cuota_bs, 
                monto_base_usd=monto_cuota_usd, 
                monto_total_usd=monto_cuota_usd, 
                fecha_vencimiento=fin.fecha_primera_cuota + timedelta(days=15 * (i - 1)), 
                estado="pendiente"
            )
            db.add(cuota)
        
        fin.monto_cuota_bs = monto_cuota_bs
        fin.monto_cuota_usd = monto_cuota_usd
        db.commit()
        
        # ✅ NUEVO: Registrar auditoría manual con detalles
        registrar_auditoria(
            db=db,
            usuario_id=current_admin.id,
            usuario_nombre=current_admin.nombre,
            usuario_rol=current_admin.rol,
            accion="APROBAR_FINANCIAMIENTO",
            tabla="financiamientos",
            registro_id=fin.id,
            detalles=f"Financiamiento #{fin.codigo} aprobado con {aprobacion.cuotas_aprobadas} cuotas por {current_admin.nombre}"
        )
        
        return {
            "success": True, 
            "mensaje": f"Aprobado con {aprobacion.cuotas_aprobadas} cuotas", 
            "aprobado_por": aprobacion.aprobado_por
        }
    except HTTPException: raise
    except Exception as e: 
        db.rollback() 
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/cliente/{cliente_id}/activos")
def get_financiamientos_activos_cliente(
    cliente_id: int, 
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Ver financiamientos activos de un cliente (sin filtro de tienda, para cajeros al buscar)."""
    try:
        activos = db.query(Financiamiento).filter(
            Financiamiento.cliente_id == cliente_id,
            Financiamiento.estado == "activo"
        ).order_by(Financiamiento.id.desc()).all()
        
        resultado = []
        for fin in activos:
            cuotas_pagadas = db.query(Cuota).filter(
                Cuota.financiamiento_id == fin.id, 
                Cuota.estado == "pagada"
            ).count()
            
            resultado.append({
                "id": fin.id,
                "codigo": fin.codigo,
                "descripcion": fin.descripcion,
                "numero_factura": fin.numero_factura,
                "tienda_nombre": fin.tienda.nombre if fin.tienda else None,
                "cuotas_aprobadas": fin.cuotas_aprobadas,
                "cuotas_pagadas": cuotas_pagadas,
                "estado": fin.estado,
                "monto_total_bs": round(fin.monto_total_bs, 2),
                "monto_total_usd": round(fin.monto_total_usd, 2)
            })
        
        return {"total": len(resultado), "financiamientos": resultado}
    except Exception as e:
        logger.error(f"❌ Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("")
def listar_financiamientos(
    skip: int = 0, 
    limit: int = 50, 
    estado: str = None, 
    cliente_id: Optional[int] = None,
    db: Session = Depends(get_db), 
    current_user = Depends(get_current_user), 
    tienda_id: Optional[int] = Depends(get_current_tienda)
):
    try:
        query = db.query(Financiamiento)
        if tienda_id: 
            query = query.filter(Financiamiento.tienda_id == tienda_id)
        if cliente_id: 
            query = query.filter(Financiamiento.cliente_id == cliente_id)
        if estado: 
            query = query.filter(Financiamiento.estado == estado)
        
        total = query.count()
        financiamientos = query.order_by(Financiamiento.id.desc()).offset(skip).limit(limit).all()
        
        resultado = []
        for fin in financiamientos:
            cliente = db.query(Cliente).filter(Cliente.id == fin.cliente_id).first()
            cuotas_pagadas = db.query(Cuota).filter(Cuota.financiamiento_id == fin.id, Cuota.estado == "pagada").count()
            resultado.append({
                "id": fin.id, "codigo": fin.codigo, "cliente_id": fin.cliente_id,
                "cliente_nombre": cliente.nombre if cliente else "Desconocido",
                "descripcion": fin.descripcion,
                "monto_total_bs": round(fin.monto_total_bs, 2),
                "monto_total_usd": round(fin.monto_total_usd, 2),
                "monto_entrada_bs": round(fin.monto_entrada_bs, 2),
                "monto_entrada_usd": round(fin.monto_entrada_usd, 2),
                "cuotas_aprobadas": fin.cuotas_aprobadas,
                "cuotas_pagadas": cuotas_pagadas,
                "estado": fin.estado,
                "tienda_id": fin.tienda_id,
                "tienda_nombre": fin.tienda.nombre if fin.tienda else None,
                "creado_en": fin.creado_en.isoformat() if fin.creado_en else None,
                "url_factura": fin.url_factura,
                "numero_factura": fin.numero_factura
            })
        
        return {
            "total": total, 
            "skip": skip, 
            "limit": limit, 
            "tienda_filtro": tienda_id, 
            "cliente_filtro": cliente_id, 
            "financiamientos": resultado
        }
    except Exception as e: 
        logger.error(f"❌ Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{id}")
def obtener_financiamiento(
    id: int, 
    db: Session = Depends(get_db), 
    current_user = Depends(get_current_user)
):
    try:
        fin = db.query(Financiamiento).filter(Financiamiento.id == id).first()
        if not fin: 
            raise HTTPException(status_code=404, detail="Financiamiento no encontrado")
        
        cliente = db.query(Cliente).filter(Cliente.id == fin.cliente_id).first()
        cuotas = db.query(Cuota).filter(Cuota.financiamiento_id == fin.id).order_by(Cuota.numero).all()
        
        return {
            "id": fin.id, "codigo": fin.codigo,
            "cliente": {"id": cliente.id if cliente else None, "nombre": cliente.nombre if cliente else "Desconocido"},
            "monto_total_bs": round(fin.monto_total_bs, 2),
            "monto_total_usd": round(fin.monto_total_usd, 2),
            "tasa_aplicada": fin.tasa_aplicada,
            "cuotas_aprobadas": fin.cuotas_aprobadas,
            "estado": fin.estado,
            "tienda_nombre": fin.tienda.nombre if fin.tienda else None,
            "url_factura": fin.url_factura,
            "numero_factura": fin.numero_factura,
            "cuotas": [{"id": c.id, "numero": c.numero, "monto_total_bs": round(c.monto_total_bs, 2), "fecha_vencimiento": c.fecha_vencimiento.isoformat() if c.fecha_vencimiento else None, "estado": c.estado} for c in cuotas]
        }
    except HTTPException: raise
    except Exception as e: 
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{id}/cuotas")
def ver_cuotas(
    id: int, 
    db: Session = Depends(get_db), 
    current_user = Depends(get_current_user)
):
    try:
        fin = db.query(Financiamiento).filter(Financiamiento.id == id).first()
        if not fin: 
            raise HTTPException(status_code=404, detail="Financiamiento no encontrado")
        
        cuotas = db.query(Cuota).filter(Cuota.financiamiento_id == id).order_by(Cuota.numero).all()
        hoy = datetime.now(timezone.utc)
        
        return {
            "financiamiento_id": id, 
            "codigo": fin.codigo, 
            "cuotas": [{
                "id": c.id, 
                "numero": c.numero, 
                "monto_base_bs": round(c.monto_base_bs, 2), 
                "monto_total_bs": round(c.monto_total_bs, 2), 
                "fecha_vencimiento": c.fecha_vencimiento.isoformat() if c.fecha_vencimiento else None, 
                "estado": c.estado, 
                "dias_atraso": (hoy - c.fecha_vencimiento).days if c.estado == "pendiente" and hoy > c.fecha_vencimiento else 0
            } for c in cuotas]
        }
    except HTTPException: raise
    except Exception as e: 
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{id}")
@audit(accion="ELIMINAR_FINANCIAMIENTO", tabla="financiamientos")  # ✅ NUEVO
def eliminar_financiamiento(
    id: int, 
    db: Session = Depends(get_db), 
    current_admin = Depends(get_current_admin)
):
    try:
        financiamiento = db.query(Financiamiento).filter(Financiamiento.id == id).first()
        if not financiamiento: 
            raise HTTPException(status_code=404, detail="Financiamiento no encontrado")
        if financiamiento.estado == "completado": 
            raise HTTPException(status_code=400, detail="No se puede eliminar un financiamiento completado")
        
        # ✅ NUEVO: Guardar datos ANTES de eliminar
        datos_antes = {
            "codigo": financiamiento.codigo,
            "cliente_id": financiamiento.cliente_id,
            "monto_total_bs": financiamiento.monto_total_bs,
            "estado": financiamiento.estado,
            "cuotas_aprobadas": financiamiento.cuotas_aprobadas
        }
        
        db.query(Pago).filter(Pago.financiamiento_id == id).delete(synchronize_session='fetch')
        
        cuotas = db.query(Cuota).filter(Cuota.financiamiento_id == id).all()
        for cuota in cuotas:
            db.delete(cuota)
        
        db.delete(financiamiento)
        db.commit()
        
        # ✅ NUEVO: Registrar auditoría manual con detalles
        registrar_auditoria(
            db=db,
            usuario_id=current_admin.id,
            usuario_nombre=current_admin.nombre,
            usuario_rol=current_admin.rol,
            accion="ELIMINAR_FINANCIAMIENTO",
            tabla="financiamientos",
            registro_id=id,
            datos_antes=datos_antes,
            detalles=f"Financiamiento #{id} ({datos_antes['codigo']}) eliminado por {current_admin.nombre}"
        )
        
        return {"success": True, "mensaje": f"Financiamiento #{id} eliminado"}
    except HTTPException: 
        raise
    except Exception as e: 
        logger.error(f"❌ Error eliminando financiamiento {id}: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))