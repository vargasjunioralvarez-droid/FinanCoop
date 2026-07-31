# backend/app/modules/admin/router.py
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
import logging
from datetime import datetime, timezone

from app.core.database import get_db
from app.modules.users.models import Usuario, Tienda, Cliente
from app.modules.loans.models import Financiamiento
from app.modules.payments.models import Pago
from app.core.security import get_current_admin, hash_password
from app.core.audit import audit, registrar_auditoria
import os
from app.core.backup import crear_backup, listar_backups, restaurar_backup


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
    rol: str = "cajero"
    activo: bool = True
    tienda_id: Optional[int] = None

class UsuarioUpdate(BaseModel):
    password: Optional[str] = None
    nombre: Optional[str] = None
    email: Optional[str] = None
    rol: Optional[str] = None
    activo: Optional[bool] = None
    tienda_id: Optional[int] = None

class TiendaCreate(BaseModel):
    nombre: str
    codigo: str
    direccion: Optional[str] = None
    telefono: Optional[str] = None

class TiendaUpdate(BaseModel):
    nombre: Optional[str] = None
    direccion: Optional[str] = None
    telefono: Optional[str] = None
    activo: Optional[bool] = None

# ============================================================
# DASHBOARD
# ============================================================
@router.get("/dashboard")
def dashboard(db: Session = Depends(get_db), current_user = Depends(get_current_admin)):
    try:
        tienda_id = None if current_user.rol == "admin_central" else current_user.tienda_id
        query_clientes = db.query(Cliente)
        query_financiamientos = db.query(Financiamiento)
        query_pagos = db.query(Pago)
        if tienda_id:
            query_clientes = query_clientes.filter(Cliente.tienda_id == tienda_id)
            query_financiamientos = query_financiamientos.filter(Financiamiento.tienda_id == tienda_id)
            query_pagos = query_pagos.join(Financiamiento).filter(Financiamiento.tienda_id == tienda_id)
        return {
            "tienda": current_user.tienda.nombre if current_user.tienda else "Central",
            "clientes": {"total": query_clientes.count(), "pendientes": query_clientes.filter(Cliente.estado == "pendiente").count(), "aprobados": query_clientes.filter(Cliente.estado == "aprobado").count()},
            "financiamientos": {"total": query_financiamientos.count(), "activos": query_financiamientos.filter(Financiamiento.estado == "activo").count(), "completados": query_financiamientos.filter(Financiamiento.estado == "completado").count()},
            "pagos_pendientes": query_pagos.filter(Pago.estado == "pendiente").count()
        }
    except Exception as e:
        logger.error(f"❌ Error en dashboard: {e}")
        raise HTTPException(status_code=500, detail="Error interno del servidor")
# ============================================================
# CRUD TIENDAS (SOLO admin_central)
# ============================================================
@router.get("/tiendas")
def listar_tiendas(db: Session = Depends(get_db), current_user = Depends(get_current_admin)):
    if current_user.rol != "admin_central":
        raise HTTPException(status_code=403, detail="Solo el administrador central puede gestionar tiendas")
    tiendas = db.query(Tienda).order_by(Tienda.nombre).all()
    return [{"id": t.id, "nombre": t.nombre, "codigo": t.codigo, "direccion": t.direccion, "telefono": t.telefono, "activo": t.activo, "total_clientes": db.query(Cliente).filter(Cliente.tienda_id == t.id).count(), "total_creditos": db.query(Financiamiento).filter(Financiamiento.tienda_id == t.id).count(), "creado_en": t.creado_en.isoformat() if t.creado_en else None} for t in tiendas]

