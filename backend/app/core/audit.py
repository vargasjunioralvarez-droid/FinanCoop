"""
Sistema de Auditoría con hash encadenado (H14)
"""

import logging
import hashlib
import json
import asyncio
from functools import wraps
from sqlalchemy.orm import Session
from app.modules.audit.models import Auditoria

logger = logging.getLogger(__name__)


def _calcular_hash(datos: dict) -> str:
    """Calcula SHA-256 de un diccionario, ordenando las claves para consistencia."""
    cadena = json.dumps(datos, sort_keys=True, default=str)
    return hashlib.sha256(cadena.encode()).hexdigest()


def _obtener_ultimo_hash(db: Session) -> str:
    """Obtiene el hash_actual del último registro de auditoría."""
    ultimo = db.query(Auditoria).order_by(Auditoria.id.desc()).first()
    return ultimo.hash_actual if ultimo else None


def _obtener_request(args, kwargs):
    """Obtener el objeto Request de forma segura desde args o kwargs."""
    for key in ['request', '_request', 'req']:
        if key in kwargs:
            request = kwargs[key]
            if hasattr(request, 'headers') and hasattr(request, 'client'):
                return request
    
    for arg in args:
        if hasattr(arg, 'headers') and hasattr(arg, 'client'):
            return arg
    
    return None


def _obtener_db(args, kwargs):
    """Obtener la sesión de base de datos de forma segura."""
    for key in ['db', 'database', 'session']:
        if key in kwargs:
            db = kwargs[key]
            if hasattr(db, 'query'):
                return db
    
    for arg in args:
        if hasattr(arg, 'query') and hasattr(arg, 'add'):
            return arg
    
    return None


def _obtener_usuario_info(usuario):
    """Obtener información del usuario de forma segura."""
    if not usuario:
        return None, None, None
    
    usuario_id = getattr(usuario, 'id', None)
    usuario_nombre = getattr(usuario, 'nombre', getattr(usuario, 'username', None))
    usuario_rol = getattr(usuario, 'rol', None)
    
    # ✅ Si no tiene rol, es un Cliente (no un Usuario admin)
    if not usuario_rol:
        usuario_id = None  # No guardar en auditoría (FK constraint)
        usuario_rol = 'cliente'
    
    return usuario_id, usuario_nombre, usuario_rol


def registrar_auditoria(
    db: Session,
    usuario_id: int = None,
    usuario_nombre: str = None,
    usuario_rol: str = None,
    accion: str = None,
    tabla: str = None,
    registro_id: int = None,
    datos_antes: dict = None,
    datos_despues: dict = None,
    detalles: str = None,
    ip: str = None,
    user_agent: str = None,
    endpoint: str = None,
    metodo_http: str = None
):
    """Función para registrar auditoría manualmente, con hash encadenado."""
    try:
        hash_anterior = _obtener_ultimo_hash(db)

        auditoria = Auditoria(
            usuario_id=usuario_id,
            usuario_nombre=usuario_nombre,
            usuario_rol=usuario_rol,
            accion=accion,
            tabla=tabla,
            registro_id=registro_id,
            datos_antes=datos_antes,
            datos_despues=datos_despues,
            detalles=detalles,
            ip=ip,
            user_agent=user_agent,
            endpoint=endpoint,
            metodo_http=metodo_http,
            hash_anterior=hash_anterior
        )

        db.add(auditoria)
        db.flush()

        datos_registro = {
            "id": auditoria.id,
            "usuario_id": usuario_id,
            "usuario_nombre": usuario_nombre,
            "usuario_rol": usuario_rol,
            "accion": accion,
            "tabla": tabla,
            "registro_id": registro_id,
            "datos_antes": datos_antes,
            "datos_despues": datos_despues,
            "detalles": detalles,
            "ip": ip,
            "endpoint": endpoint,
            "metodo_http": metodo_http,
            "hash_anterior": hash_anterior,
            "fecha": auditoria.fecha.isoformat() if auditoria.fecha else None
        }
        auditoria.hash_actual = _calcular_hash(datos_registro)

        db.commit()
        logger.info(f"📋 Auditoría: {accion} - {tabla} #{registro_id} (hash: {auditoria.hash_actual[:8]}...)")

    except Exception as e:
        logger.error(f"❌ Error registrando auditoría: {e}")
        db.rollback()


