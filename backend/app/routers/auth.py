"""
🔒 FinanCoop - Router de Autenticación Ultra-Seguro
Login Admin (Frontend Vue) + Login Cliente (App Móvil)
"""

from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel, Field, validator
from sqlalchemy.orm import Session
from datetime import datetime, timezone
import logging
import re

from app.database import get_db
from app.models import Usuario, Cliente
from app.auth import (
    create_access_token, create_refresh_token,
    get_current_cliente, get_current_admin, get_current_user,
    hash_password, hash_pin, verify_password, verify_pin,
    _check_rate_limit, _record_failed_attempt, _record_successful_attempt,
    _hash_token, blacklist_token, ACCESS_TOKEN_EXPIRE_MINUTES
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/auth", tags=["Autenticación"])

# ============================================================
# 📋 MODELOS Pydantic
# ============================================================

class LoginClienteRequest(BaseModel):
    """Login para app móvil - Cédula + PIN"""
    cedula: str = Field(..., min_length=6, max_length=20, pattern=r"^[0-9Vv-]+$")
    pin: str = Field(..., min_length=4, max_length=6, pattern=r"^[0-9]+$")
    
    @validator('cedula')
    def validate_cedula(cls, v):
        v = v.strip().upper()
        if not re.match(r"^[0-9Vv-]+$", v):
            raise ValueError("Cédula contiene caracteres inválidos")
        return v
    
    @validator('pin')
    def validate_pin(cls, v):
        if len(v) < 4:
            raise ValueError("PIN debe tener al menos 4 dígitos")
        return v.strip()

class RefreshTokenRequest(BaseModel):
    refresh_token: str = Field(..., min_length=20)

class PasswordChangeRequest(BaseModel):
    old_password: str = Field(..., min_length=8, max_length=128)
    new_password: str = Field(..., min_length=12, max_length=128)
    
    @validator('new_password')
    def validate_password_strength(cls, v):
        if not re.search(r"[A-Z]", v):
            raise ValueError("Debe contener al menos una mayúscula")
        if not re.search(r"[a-z]", v):
            raise ValueError("Debe contener al menos una minúscula")
        if not re.search(r"[0-9]", v):
            raise ValueError("Debe contener al menos un número")
        if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", v):
            raise ValueError("Debe contener al menos un carácter especial")
        return v

class RegistroAdminRequest(BaseModel):
    username: str = Field(..., min_length=3, max_length=50, pattern=r"^[a-zA-Z0-9_]+$")
    password: str = Field(..., min_length=12, max_length=128)
    rol: str = Field(default="usuario", pattern=r"^(admin|cajero|usuario)$")
    nombre: str = Field(..., min_length=2, max_length=100)
    email: str = Field(default="", max_length=200)

# ============================================================
# 🔐 LOGIN ADMIN (Frontend Vue - Panel Web)
# ============================================================

@router.post("/login")
def login_admin(
    request: Request,
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    """
    Login para administradores del panel web.
    Usado por el frontend Vue con OAuth2PasswordRequestForm.
    Protegido contra brute force y timing attacks.
    """
    username = form_data.username.lower().strip()
    password = form_data.password
    
    # Obtener IP real (considerando proxy)
    client_ip = request.headers.get("x-forwarded-for", request.client.host if request.client else "unknown")
    rate_key = f"admin:{username}:{client_ip}"
    
    # 🚫 Rate limiting
    if not _check_rate_limit(rate_key):
        raise HTTPException(
            status_code=429,
            detail="Demasiados intentos fallidos. Intente más tarde."
        )
    
    logger.info(f"🔑 [Admin Login] Intento: {username} desde {client_ip}")
    
    usuario = db.query(Usuario).filter(Usuario.username == username).first()
    
    # ⚠️ Timing-safe: verificar contra hash dummy si usuario no existe
    if not usuario:
        verify_password(password, "$2b$12$dummyhashfordummyuser1234567890123456789012345")
        _record_failed_attempt(rate_key)
        logger.warning(f"❌ [Admin Login] Usuario no encontrado: {username}")
        raise HTTPException(status_code=401, detail="Credenciales incorrectas")
    
    if not verify_password(password, usuario.password):
        _record_failed_attempt(rate_key)
        logger.warning(f"❌ [Admin Login] Contraseña incorrecta: {username}")
        raise HTTPException(status_code=401, detail="Credenciales incorrectas")
    
    if not usuario.activo:
        _record_failed_attempt(rate_key)
        logger.warning(f"❌ [Admin Login] Usuario inactivo: {username}")
        raise HTTPException(status_code=403, detail="Usuario inactivo. Contacte al administrador.")
    
    # ✅ Login exitoso
    _record_successful_attempt(rate_key)
    
    # Actualizar último acceso
    usuario.ultimo_acceso = datetime.now(timezone.utc)
    db.commit()
    
    # Crear tokens
    access_token = create_access_token(
        data={"sub": usuario.username, "rol": usuario.rol}
    )
    refresh_token = create_refresh_token(usuario.username, usuario.rol)
    
    logger.info(f"✅ [Admin Login] Exitoso: {usuario.username} (rol: {usuario.rol})")
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "expires_in": ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        "refresh_token": refresh_token,
        "rol": usuario.rol,
        "username": usuario.username,
        "nombre": usuario.nombre
    }

# ============================================================
# 🔐 LOGIN CLIENTE (App Móvil)
# ============================================================

@router.post("/login-cliente")
def login_cliente(
    request_data: LoginClienteRequest,
    request: Request,
    db: Session = Depends(get_db)
):
    """
    Login para clientes de la app móvil.
    Usa cédula + PIN con verificación bcrypt.
    Protegido contra brute force y timing attacks.
    """
    cedula = request_data.cedula
    pin = request_data.pin
    
    # IP para rate limiting
    client_ip = request.headers.get("x-forwarded-for", request.client.host if request.client else "unknown")
    rate_key = f"cliente:{cedula}:{client_ip}"
    
    # 🚫 Rate limiting
    if not _check_rate_limit(rate_key):
        raise HTTPException(
            status_code=429,
            detail="Demasiados intentos fallidos. Intente más tarde."
        )
    
    logger.info(f"🔑 [Cliente Login] Intento: cédula {cedula[:4]}**** desde {client_ip}")
    
    cliente = db.query(Cliente).filter(Cliente.cedula == cedula).first()
    
    # ⚠️ Timing-safe: siempre verificar PIN incluso si cliente no existe
    if not cliente:
        verify_pin(pin, "$2b$12$dummyhashfordummypin123456789012345678901234567")
        _record_failed_attempt(rate_key)
        logger.warning(f"❌ [Cliente Login] Cliente no encontrado: {cedula[:4]}****")
        raise HTTPException(status_code=401, detail="Credenciales incorrectas")
    
    if cliente.estado != "aprobado":
        _record_failed_attempt(rate_key)
        logger.warning(f"❌ [Cliente Login] Cliente no aprobado: {cedula[:4]}****")
        raise HTTPException(status_code=403, detail="Tu cuenta está pendiente de aprobación")
    
    # Verificar PIN con bcrypt
    if not cliente.pin_hash:
        # Migración: si no tiene pin_hash, verificar contra el PIN antiguo
        from app.utils import generar_pin
        if cliente.pin == pin:
            # Migrar a hash
            cliente.pin_hash = hash_pin(pin)
            cliente.pin = None  # Limpiar PIN texto plano
            db.commit()
        else:
            _record_failed_attempt(rate_key)
            raise HTTPException(status_code=401, detail="Credenciales incorrectas")
    else:
        if not verify_pin(pin, cliente.pin_hash):
            _record_failed_attempt(rate_key)
            logger.warning(f"❌ [Cliente Login] PIN incorrecto: {cedula[:4]}****")
            raise HTTPException(status_code=401, detail="Credenciales incorrectas")
    
    # ✅ Login exitoso
    _record_successful_attempt(rate_key)
    
    # Actualizar último acceso
    cliente.ultimo_acceso = datetime.now(timezone.utc)
    db.commit()
    
    # Crear tokens
    access_token = create_access_token(
        data={"sub": str(cliente.id), "rol": "cliente"}
    )
    refresh_token = create_refresh_token(str(cliente.id), "cliente")
    
    logger.info(f"✅ [Cliente Login] Exitoso: {cliente.nombre} (ID: {cliente.id})")
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "expires_in": ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        "refresh_token": refresh_token,
        "cliente": {
            "id": cliente.id,
            "nombre": cliente.nombre,
            "cedula": cliente.cedula[:4] + "****",
            "nivel": cliente.nivel,
            "score": cliente.score,
            "telefono": cliente.telefono
        }
    }