@router.post("/tiendas")
@audit(accion="CREAR_TIENDA", tabla="tiendas")
def crear_tienda(data: TiendaCreate, db: Session = Depends(get_db), current_user = Depends(get_current_admin)):
    if current_user.rol != "admin_central":
        raise HTTPException(status_code=403, detail="Solo el administrador central puede crear tiendas")
    existe = db.query(Tienda).filter(Tienda.codigo == data.codigo).first()
    if existe:
        raise HTTPException(status_code=409, detail="El código de tienda ya existe")
    tienda = Tienda(nombre=data.nombre, codigo=data.codigo.upper(), direccion=data.direccion, telefono=data.telefono)
    db.add(tienda); db.commit(); db.refresh(tienda)
    logger.info(f"✅ Tienda creada: {tienda.nombre} ({tienda.codigo})")
    
    registrar_auditoria(
        db=db,
        usuario_id=current_user.id,
        usuario_nombre=current_user.nombre,
        usuario_rol=current_user.rol,
        accion="CREAR_TIENDA",
        tabla="tiendas",
        registro_id=tienda.id,
        detalles=f"Tienda '{tienda.nombre}' ({tienda.codigo}) creada por {current_user.nombre}"
    )
    
    return {"success": True, "id": tienda.id, "nombre": tienda.nombre}

@router.put("/tiendas/{id}")
@audit(accion="ACTUALIZAR_TIENDA", tabla="tiendas")
def actualizar_tienda(id: int, data: TiendaUpdate, db: Session = Depends(get_db), current_user = Depends(get_current_admin)):
    if current_user.rol != "admin_central":
        raise HTTPException(status_code=403, detail="Solo el administrador central")
    tienda = db.query(Tienda).filter(Tienda.id == id).first()
    if not tienda:
        raise HTTPException(status_code=404, detail="Tienda no encontrada")
    
    datos_antes = {
        "nombre": tienda.nombre,
        "direccion": tienda.direccion,
        "telefono": tienda.telefono,
        "activo": tienda.activo
    }
    
    if data.nombre is not None: tienda.nombre = data.nombre
    if data.direccion is not None: tienda.direccion = data.direccion
    if data.telefono is not None: tienda.telefono = data.telefono
    if data.activo is not None: tienda.activo = data.activo
    db.commit()
    
    registrar_auditoria(
        db=db,
        usuario_id=current_user.id,
        usuario_nombre=current_user.nombre,
        usuario_rol=current_user.rol,
        accion="ACTUALIZAR_TIENDA",
        tabla="tiendas",
        registro_id=id,
        datos_antes=datos_antes,
        detalles=f"Tienda {tienda.nombre} actualizada por {current_user.nombre}"
    )
    
    return {"success": True, "mensaje": "Tienda actualizada"}

@router.delete("/tiendas/{id}")
@audit(accion="ELIMINAR_TIENDA", tabla="tiendas")
def eliminar_tienda(id: int, db: Session = Depends(get_db), current_user = Depends(get_current_admin)):
    if current_user.rol != "admin_central":
        raise HTTPException(status_code=403, detail="Solo el administrador central puede eliminar tiendas")
    tienda = db.query(Tienda).filter(Tienda.id == id).first()
    if not tienda:
        raise HTTPException(status_code=404, detail="Tienda no encontrada")
    clientes = db.query(Cliente).filter(Cliente.tienda_id == id).count()
    if clientes > 0:
        raise HTTPException(status_code=400, detail=f"No se puede eliminar: tiene {clientes} cliente(s) asignados")
    
    datos_antes = {"nombre": tienda.nombre, "codigo": tienda.codigo}
    db.delete(tienda); db.commit()
    logger.info(f"🗑️ Tienda eliminada: {tienda.nombre}")
    
    registrar_auditoria(
        db=db,
        usuario_id=current_user.id,
        usuario_nombre=current_user.nombre,
        usuario_rol=current_user.rol,
        accion="ELIMINAR_TIENDA",
        tabla="tiendas",
        registro_id=id,
        datos_antes=datos_antes,
        detalles=f"Tienda {tienda.nombre} eliminada por {current_user.nombre}"
    )
    
    return {"success": True, "mensaje": f"Tienda {tienda.nombre} eliminada"}