def audit(accion: str, tabla: str = None):
    """Decorador para auditar endpoints síncronos y asíncronos."""
    def decorator(func):
        is_async = asyncio.iscoroutinefunction(func)

        if is_async:
            @wraps(func)
            async def async_wrapper(*args, **kwargs):
                request = _obtener_request(args, kwargs)
                db = _obtener_db(args, kwargs)

                usuario = None
                if 'current_user' in kwargs:
                    usuario = kwargs.get('current_user')
                elif 'current_admin' in kwargs:
                    usuario = kwargs.get('current_admin')

                # ✅ Usar función segura para obtener info del usuario
                usuario_id, usuario_nombre, usuario_rol = _obtener_usuario_info(usuario)

                registro_id = kwargs.get('id') or kwargs.get('registro_id') or kwargs.get('pago_id') or kwargs.get('nivel')

                try:
                    result = await func(*args, **kwargs)

                    if request and db:
                        ip = request.headers.get("x-forwarded-for",
                                  request.client.host if request.client else "unknown")
                        user_agent = request.headers.get("user-agent", "unknown")

                        registrar_auditoria(
                            db=db,
                            usuario_id=usuario_id,
                            usuario_nombre=usuario_nombre,
                            usuario_rol=usuario_rol,
                            accion=accion,
                            tabla=tabla,
                            registro_id=registro_id,
                            ip=ip,
                            user_agent=user_agent,
                            endpoint=str(request.url.path),
                            metodo_http=request.method
                        )

                    return result

                except Exception as e:
                    if request and db:
                        ip = request.headers.get("x-forwarded-for",
                                  request.client.host if request.client else "unknown")
                        user_agent = request.headers.get("user-agent", "unknown")

                        registrar_auditoria(
                            db=db,
                            usuario_id=usuario_id,
                            usuario_nombre=usuario_nombre,
                            usuario_rol=usuario_rol,
                            accion=f"{accion}_ERROR",
                            tabla=tabla,
                            registro_id=registro_id,
                            detalles=f"Error: {str(e)}",
                            ip=ip,
                            user_agent=user_agent,
                            endpoint=str(request.url.path),
                            metodo_http=request.method
                        )
                    raise

            return async_wrapper
        else:
            @wraps(func)
            def wrapper(*args, **kwargs):
                request = _obtener_request(args, kwargs)
                db = _obtener_db(args, kwargs)

                usuario = None
                if 'current_user' in kwargs:
                    usuario = kwargs.get('current_user')
                elif 'current_admin' in kwargs:
                    usuario = kwargs.get('current_admin')

                # ✅ Usar función segura para obtener info del usuario
                usuario_id, usuario_nombre, usuario_rol = _obtener_usuario_info(usuario)

                registro_id = kwargs.get('id') or kwargs.get('registro_id') or kwargs.get('pago_id') or kwargs.get('nivel')

                try:
                    result = func(*args, **kwargs)

                    if request and db:
                        ip = request.headers.get("x-forwarded-for",
                                  request.client.host if request.client else "unknown")
                        user_agent = request.headers.get("user-agent", "unknown")

                        registrar_auditoria(
                            db=db,
                            usuario_id=usuario_id,
                            usuario_nombre=usuario_nombre,
                            usuario_rol=usuario_rol,
                            accion=accion,
                            tabla=tabla,
                            registro_id=registro_id,
                            ip=ip,
                            user_agent=user_agent,
                            endpoint=str(request.url.path),
                            metodo_http=request.method
                        )

                    return result

                except Exception as e:
                    if request and db:
                        ip = request.headers.get("x-forwarded-for",
                                  request.client.host if request.client else "unknown")
                        user_agent = request.headers.get("user-agent", "unknown")

                        registrar_auditoria(
                            db=db,
                            usuario_id=usuario_id,
                            usuario_nombre=usuario_nombre,
                            usuario_rol=usuario_rol,
                            accion=f"{accion}_ERROR",
                            tabla=tabla,
                            registro_id=registro_id,
                            detalles=f"Error: {str(e)}",
                            ip=ip,
                            user_agent=user_agent,
                            endpoint=str(request.url.path),
                            metodo_http=request.method
                        )
                    raise

            return wrapper

    return decorator


def audit_login(logout: bool = False):
    """Decorador para auditar LOGIN/LOGOUT (síncrono)."""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            request = _obtener_request(args, kwargs)
            db = _obtener_db(args, kwargs)

            try:
                result = func(*args, **kwargs)

                if request and db:
                    try:
                        ip = request.headers.get("x-forwarded-for",
                                  request.client.host if request.client else "unknown")
                        user_agent = request.headers.get("user-agent", "unknown")

                        registrar_auditoria(
                            db=db,
                            usuario_id=None,
                            usuario_nombre='admin',
                            usuario_rol=None,
                            accion="LOGOUT" if logout else "LOGIN",
                            ip=ip,
                            user_agent=user_agent,
                            endpoint=str(request.url.path),
                            metodo_http=request.method
                        )
                    except Exception as e:
                        logger.error(f"Error registrando auditoría de login: {e}")

                return result

            except Exception as e:
                if request and db:
                    try:
                        ip = request.headers.get("x-forwarded-for",
                                  request.client.host if request.client else "unknown")
                        user_agent = request.headers.get("user-agent", "unknown")

                        registrar_auditoria(
                            db=db,
                            usuario_id=None,
                            usuario_nombre='desconocido',
                            usuario_rol=None,
                            accion="LOGIN_FAILED",
                            detalles=f"Intento fallido: {str(e)}",
                            ip=ip,
                            user_agent=user_agent,
                            endpoint=str(request.url.path),
                            metodo_http=request.method
                        )
                    except Exception as audit_error:
                        logger.error(f"Error registrando login fallido: {audit_error}")

                raise

        return wrapper
    return decorator