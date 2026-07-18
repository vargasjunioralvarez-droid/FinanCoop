# backend/app/routers/admin.py
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
import logging

from app.database import get_db
from app.models import Usuario, Cliente, Financiamiento, Pago, Cuota
from app.auth import get_current_admin, hash_password, verify_password

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/admin", tags=["Administración"])

# ============================================================
# SCHEMAS
# ============================================================
class UsuarioCreate(BaseModel):
    username: str
    password: str
    nombre: Optional[str] = None
    email: Optional[str] = None
    rol: str = "usuario"
    activo: bool = True

class UsuarioUpdate(BaseModel):
    password: Optional[str] = None
    nombre: Optional[str] = None
    email: Optional[str] = None
    rol: Optional[str] = None
    activo: Optional[bool] = None

# ============================================================
# DASHBOARD
# ============================================================
@router.get("/dashboard")
def dashboard(
    db: Session = Depends(get_db),
    current_user = Depends(get_current_admin)
):
    """Panel de control con estadísticas generales."""
    try:
        total_clientes = db.query(Cliente).count()
        clientes_pendientes = db.query(Cliente).filter(Cliente.estado == "pendiente").count()
        clientes_aprobados = db.query(Cliente).filter(Cliente.estado == "aprobado").count()
        
        total_financiamientos = db.query(Financiamiento).count()
        financiamientos_activos = db.query(Financiamiento).filter(Financiamiento.estado == "activo").count()
        financiamientos_completados = db.query(Financiamiento).filter(Financiamiento.estado == "completado").count()
        
        pagos_pendientes = db.query(Pago).filter(Pago.estado == "pendiente").count()
        
        return {
            "clientes": {
                "total": total_clientes,
                "pendientes": clientes_pendientes,
                "aprobados": clientes_aprobados
            },
            "financiamientos": {
                "total": total_financiamientos,
                "activos": financiamientos_activos,
                "completados": financiamientos_completados
            },
            "pagos_pendientes": pagos_pendientes
        }
    except Exception as e:
        logger.error(f"❌ Error en dashboard: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ============================================================
# LISTAR USUARIOS (SOLO ADMIN)
# ============================================================
@router.get("/usuarios")
def listar_usuarios(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_admin)
):
    """Listar usuarios del panel administrativo."""
    try:
        total = db.query(Usuario).count()
        usuarios = db.query(Usuario).order_by(Usuario.id).offset(skip).limit(limit).all()
        
        return {
            "total": total,
            "skip": skip,
            "limit": limit,
            "usuarios": [
                {
                    "id": u.id,
                    "username": u.username,
                    "nombre": u.nombre,
                    "email": u.email,
                    "rol": u.rol,
                    "activo": u.activo,
                    "ultimo_acceso": u.ultimo_acceso.isoformat() if u.ultimo_acceso else None,
                    "creado_en": u.creado_en.isoformat() if u.creado_en else None
                }
                for u in usuarios
            ]
        }
    except Exception as e:
        logger.error(f"❌ Error listando usuarios: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ============================================================
# CREAR USUARIO (SOLO ADMIN)
# ============================================================
@router.post("/usuarios")
def crear_usuario(
    usuario_data: UsuarioCreate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_admin)
):
    """Crear nuevo usuario del panel (admin, cajero, etc)."""
    try:
        existe = db.query(Usuario).filter(Usuario.username == usuario_data.username).first()
        if existe:
            raise HTTPException(status_code=409, detail="El usuario ya existe")
        
        if len(usuario_data.password) < 8:
            raise HTTPException(status_code=400, detail="La contraseña debe tener al menos 8 caracteres")
        
        nuevo = Usuario(
            username=usuario_data.username,
            password=hash_password(usuario_data.password),
            nombre=usuario_data.nombre,
            email=usuario_data.email,
            rol=usuario_data.rol,
            activo=usuario_data.activo,
            creado_por=current_user.username
        )
        db.add(nuevo)
        db.commit()
        db.refresh(nuevo)
        
        logger.info(f"✅ Usuario creado: {nuevo.username} por {current_user.username}")
        
        return {
            "id": nuevo.id,
            "username": nuevo.username,
            "nombre": nuevo.nombre,
            "email": nuevo.email,
            "rol": nuevo.rol,
            "activo": nuevo.activo
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error creando usuario: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

# ============================================================
# ACTUALIZAR USUARIO (SOLO ADMIN)
# ============================================================
@router.put("/usuarios/{id}")
def actualizar_usuario(
    id: int,
    usuario_data: UsuarioUpdate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_admin)
):
    """Actualizar datos de un usuario del panel."""
    try:
        usuario = db.query(Usuario).filter(Usuario.id == id).first()
        if not usuario:
            raise HTTPException(status_code=404, detail="Usuario no encontrado")
        
        if usuario_data.password:
            if len(usuario_data.password) < 8:
                raise HTTPException(status_code=400, detail="La contraseña debe tener al menos 8 caracteres")
            usuario.password = hash_password(usuario_data.password)
        if usuario_data.nombre is not None:
            usuario.nombre = usuario_data.nombre
        if usuario_data.email is not None:
            usuario.email = usuario_data.email
        if usuario_data.rol is not None:
            usuario.rol = usuario_data.rol
        if usuario_data.activo is not None:
            usuario.activo = usuario_data.activo
        
        db.commit()
        db.refresh(usuario)
        
        logger.info(f"✅ Usuario actualizado: {usuario.username} por {current_user.username}")
        
        return {
            "id": usuario.id,
            "username": usuario.username,
            "nombre": usuario.nombre,
            "email": usuario.email,
            "rol": usuario.rol,
            "activo": usuario.activo
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error actualizando usuario: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

# ============================================================
# ELIMINAR USUARIO (SOLO ADMIN)
# ============================================================
@router.delete("/usuarios/{id}")
def eliminar_usuario(
    id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_admin)
):
    """Eliminar un usuario del panel."""
    try:
        usuario = db.query(Usuario).filter(Usuario.id == id).first()
        if not usuario:
            raise HTTPException(status_code=404, detail="Usuario no encontrado")
        
        if usuario.id == current_user.id:
            raise HTTPException(status_code=403, detail="No puedes eliminar tu propio usuario")
        
        db.delete(usuario)
        db.commit()
        
        logger.info(f"🗑️ Usuario eliminado: {usuario.username} por {current_user.username}")
        
        return {"mensaje": f"Usuario {usuario.username} eliminado"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error eliminando usuario: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

# ============================================================
# CLIENTES PENDIENTES
# ============================================================
@router.get("/clientes/pendientes")
def clientes_pendientes(
    db: Session = Depends(get_db),
    current_user = Depends(get_current_admin)
):
    """Listar clientes pendientes de aprobación."""
    try:
        clientes = db.query(Cliente).filter(Cliente.estado == "pendiente").order_by(Cliente.creado_en.desc()).all()
        
        return {
            "total": len(clientes),
            "clientes": [
                {
                    "id": c.id,
                    "nombre": c.nombre,
                    "cedula": c.cedula,
                    "telefono": c.telefono,
                    "email": c.email,
                    "url_cedula": c.url_cedula,
                    "creado_en": c.creado_en.isoformat() if c.creado_en else None
                }
                for c in clientes
            ]
        }
    except Exception as e:
        logger.error(f"❌ Error listando pendientes: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ============================================================
# FINANCIAMIENTOS PENDIENTES DE APROBACIÓN
# ============================================================
@router.get("/financiamientos/pendientes")
def financiamientos_pendientes(
    db: Session = Depends(get_db),
    current_user = Depends(get_current_admin)
):
    """Listar financiamientos que requieren aprobación extra."""
    try:
        fins = db.query(Financiamiento).filter(
            Financiamiento.requiere_aprobacion == True,
            Financiamiento.estado == "activo"
        ).order_by(Financiamiento.creado_en.desc()).all()
        
        resultado = []
        for fin in fins:
            cliente = db.query(Cliente).filter(Cliente.id == fin.cliente_id).first()
            resultado.append({
                "id": fin.id,
                "codigo": fin.codigo,
                "cliente_nombre": cliente.nombre if cliente else "Desconocido",
                "cliente_cedula": cliente.cedula if cliente else "",
                "monto_total_bs": round(fin.monto_total_bs, 2),
                "monto_total_usd": round(fin.monto_total_usd, 2),
                "cuotas_solicitadas": fin.cuotas_solicitadas,
                "nivel_cliente": cliente.nivel if cliente else "",
                "creado_en": fin.creado_en.isoformat() if fin.creado_en else None
            })
        
        return {"total": len(resultado), "financiamientos": resultado}
    except Exception as e:
        logger.error(f"❌ Error listando financiamientos pendientes: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ============================================================
# REPORTES
# ============================================================
@router.get("/reportes")
def reportes(
    db: Session = Depends(get_db),
    current_user = Depends(get_current_admin)
):
    """Generar reportes del sistema."""
    try:
        total_clientes = db.query(Cliente).count()
        total_creditos = db.query(Financiamiento).count()
        creditos_activos = db.query(Financiamiento).filter(Financiamiento.estado == "activo").count()
        creditos_completados = db.query(Financiamiento).filter(Financiamiento.estado == "completado").count()
        pagos_pendientes = db.query(Pago).filter(Pago.estado == "pendiente").count()
        pagos_conciliados = db.query(Pago).filter(Pago.estado == "conciliado").count()
        
        return {
            "fecha_reporte": datetime.now(timezone.utc).isoformat(),
            "clientes": {
                "total": total_clientes
            },
            "creditos": {
                "total": total_creditos,
                "activos": creditos_activos,
                "completados": creditos_completados
            },
            "pagos": {
                "pendientes": pagos_pendientes,
                "conciliados": pagos_conciliados
            }
        }
    except Exception as e:
        logger.error(f"❌ Error generando reportes: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Necesario para el reporte
from datetime import datetime, timezone