# ============================================================
# LISTAR USUARIOS
# ============================================================
@router.get("/usuarios")
def listar_usuarios(skip: int = Query(0, ge=0), limit: int = Query(50, ge=1, le=100), db: Session = Depends(get_db), current_user = Depends(get_current_admin)):
    try:
        query = db.query(Usuario)
        if current_user.rol != "admin_central":
            query = query.filter((Usuario.tienda_id == current_user.tienda_id) | (Usuario.id == current_user.id))
        total = query.count()
        usuarios = query.order_by(Usuario.id).offset(skip).limit(limit).all()
        return {"total": total, "skip": skip, "limit": limit, "usuarios": [{"id": u.id, "username": u.username, "nombre": u.nombre, "email": u.email, "rol": u.rol, "activo": u.activo, "tienda_id": u.tienda_id, "tienda_nombre": u.tienda.nombre if u.tienda else None, "ultimo_acceso": u.ultimo_acceso.isoformat() if u.ultimo_acceso else None, "creado_en": u.creado_en.isoformat() if u.creado_en else None} for u in usuarios]}
    except Exception as e:
        logger.error(f"❌ Error listando usuarios: {e}")
        raise HTTPException(status_code=500, detail="Error interno del servidor")

# ============================================================
# CREAR USUARIO (SOLO admin_central)
# ============================================================
@router.post("/usuarios")
@audit(accion="CREAR_USUARIO", tabla="usuarios")
def crear_usuario(usuario_data: UsuarioCreate, db: Session = Depends(get_db), current_user = Depends(get_current_admin)):
    if current_user.rol != "admin_central":
        raise HTTPException(status_code=403, detail="Solo el administrador central puede crear usuarios")
    try:
        existe = db.query(Usuario).filter(Usuario.username == usuario_data.username).first()
        if existe: raise HTTPException(status_code=409, detail="El usuario ya existe")
        if len(usuario_data.password) < 8: raise HTTPException(status_code=400, detail="La contraseña debe tener al menos 8 caracteres")
        tienda_id = usuario_data.tienda_id if usuario_data.rol != "admin_central" else None
        if tienda_id:
            tienda = db.query(Tienda).filter(Tienda.id == tienda_id).first()
            if not tienda: raise HTTPException(status_code=404, detail="Tienda no encontrada")
        nuevo = Usuario(username=usuario_data.username, password=hash_password(usuario_data.password), nombre=usuario_data.nombre, email=usuario_data.email, rol=usuario_data.rol, activo=usuario_data.activo, tienda_id=tienda_id, creado_por=current_user.username)
        db.add(nuevo); db.commit(); db.refresh(nuevo)
        logger.info(f"✅ Usuario creado: {nuevo.username} (rol: {nuevo.rol}, tienda: {tienda_id})")
        
        registrar_auditoria(
            db=db,
            usuario_id=current_user.id,
            usuario_nombre=current_user.nombre,
            usuario_rol=current_user.rol,
            accion="CREAR_USUARIO",
            tabla="usuarios",
            registro_id=nuevo.id,
            detalles=f"Usuario {nuevo.username} ({nuevo.rol}) creado por {current_user.nombre}"
        )
        
        return {"id": nuevo.id, "username": nuevo.username, "nombre": nuevo.nombre, "email": nuevo.email, "rol": nuevo.rol, "activo": nuevo.activo, "tienda_id": nuevo.tienda_id}
    except HTTPException: raise
    except Exception as e: logger.error(f"❌ Error creando usuario: {e}"); db.rollback(); raise HTTPException(status_code=500, detail="Error interno del servidor")

