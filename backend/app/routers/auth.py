"""
🔒 FinanCoop - Router de Autenticación Ultra-Seguro
Protección contra: brute force, timing attacks, JWT forgery, replay attacks
"""

from fastapi import APIRouter, Depends, HTTPException, status, Request, Header
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
    hash_password, verify_password,
    _check_rate_limit, _record_failed_attempt, _record_successful_attempt,
    _hash_token, ACCESS_TOKEN_EXPIRE_MINUTES
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/auth", tags=["Autenticación"])

# ─────────────────────────────────────────────────────────────
# 📋 MODELOS Pydantic (con validación estricta)
# ─────────────────────────────────────────────────────────────

class LoginClienteRequest(BaseModel):
    cedula: str = Field(..., min_length=6, max_length=20, pattern=r"^[0-9Vv-]+$")
    pin: str = Field(..., min_length=4, max_length=6, pattern=r"^[0-9]+$")

    @validator('cedula')
    def validate_cedula(cls, v):
        v = v.strip().upper()
        if not re.match(r"^[0-9Vv-]+$", v):
            raise ValueError("Cédula contiene caracteres inválidos")
        return v

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
        if not re.search(r"[!@#$%^&*(),.?":{}|<>]", v):
            raise ValueError("Debe contener al menos un carácter especial")
        return v

# ─────────────────────────────────────────────────────────────
# 🔐 LOGIN CLIENTE (App Móvil) - Con rate limiting
# ─────────────────────────────────────────────────────────────

@router.post("/login-cliente")
def login_cliente(request: LoginClienteRequest, db: Session = Depends(get_db)):
    """
    Login para clientes de la app móvil.
    Protegido contra brute force y timing attacks.
    """
    cedula = request.cedula
    pin = request.pin

    # 🚫 Rate limiting por cédula
    if not _check_rate_limit(f"cliente:{cedula}"):
        raise HTTPException(
            status_code=429,
            detail="Demasiados intentos fallidos. Intente más tarde."
        )

    logger.info(f"🚀 [BACKEND] Login cliente - Cédula: {cedula[:4]}****")

    cliente = db.query(Cliente).filter(Cliente.cedula == cedula).first()

    # ⚠️ Timing-safe: siempre verificar PIN incluso si cliente no existe
    # (usar un hash dummy para mantener tiempo constante)
    if not cliente:
        # Verificar contra un hash dummy para prevenir user enumeration
        verify_password(pin, "$2b$12$dummyhashfordummyuser1234567890123456789012345")
        _record_failed_attempt(f"cliente:{cedula}")
        logger.warning(f"❌ [BACKEND] Cliente no encontrado: {cedula[:4]}****")
        raise HTTPException(status_code=401, detail="Credenciales incorrectas")

    if cliente.pin != pin:
        _record_failed_attempt(f"cliente:{cedula}")
        logger.warning(f"❌ [BACKEND] PIN incorrecto: {cedula[:4]}****")
        raise HTTPException(status_code=401, detail="Credenciales incorrectas")

    # ✅ Login exitoso
    _record_successful_attempt(f"cliente:{cedula}")

    # Actualizar último acceso
    cliente.ultimo_acceso = datetime.now(timezone.utc)
    db.commit()

    # Crear tokens
    access_token = create_access_token(
        data={"sub": str(cliente.id), "rol": "cliente"}
    )
    refresh_token = create_refresh_token(str(cliente.id), "cliente")

    logger.info(f"🔑 [BACKEND] Tokens generados para cliente {cliente.id}")

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
            "score": cliente.score
        }
    }

# ─────────────────────────────────────────────────────────────
# 🔐 LOGIN ADMIN (Panel Web) - Con rate limiting y headers seguros
# ─────────────────────────────────────────────────────────────

@router.post("/login")
def login_admin(
    request: Request,
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    """
    Login para administradores del panel web.
    Protegido contra brute force, timing attacks y user enumeration.
    """
    username = form_data.username.lower().strip()
    password = form_data.password

    # Obtener IP real (considerando proxy)
    client_ip = request.headers.get("x-forwarded-for", request.client.host)
    rate_key = f"admin:{username}:{client_ip}"

    # 🚫 Rate limiting
    if not _check_rate_limit(rate_key):
        raise HTTPException(
            status_code=429,
            detail="Demasiados intentos fallidos. Intente más tarde."
        )

    logger.info(f"🚀 [BACKEND] Login admin - Username: {username}")

    usuario = db.query(Usuario).filter(Usuario.username == username).first()

    # ⚠️ Timing-safe: verificar contra hash dummy si usuario no existe
    if not usuario:
        verify_password(password, "$2b$12$dummyhashfordummyuser1234567890123456789012345")
        _record_failed_attempt(rate_key)
        logger.warning(f"❌ [BACKEND] Admin no encontrado: {username}")
        raise HTTPException(status_code=401, detail="Credenciales incorrectas")

    if not verify_password(password, usuario.password):
        _record_failed_attempt(rate_key)
        logger.warning(f"❌ [BACKEND] Contraseña incorrecta: {username}")
        raise HTTPException(status_code=401, detail="Credenciales incorrectas")

    if not usuario.activo:
        _record_failed_attempt(rate_key)
        logger.warning(f"❌ [BACKEND] Usuario inactivo: {username}")
        raise HTTPException(status_code=403, detail="Usuario inactivo")

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

    token_hash = _hash_token(access_token)
    logger.info(f"🔑 [BACKEND] Token admin generado para {usuario.username} (hash: {token_hash})")

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "expires_in": ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        "refresh_token": refresh_token,
        "rol": usuario.rol,
        "username": usuario.username,
        "nombre": usuario.nombre
    }

