"""
📋 Router para consultar auditoría
Solo accesible por admin_central
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, desc, and_
from datetime import datetime, timedelta
from typing import Optional

from app.core.database import get_db
from app.core.security import get_current_admin
from app.modules.users.models import Usuario
from app.modules.audit.models import Auditoria
from app.modules.audit.schemas import AuditoriaResponse, AuditoriaFiltros, EstadisticasAuditoria

router = APIRouter(prefix="/audit", tags=["Auditoría"])

@router.get("/logs")
def obtener_logs(
    filtros: AuditoriaFiltros = Depends(),
    db: Session = Depends(get_db),
    current_admin: Usuario = Depends(get_current_admin)
):
    """
    Obtener registros de auditoría con filtros
    Solo admin_central puede ver TODOS los logs
    admin_tienda ve logs de su tienda
    """
    # Verificar permisos
    if current_admin.rol not in ["admin_central", "admin_tienda"]:
        raise HTTPException(status_code=403, detail="Permisos insuficientes")
    
    query = db.query(Auditoria)
    
    # Filtrar por usuario
    if filtros.usuario_id:
        query = query.filter(Auditoria.usuario_id == filtros.usuario_id)
    
    # Filtrar por acción
    if filtros.accion:
        query = query.filter(Auditoria.accion == filtros.accion)
    
    # Filtrar por tabla
    if filtros.tabla:
        query = query.filter(Auditoria.tabla == filtros.tabla)
    
    # Filtrar por registro
    if filtros.registro_id:
        query = query.filter(Auditoria.registro_id == filtros.registro_id)
    
    # Filtrar por fecha
    if filtros.fecha_desde:
        query = query.filter(Auditoria.fecha >= filtros.fecha_desde)
    if filtros.fecha_hasta:
        query = query.filter(Auditoria.fecha <= filtros.fecha_hasta)
    
    # Si es admin_tienda, filtrar por usuarios de su tienda
    if current_admin.rol == "admin_tienda" and current_admin.tienda_id:
        # Obtener IDs de usuarios de esta tienda
        usuarios_tienda = db.query(Usuario.id).filter(
            Usuario.tienda_id == current_admin.tienda_id
        ).all()
        usuarios_ids = [u[0] for u in usuarios_tienda]
        query = query.filter(Auditoria.usuario_id.in_(usuarios_ids))
    
    # Total de registros
    total = query.count()
    
    # Ordenar y paginar
    logs = query.order_by(desc(Auditoria.fecha)).offset(filtros.offset).limit(filtros.limite).all()
    
    return {
        "total": total,
        "limite": filtros.limite,
        "offset": filtros.offset,
        "logs": [AuditoriaResponse.model_validate(log).model_dump() for log in logs]
    }

@router.get("/logs/usuario/{usuario_id}")
def logs_usuario(
    usuario_id: int,
    limite: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db),
    current_admin: Usuario = Depends(get_current_admin)
):
    """Obtener logs de un usuario específico"""
    if current_admin.rol not in ["admin_central"]:
        raise HTTPException(status_code=403, detail="Solo admin_central puede ver logs de otros usuarios")
    
    logs = db.query(Auditoria).filter(
        Auditoria.usuario_id == usuario_id
    ).order_by(desc(Auditoria.fecha)).limit(limite).all()
    
    return {
        "usuario_id": usuario_id,
        "total": len(logs),
        "logs": [AuditoriaResponse.model_validate(log).model_dump() for log in logs]
    }

@router.get("/estadisticas")
def estadisticas_auditoria(
    dias: int = Query(7, ge=1, le=90),
    db: Session = Depends(get_db),
    current_admin: Usuario = Depends(get_current_admin)
):
    """Estadísticas de auditoría"""
    if current_admin.rol not in ["admin_central", "admin_tienda"]:
        raise HTTPException(status_code=403, detail="Permisos insuficientes")
    
    fecha_corte = datetime.now() - timedelta(days=dias)
    
    query = db.query(Auditoria).filter(Auditoria.fecha >= fecha_corte)
    
    # Si es admin_tienda, filtrar
    if current_admin.rol == "admin_tienda" and current_admin.tienda_id:
        usuarios_tienda = db.query(Usuario.id).filter(
            Usuario.tienda_id == current_admin.tienda_id
        ).all()
        usuarios_ids = [u[0] for u in usuarios_tienda]
        query = query.filter(Auditoria.usuario_id.in_(usuarios_ids))
    
    # Total
    total = query.count()
    
    # Por acción
    acciones = query.with_entities(
        Auditoria.accion, func.count(Auditoria.id)
    ).group_by(Auditoria.accion).all()
    por_accion = {a[0]: a[1] for a in acciones}
    
    # Por usuario
    usuarios = query.with_entities(
        Auditoria.usuario_nombre, func.count(Auditoria.id)
    ).group_by(Auditoria.usuario_nombre).order_by(func.count(Auditoria.id).desc()).limit(10).all()
    por_usuario = {u[0] or "sistema": u[1] for u in usuarios}
    
    # Por tabla
    tablas = query.with_entities(
        Auditoria.tabla, func.count(Auditoria.id)
    ).group_by(Auditoria.tabla).all()
    por_tabla = {t[0] or "N/A": t[1] for t in tablas}
    
    # Última semana
    ultima_semana = db.query(Auditoria).filter(
        Auditoria.fecha >= fecha_corte
    ).count()
    
    # Hoy
    hoy = datetime.now().date()
    hoy_count = db.query(Auditoria).filter(
        func.date(Auditoria.fecha) == hoy
    ).count()
    
    return {
        "total_acciones": total,
        "por_accion": por_accion,
        "por_usuario": por_usuario,
        "por_tabla": por_tabla,
        "ultima_semana": ultima_semana,
        "hoy": hoy_count,
        "periodo_dias": dias
    }

@router.get("/reciente")
def logs_recientes(
    limite: int = Query(50, ge=1, le=500),
    db: Session = Depends(get_db),
    current_admin: Usuario = Depends(get_current_admin)
):
    """Últimos logs de auditoría"""
    if current_admin.rol not in ["admin_central", "admin_tienda"]:
        raise HTTPException(status_code=403, detail="Permisos insuficientes")
    
    query = db.query(Auditoria)
    
    if current_admin.rol == "admin_tienda" and current_admin.tienda_id:
        usuarios_tienda = db.query(Usuario.id).filter(
            Usuario.tienda_id == current_admin.tienda_id
        ).all()
        usuarios_ids = [u[0] for u in usuarios_tienda]
        query = query.filter(Auditoria.usuario_id.in_(usuarios_ids))
    
    logs = query.order_by(desc(Auditoria.fecha)).limit(limite).all()
    
    return {
        "total": len(logs),
        "logs": [AuditoriaResponse.model_validate(log).model_dump() for log in logs]
    }