# ============================================================
# ACTUALIZAR USUARIO (SOLO admin_central)
# ============================================================
@router.put("/usuarios/{id}")
@audit(accion="ACTUALIZAR_USUARIO", tabla="usuarios")
def actualizar_usuario(id: int, usuario_data: UsuarioUpdate, db: Session = Depends(get_db), current_user = Depends(get_current_admin)):
    if current_user.rol != "admin_central": raise HTTPException(status_code=403, detail="Solo el administrador central puede modificar usuarios")
    try:
        usuario = db.query(Usuario).filter(Usuario.id == id).first()
        if not usuario: raise HTTPException(status_code=404, detail="Usuario no encontrado")
        
        datos_antes = {"username": usuario.username, "rol": usuario.rol, "activo": usuario.activo, "tienda_id": usuario.tienda_id}
        
        if usuario_data.password:
            if len(usuario_data.password) < 8: raise HTTPException(status_code=400, detail="La contraseña debe tener al menos 8 caracteres")
            usuario.password = hash_password(usuario_data.password)
        if usuario_data.nombre is not None: usuario.nombre = usuario_data.nombre
        if usuario_data.email is not None: usuario.email = usuario_data.email
        if usuario_data.rol is not None: usuario.rol = usuario_data.rol
        if usuario_data.activo is not None: usuario.activo = usuario_data.activo
        if usuario_data.tienda_id is not None: usuario.tienda_id = usuario_data.tienda_id if usuario_data.rol != "admin_central" else None
        db.commit(); db.refresh(usuario)
        
        registrar_auditoria(
            db=db,
            usuario_id=current_user.id,
            usuario_nombre=current_user.nombre,
            usuario_rol=current_user.rol,
            accion="ACTUALIZAR_USUARIO",
            tabla="usuarios",
            registro_id=id,
            datos_antes=datos_antes,
            detalles=f"Usuario {usuario.username} actualizado por {current_user.nombre}"
        )
        
        return {"success": True, "mensaje": "Usuario actualizado"}
    except HTTPException: raise
    except Exception as e: logger.error(f"❌ Error actualizando usuario: {e}"); db.rollback(); raise HTTPException(status_code=500, detail="Error interno del servidor")

# ============================================================
# ELIMINAR USUARIO (SOLO admin_central)
# ============================================================
@router.delete("/usuarios/{id}")
@audit(accion="ELIMINAR_USUARIO", tabla="usuarios")
def eliminar_usuario(id: int, db: Session = Depends(get_db), current_user = Depends(get_current_admin)):
    if current_user.rol != "admin_central": raise HTTPException(status_code=403, detail="Solo el administrador central puede eliminar usuarios")
    try:
        usuario = db.query(Usuario).filter(Usuario.id == id).first()
        if not usuario: raise HTTPException(status_code=404, detail="Usuario no encontrado")
        if usuario.id == current_user.id: raise HTTPException(status_code=403, detail="No puedes eliminar tu propio usuario")
        
        datos_antes = {"username": usuario.username, "rol": usuario.rol}
        db.delete(usuario); db.commit()
        
        registrar_auditoria(
            db=db,
            usuario_id=current_user.id,
            usuario_nombre=current_user.nombre,
            usuario_rol=current_user.rol,
            accion="ELIMINAR_USUARIO",
            tabla="usuarios",
            registro_id=id,
            datos_antes=datos_antes,
            detalles=f"Usuario {usuario.username} eliminado por {current_user.nombre}"
        )
        
        return {"mensaje": f"Usuario {usuario.username} eliminado"}
    except HTTPException: raise
    except Exception as e: logger.error(f"❌ Error eliminando usuario: {e}"); db.rollback(); raise HTTPException(status_code=500, detail="Error interno del servidor") 

# ============================================================
# CLIENTES PENDIENTES
# ============================================================
@router.get("/clientes/pendientes")
def clientes_pendientes(db: Session = Depends(get_db), current_user = Depends(get_current_admin)):
    try:
        query = db.query(Cliente).filter(Cliente.estado == "pendiente")
        if current_user.rol != "admin_central" and current_user.tienda_id: query = query.filter(Cliente.tienda_id == current_user.tienda_id)
        clientes = query.order_by(Cliente.creado_en.desc()).all()
        return {"total": len(clientes), "clientes": [{"id": c.id, "nombre": c.nombre, "cedula": c.cedula, "telefono": c.telefono, "email": c.email, "url_cedula": c.url_cedula, "tienda_nombre": c.tienda.nombre if c.tienda else None, "creado_en": c.creado_en.isoformat() if c.creado_en else None} for c in clientes]}
    except Exception as e: logger.error(f"❌ Error listando pendientes: {e}"); raise HTTPException(status_code=500, detail="Error interno del servidor")

