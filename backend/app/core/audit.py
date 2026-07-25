"""
Sistema de Auditoría
"""

import logging
from functools import wraps
from sqlalchemy.orm import Session
from app.modules.audit.models import Auditoria

logger = logging.getLogger(__name__)

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
    """Función para registrar auditoría manualmente"""
    try:
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
            metodo_http=metodo_http
        )
        db.add(auditoria)
        db.commit()
        logger.info(f"📋 Auditoría: {accion} - {tabla} #{registro_id}")
    except Exception as e:
        logger.error(f"❌ Error registrando auditoría: {e}")
        db.rollback()


def audit(accion: str, tabla: str = None):
    """Decorador para auditar endpoints síncronos"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            request = kwargs.get('request')
            db = kwargs.get('db')
            
            # Obtener usuario
            usuario = None
            usuario_id = None
            usuario_nombre = None
            usuario_rol = None
            
            if 'current_user' in kwargs:
                usuario = kwargs.get('current_user')
            elif 'current_admin' in kwargs:
                usuario = kwargs.get('current_admin')
            
            if usuario:
                usuario_id = getattr(usuario, 'id', None)
                usuario_nombre = getattr(usuario, 'nombre', getattr(usuario, 'username', None))
                usuario_rol = getattr(usuario, 'rol', None)
            
            # ID del registro
            registro_id = kwargs.get('id') or kwargs.get('registro_id') or kwargs.get('pago_id')
            
            # Ejecutar función
            try:
                result = func(*args, **kwargs)
                
                # Registrar auditoría después del éxito
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
                # Registrar error en auditoría
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
    """Decorador para auditar LOGIN/LOGOUT (síncrono)"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            request = kwargs.get('request')
            db = kwargs.get('db')
            
            try:
                # Ejecutar la función (síncrona, sin await)
                result = func(*args, **kwargs)
                
                # Registrar auditoría si hay request y db
                if request and db:
                    try:
                        ip = request.headers.get("x-forwarded-for", 
                                  request.client.host if request.client else "unknown")
                        user_agent = request.headers.get("user-agent", "unknown")
                        
                        # Obtener usuario
                        usuario = kwargs.get('current_user')
                        if not usuario and isinstance(result, dict):
                            # Ver si el resultado contiene el usuario
                            pass
                        
                        # Para login, obtenemos el usuario de la consulta a la BD
                        # o podemos buscarlo después del login exitoso
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
                # Registrar intento fallido
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