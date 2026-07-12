# backend/app/routers/admin.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
import logging

from app.database import get_db
from app.models import Usuario
from app.auth import get_current_admin, hash_password, verify_password

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/admin", tags=["Administración"])

# ============================================================
# ✅ SCHEMAS
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
# ✅ LISTAR USUARIOS (SOLO ADMIN) - CON LOGS
# ============================================================
@router.get("/usuarios")
def listar_usuarios(
    db: Session = Depends(get_db),
    current_user = Depends(get_current_admin)
):
    logger.info("=" * 50)
    logger.info("📋 [ADMIN] listar_usuarios - INICIO")
    logger.info(f"📋 [ADMIN] Usuario actual: {current_user.username}")
    logger.info(f"📋 [ADMIN] Rol del usuario: {current_user.rol}")
    
    usuarios = db.query(Usuario).all()
    logger.info(f"📋 [ADMIN] Total usuarios en BD: {len(usuarios)}")
    
    result = [
        {
            "id": u.id,
            "username": u.username,
            "nombre": u.nombre,
            "email": u.email,
            "rol": u.rol,
            "activo": u.activo,
            "creado_en": u.creado_en
        }
        for u in usuarios
    ]
    
    logger.info(f"✅ [ADMIN] Usuarios listados exitosamente")
    logger.info("=" * 50)
    return result

# ============================================================
# ✅ CREAR USUARIO (SOLO ADMIN)
# ============================================================
@router.post("/usuarios")
def crear_usuario(
    usuario_data: UsuarioCreate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_admin)
):
    logger.info(f"➕ [ADMIN] Creando usuario por: {current_user.username}")
    
    # Verificar si el usuario ya existe
    existe = db.query(Usuario).filter(Usuario.username == usuario_data.username).first()
    if existe:
        raise HTTPException(status_code=400, detail="El usuario ya existe")
    
    nuevo = Usuario(
        username=usuario_data.username,
        password=hash_password(usuario_data.password),
        nombre=usuario_data.nombre,
        email=usuario_data.email,
        rol=usuario_data.rol,
        activo=usuario_data.activo
    )
    db.add(nuevo)
    db.commit()
    db.refresh(nuevo)
    
    return {
        "id": nuevo.id,
        "username": nuevo.username,
        "nombre": nuevo.nombre,
        "email": nuevo.email,
        "rol": nuevo.rol,
        "activo": nuevo.activo
    }

# ============================================================
# ✅ ACTUALIZAR USUARIO (SOLO ADMIN)
# ============================================================
@router.put("/usuarios/{id}")
def actualizar_usuario(
    id: int,
    usuario_data: UsuarioUpdate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_admin)
):
    logger.info(f"✏️ [ADMIN] Actualizando usuario {id} por: {current_user.username}")
    
    usuario = db.query(Usuario).filter(Usuario.id == id).first()
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    
    if usuario_data.password:
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
    
    return {
        "id": usuario.id,
        "username": usuario.username,
        "nombre": usuario.nombre,
        "email": usuario.email,
        "rol": usuario.rol,
        "activo": usuario.activo
    }

# ============================================================
# ✅ ELIMINAR USUARIO (SOLO ADMIN)
# ============================================================
@router.delete("/usuarios/{id}")
def eliminar_usuario(
    id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_admin)
):
    logger.info(f"🗑️ [ADMIN] Eliminando usuario {id} por: {current_user.username}")
    
    usuario = db.query(Usuario).filter(Usuario.id == id).first()
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    
    # No permitir eliminar al propio admin
    if usuario.id == current_user.id:
        raise HTTPException(status_code=403, detail="No puedes eliminar tu propio usuario")
    
    db.delete(usuario)
    db.commit()
    return {"mensaje": "Usuario eliminado"}