# ============================================================
# FINANCIAMIENTOS PENDIENTES
# ============================================================
@router.get("/financiamientos/pendientes")
def financiamientos_pendientes(db: Session = Depends(get_db), current_user = Depends(get_current_admin)):
    try:
        query = db.query(Financiamiento).filter(Financiamiento.requiere_aprobacion == True, Financiamiento.estado == "activo")
        if current_user.rol != "admin_central" and current_user.tienda_id: query = query.filter(Financiamiento.tienda_id == current_user.tienda_id)
        fins = query.order_by(Financiamiento.creado_en.desc()).all()
        resultado = []
        for fin in fins:
            cliente = db.query(Cliente).filter(Cliente.id == fin.cliente_id).first()
            resultado.append({"id": fin.id, "codigo": fin.codigo, "cliente_nombre": cliente.nombre if cliente else "Desconocido", "cliente_cedula": cliente.cedula if cliente else "", "monto_total_bs": round(fin.monto_total_bs, 2), "monto_total_usd": round(fin.monto_total_usd, 2), "cuotas_solicitadas": fin.cuotas_solicitadas, "tienda_nombre": fin.tienda.nombre if fin.tienda else None, "creado_en": fin.creado_en.isoformat() if fin.creado_en else None})
        return {"total": len(resultado), "financiamientos": resultado}
    except Exception as e: logger.error(f"❌ Error: {e}"); raise HTTPException(status_code=500, detail="Error interno del servidor")

# ============================================================
# BACKUPS
# ============================================================

# ============================================================
# BACKUPS
# ============================================================

@router.post("/backup/crear")
def crear_backup_manual(
    db: Session = Depends(get_db),
    current_user = Depends(get_current_admin)
):
    """Crear backup manual (solo admin_central)"""
    if current_user.rol != "admin_central":
        raise HTTPException(status_code=403, detail="Solo admin_central")
    
    resultado = crear_backup()
    if resultado:
        return {"success": True, "mensaje": "Backup creado correctamente"}
    else:
        raise HTTPException(status_code=500, detail="Error creando backup")

@router.get("/backup/listar")
def listar_backups_disponibles(
    db: Session = Depends(get_db),
    current_user = Depends(get_current_admin)
):
    """Listar backups disponibles (solo admin_central)"""
    if current_user.rol != "admin_central":
        raise HTTPException(status_code=403, detail="Solo admin_central")
    
    return {"backups": listar_backups()}

# ============================================================
# RESTAURAR BACKUP (VERSIÓN MEJORADA)
# ============================================================
@router.post("/backup/restaurar")
def restaurar_backup_manual(
    archivo: str,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_admin)
):
    """
    Restaurar backup (solo admin_central)
    Versión mejorada con manejo de errores y timeout
    """
    if current_user.rol != "admin_central":
        raise HTTPException(status_code=403, detail="Solo admin_central")
    
    try:
        backup_dir = os.getenv("BACKUP_DIR", "./backups")
        backup_path = os.path.join(backup_dir, archivo)
        
        # Verificar que el archivo existe
        if not os.path.exists(backup_path):
            raise HTTPException(status_code=404, detail="Archivo no encontrado")
        
        # Verificar que es un ZIP
        if not archivo.endswith('.zip'):
            raise HTTPException(status_code=400, detail="Solo se permiten archivos ZIP")
        
        logger.info(f"🔄 Iniciando restauración manual: {archivo}")
        
        # Ejecutar restauración con timeout
        resultado = restaurar_backup(backup_path)
        
        if resultado:
            # Limpiar conexiones inactivas después de restaurar
            try:
                from sqlalchemy import text
                db.execute(text("""
                    SELECT pg_terminate_backend(pid) 
                    FROM pg_stat_activity 
                    WHERE datname = current_database() 
                    AND pid <> pg_backend_pid() 
                    AND state = 'idle'
                """))
                db.commit()
                logger.info("🧹 Conexiones inactivas limpiadas después de restauración")
            except Exception as e:
                logger.warning(f"⚠️ No se pudieron limpiar conexiones: {e}")
            
            return {"success": True, "mensaje": f"Backup {archivo} restaurado correctamente"}
        else:
            raise HTTPException(status_code=500, detail="Error restaurando backup")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error en restauración manual: {e}")
        raise HTTPException(status_code=500, detail="Error interno del servidor")