# ============================================================
# 🔄 REFRESH TOKEN
# ============================================================

@router.post("/refresh")
def refresh_token(
    request_data: RefreshTokenRequest,
    db: Session = Depends(get_db)
):
    """
    Obtiene nuevo access token usando refresh token válido.
    Implementa refresh token rotation.
    """
    from app.auth import _decode_and_validate_token
    
    try:
        payload = _decode_and_validate_token(request_data.refresh_token, db)
    except HTTPException:
        raise HTTPException(status_code=401, detail="Refresh token inválido o revocado")
    
    if payload.get("type") != "refresh":
        raise HTTPException(status_code=401, detail="Token no es de tipo refresh")
    
    sub = payload.get("sub")
    rol = payload.get("rol")
    
    # Blacklistear el refresh token actual (rotación)
    blacklist_token(payload["jti"], datetime.fromtimestamp(payload["exp"], tz=timezone.utc), db)
    
    # Crear nuevos tokens
    new_access = create_access_token(data={"sub": sub, "rol": rol})
    new_refresh = create_refresh_token(sub, rol)
    
    logger.info(f"🔄 [Refresh] Tokens rotados para {sub}")
    
    return {
        "access_token": new_access,
        "token_type": "bearer",
        "expires_in": ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        "refresh_token": new_refresh
    }