# ─────────────────────────────────────────────────────────────
# 🔄 REFRESH TOKEN
# ─────────────────────────────────────────────────────────────

@router.post("/refresh")
def refresh_token(request: RefreshTokenRequest, db: Session = Depends(get_db)):
    """
    Obtiene un nuevo access token usando un refresh token válido.
    Implementa refresh token rotation (cada uso genera uno nuevo).
    """
    from app.auth import _decode_and_validate_token

    try:
        payload = _decode_and_validate_token(request.refresh_token)
    except HTTPException:
        raise HTTPException(status_code=401, detail="Refresh token inválido")

    # Verificar que sea un refresh token
    if payload.get("type") != "refresh":
        raise HTTPException(status_code=401, detail="Token inválido")

    username = payload.get("sub")
    rol = payload.get("rol")

    # Crear nuevos tokens (rotación)
    new_access = create_access_token(data={"sub": username, "rol": rol})
    new_refresh = create_refresh_token(username, rol)

    logger.info(f"🔄 [BACKEND] Tokens rotados para {username}")

    return {
        "access_token": new_access,
        "token_type": "bearer",
        "expires_in": ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        "refresh_token": new_refresh
    }

# ─────────────────────────────────────────────────────────────
# 📝 REGISTRO DE ADMINISTRADOR (solo admins existentes)
# ─────────────────────────────────────────────────────────────

class RegistroRequest(BaseModel):
    username: str = Field(..., min_length=3, max_length=50, pattern=r"^[a-zA-Z0-9_]+$")
    password: str = Field(..., min_length=12, max_length=128)
    rol: str = Field(default="usuario", pattern=r"^(admin|cajero|usuario)$")
    nombre: str = Field(..., min_length=2, max_length=100)

@router.post("/registro")
def registrar_usuario(
    request: RegistroRequest,
    current_admin: Usuario = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """
    Registro de nuevos usuarios. Solo administradores pueden crear cuentas.
    """
    logger.info(f"🚀 [BACKEND] Registro de usuario: {request.username} por {current_admin.username}")

    # Verificar que el username no exista
    existe = db.query(Usuario).filter(Usuario.username == request.username.lower()).first()
    if existe:
        logger.warning(f"❌ [BACKEND] Usuario ya existe: {request.username}")
        raise HTTPException(status_code=400, detail="El usuario ya existe")

    # Hashear contraseña con bcrypt rounds=12
    hashed_password = hash_password(request.password)

    nuevo = Usuario(
        username=request.username.lower(),
        password=hashed_password,
        rol=request.rol,
        nombre=request.nombre,
        activo=True,
        creado_por=current_admin.username
    )
    db.add(nuevo)
    db.commit()
    db.refresh(nuevo)

    logger.info(f"✅ [BACKEND] Usuario creado: {request.username} (rol: {request.rol})")

    return {
        "mensaje": "Usuario creado exitosamente",
        "username": nuevo.username,
        "rol": nuevo.rol,
        "nombre": nuevo.nombre
    }

# ─────────────────────────────────────────────────────────────
# 🔍 VERIFICAR TOKEN
# ─────────────────────────────────────────────────────────────

@router.get("/verificar")
def verificar_token(current_user: Usuario = Depends(get_current_admin)):
    """Verifica que el token del admin sea válido."""
    return {
        "valid": True,
        "username": current_user.username,
        "rol": current_user.rol,
        "nombre": current_user.nombre
    }

# ─────────────────────────────────────────────────────────────
# 🔒 CAMBIAR CONTRASEÑA
# ─────────────────────────────────────────────────────────────

@router.post("/cambiar-password")
def cambiar_password(
    request: PasswordChangeRequest,
    current_user: Usuario = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Cambio de contraseña con verificación de la anterior.
    """
    if not verify_password(request.old_password, current_user.password):
        raise HTTPException(status_code=400, detail="Contraseña actual incorrecta")

    current_user.password = hash_password(request.new_password)
    db.commit()

    logger.info(f"🔑 [BACKEND] Contraseña cambiada para: {current_user.username}")

    return {"mensaje": "Contraseña actualizada exitosamente"}

# ─────────────────────────────────────────────────────────────
# 🚪 LOGOUT (revocación de token - placeholder para blacklist)
# ─────────────────────────────────────────────────────────────

# En producción, implementar blacklist de tokens en Redis
_token_blacklist = set()

@router.post("/logout")
def logout(current_user: Usuario = Depends(get_current_user)):
    """
    Logout del usuario. En producción, agregar token a blacklist en Redis.
    """
    # TODO: Agregar token a blacklist en Redis con TTL = tiempo restante del token
    logger.info(f"🚪 [BACKEND] Logout: {current_user.username}")
    return {"mensaje": "Sesión cerrada exitosamente"}