# ============================================================
# LIMPIAR CONEXIONES (NUEVO ENDPOINT)
# ============================================================
@router.post("/backup/limpiar-conexiones")
def limpiar_conexiones(
    db: Session = Depends(get_db),
    current_user = Depends(get_current_admin)
):
    """
    Limpiar conexiones inactivas (solo admin_central)
    """
    if current_user.rol != "admin_central":
        raise HTTPException(status_code=403, detail="Solo admin_central")
    
    try:
        from sqlalchemy import text
        
        # Cerrar conexiones inactivas
        result = db.execute(text("""
            SELECT pg_terminate_backend(pid) 
            FROM pg_stat_activity 
            WHERE datname = current_database() 
            AND pid <> pg_backend_pid() 
            AND state = 'idle'
        """))
        db.commit()
        
        # Cerrar conexiones activas que lleven más de 5 minutos
        result2 = db.execute(text("""
            SELECT pg_terminate_backend(pid) 
            FROM pg_stat_activity 
            WHERE datname = current_database() 
            AND pid <> pg_backend_pid() 
            AND state = 'active'
            AND now() - query_start > interval '5 minutes'
        """))
        db.commit()
        
        logger.info(f"🧹 Conexiones limpiadas: idle={result.rowcount}, long_running={result2.rowcount}")
        
        return {
            "success": True, 
            "mensaje": "Conexiones inactivas limpiadas",
            "idle_terminadas": result.rowcount,
            "long_running_terminadas": result2.rowcount
        }
        
    except Exception as e:
        logger.error(f"❌ Error limpiando conexiones: {e}")
        raise HTTPException(status_code=500, detail="Error interno del servidor")

# ============================================================
# DESCARGAR BACKUP
# ============================================================
@router.get("/backup/descargar")
def descargar_backup(
    archivo: str,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_admin)
):
    """Descargar backup (solo admin_central)"""
    if current_user.rol != "admin_central":
        raise HTTPException(status_code=403, detail="Solo admin_central")
    
    import os
    from fastapi.responses import FileResponse
    
    # Ruta segura al directorio de backups
    backup_dir = os.getenv("BACKUP_DIR", "./backups")
    
    # Validar que el archivo no tenga path traversal (../)
    if ".." in archivo or "/" in archivo or "\\" in archivo:
        raise HTTPException(status_code=400, detail="Nombre de archivo inválido")
    
    backup_path = os.path.join(backup_dir, archivo)
    
    # Verificar que el archivo existe
    if not os.path.exists(backup_path):
        raise HTTPException(status_code=404, detail="Archivo no encontrado")
    
    # Verificar que el archivo es un ZIP
    if not archivo.endswith('.zip'):
        raise HTTPException(status_code=400, detail="Solo se permiten archivos ZIP")
    
    # Verificar tamaño
    file_size = os.path.getsize(backup_path)
    if file_size == 0:
        raise HTTPException(status_code=400, detail="El archivo está vacío")
    
    logger.info(f"📤 Descargando backup: {archivo} ({file_size} bytes)")
    
    return FileResponse(
        backup_path,
        media_type="application/zip",
        filename=archivo,
        headers={
            "Content-Disposition": f"attachment; filename={archivo}",
            "Content-Length": str(file_size)
        }
    )