# ============================================================
# 🔍 VERIFICAR TOKEN (Admin)
# ============================================================

@router.get("/verificar")
def verificar_token(current_user: Usuario = Depends(get_current_admin)):
    """Verifica que el token del admin sea válido."""
    return {
        "valid": True,
        "username": current_user.username,
        "rol": current_user.rol,
        "nombre": current_user.nombre
    }

# ============================================================
# 📝 REGISTRO DE ADMIN (Solo admins existentes)
# ============================================================

@router.post("/registro")
def registrar_admin(
    request_data: RegistroAdminRequest,
    current_admin: Usuario = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Registro de nuevos administradores/usuarios del panel."""
    logger.info(f"📝 [Registro Admin] {request_data.username} por {current_admin.username}")
    
    existe = db.query(Usuario).filter(Usuario.username == request_data.username.lower()).first()
    if existe:
        raise HTTPException(status_code=409, detail="El usuario ya existe")
    
    nuevo = Usuario(
        username=request_data.username.lower(),
        password=hash_password(request_data.password),
        rol=request_data.rol,
        nombre=request_data.nombre,
        email=request_data.email,
        activo=True,
        creado_por=current_admin.username
    )
    db.add(nuevo)
    db.commit()
    db.refresh(nuevo)
    
    logger.info(f"✅ [Registro Admin] Usuario creado: {request_data.username} (rol: {request_data.rol})")
    
    return {
        "mensaje": "Usuario creado exitosamente",
        "username": nuevo.username,
        "rol": nuevo.rol,
        "nombre": nuevo.nombre
    }

# ============================================================
# 🔒 CAMBIAR CONTRASEÑA
# ============================================================

@router.post("/cambiar-password")
def cambiar_password(
    request_data: PasswordChangeRequest,
    current_user: Usuario = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Cambio de contraseña con verificación de la anterior."""
    if not verify_password(request_data.old_password, current_user.password):
        raise HTTPException(status_code=400, detail="Contraseña actual incorrecta")
    
    if request_data.old_password == request_data.new_password:
        raise HTTPException(status_code=400, detail="La nueva contraseña debe ser diferente")
    
    current_user.password = hash_password(request_data.new_password)
    db.commit()
    
    logger.info(f"🔑 [Password] Contraseña cambiada para: {current_user.username}")
    
    return {"mensaje": "Contraseña actualizada exitosamente"}

# ============================================================
# 🚪 LOGOUT (Blacklist de token)
# ============================================================

@router.post("/logout")
def logout(
    request: Request,
    current_user: Usuario = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Logout: agrega el token actual a blacklist.
    El token no podrá ser usado nuevamente.
    """
    auth_header = request.headers.get("Authorization", "")
    token = auth_header.replace("Bearer ", "")
    
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM], 
                            audience="financoop-api", issuer="financoop-backend")
        jti = payload.get("jti")
        exp = datetime.fromtimestamp(payload["exp"], tz=timezone.utc)
        
        blacklist_token(jti, exp, db)
        
        logger.info(f"🚪 [Logout] Token revocado para: {current_user.username if hasattr(current_user, 'username') else current_user.id}")
        return {"mensaje": "Sesión cerrada exitosamente"}
    except Exception:
        return {"mensaje": "Sesión cerrada"}

# Necesitamos jwt aquí para el logout
from jose import jwt as jwt_decode
import jwt as pyjwt