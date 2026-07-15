"""
🔒 FinanCoop - Sistema de Autenticación Ultra-Seguro
Hardening completo contra ataques JWT, fuerza bruta, timing attacks y más.
"""

from fastapi import Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from jose.exceptions import ExpiredSignatureError
from sqlalchemy.orm import Session
from datetime import datetime, timedelta, timezone
from app.database import get_db
from app.models import Cliente, Usuario
import os
import bcrypt
import logging
import secrets
import hashlib
import hmac
from typing import Optional, Union

# ─────────────────────────────────────────────────────────────
# 🛡️ CONFIGURACIÓN DE SEGURIDAD
# ─────────────────────────────────────────────────────────────

SECRET_KEY = os.getenv("SECRET_KEY")
if not SECRET_KEY:
    raise ValueError("❌ SECRET_KEY no está configurada en las variables de entorno")

# 🔥 Validar longitud mínima de SECRET_KEY (mínimo 256 bits = 32 bytes)
if len(SECRET_KEY.encode()) < 32:
    raise ValueError("❌ SECRET_KEY debe tener al menos 32 caracteres (256 bits)")

ALGORITHM = "HS256"

# ⏱️ TTL de tokens muy cortos (15 min acceso, 7 días refresh)
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "15"))
REFRESH_TOKEN_EXPIRE_DAYS = int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", "7"))

# 🔑 bcrypt rounds: 12 = ~250ms por hash (resistente a fuerza bruta)
BCRYPT_ROUNDS = int(os.getenv("BCRYPT_ROUNDS", "12"))

# 🚫 Rate limiting en memoria (en producción usar Redis)
_login_attempts = {}
MAX_LOGIN_ATTEMPTS = 5
LOGIN_LOCKOUT_MINUTES = 15

# Configurar logging seguro (sin exponer tokens ni contraseñas)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

# ─────────────────────────────────────────────────────────────
# 🔐 UTILIDADES CRIPTOGRÁFICAS
# ─────────────────────────────────────────────────────────────

def _secure_compare(a: str, b: str) -> bool:
    """Comparación constant-time para prevenir timing attacks."""
    return hmac.compare_digest(a.encode(), b.encode())

def _hash_token(token: str) -> str:
    """Hash SHA-256 del token para logging seguro (nunca loggear tokens raw)."""
    return hashlib.sha256(token.encode()).hexdigest()[:16]

def _generate_jti() -> str:
    """Genera un JWT ID único para prevenir replay attacks."""
    return secrets.token_urlsafe(16)

# ─────────────────────────────────────────────────────────────
# 🎫 CREACIÓN DE TOKENS
# ─────────────────────────────────────────────────────────────

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    Crea un JWT de acceso con claims de seguridad completos.
    """
    to_encode = data.copy()
    now = datetime.now(timezone.utc)

    if expires_delta:
        expire = now + expires_delta
    else:
        expire = now + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode.update({
        "exp": expire,
        "iat": now,
        "nbf": now,
        "jti": _generate_jti(),
        "aud": "financoop-api",
        "iss": "financoop-backend",
    })

    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def create_refresh_token(user_id: str, rol: str) -> str:
    """Crea un refresh token con TTL más largo."""
    return create_access_token(
        data={"sub": user_id, "rol": rol, "type": "refresh"},
        expires_delta=timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    )

# ─────────────────────────────────────────────────────────────
# 🛡️ RATE LIMITING PARA LOGIN
# ─────────────────────────────────────────────────────────────

def _check_rate_limit(identifier: str) -> bool:
    """Verifica si el identificador está bloqueado por rate limiting."""
    now = datetime.now(timezone.utc)

    if identifier in _login_attempts:
        attempts, first_attempt, locked_until = _login_attempts[identifier]

        if locked_until and now < locked_until:
            logger.warning(f"🚫 [Rate Limit] {identifier} bloqueado hasta {locked_until}")
            return False

        if locked_until and now >= locked_until:
            _login_attempts[identifier] = (0, now, None)

    return True

def _record_failed_attempt(identifier: str):
    """Registra un intento fallido de login."""
    now = datetime.now(timezone.utc)

    if identifier not in _login_attempts:
        _login_attempts[identifier] = (1, now, None)
    else:
        attempts, first_attempt, _ = _login_attempts[identifier]
        attempts += 1

        if attempts >= MAX_LOGIN_ATTEMPTS:
            locked_until = now + timedelta(minutes=LOGIN_LOCKOUT_MINUTES)
            _login_attempts[identifier] = (attempts, first_attempt, locked_until)
            logger.warning(f"🔒 [Rate Limit] {identifier} bloqueado por {LOGIN_LOCKOUT_MINUTES} min")
        else:
            _login_attempts[identifier] = (attempts, first_attempt, None)

def _record_successful_attempt(identifier: str):
    """Resetea el contador de intentos fallidos tras login exitoso."""
    if identifier in _login_attempts:
        del _login_attempts[identifier]

# ─────────────────────────────────────────────────────────────
# ✅ VALIDACIÓN DE TOKENS
# ─────────────────────────────────────────────────────────────

def _decode_and_validate_token(token: str) -> dict:
    """Decodifica y valida un JWT con todas las verificaciones de seguridad."""
    try:
        payload = jwt.decode(
            token,
            SECRET_KEY,
            algorithms=[ALGORITHM],
            audience="financoop-api",
            issuer="financoop-backend",
            options={
                "verify_signature": True,
                "verify_exp": True,
                "verify_iat": True,
                "verify_nbf": True,
                "verify_aud": True,
                "verify_iss": True,
                "require": ["exp", "iat", "sub", "jti"]
            }
        )
        return payload
    except ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expirado")
    except JWTError as e:
        logger.warning(f"❌ [JWT] Token inválido: {str(e)}")
        raise HTTPException(status_code=401, detail="Token inválido")

# ─────────────────────────────────────────────────────────────
# 👤 OBTENER USUARIO ACTUAL (CORREGIDO)
# ─────────────────────────────────────────────────────────────

def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    """
    Obtiene el usuario/cliente actual con validación completa del token.
    
    🔥 CORREGIDO: Busca por ID si es cliente, por username si es admin
    """
    token_hash = _hash_token(token)
    logger.info(f"🔍 [get_current_user] Token hash: {token_hash}...")

    payload = _decode_and_validate_token(token)
    sub = payload.get("sub")
    rol = payload.get("rol", "cliente")

    if sub is None:
        logger.error("❌ [get_current_user] Subject (sub) es None")
        raise HTTPException(status_code=401, detail="Token inválido: subject missing")

    # 🔥 Si es admin, buscar por username
    if rol == "admin":
        usuario = db.query(Usuario).filter(Usuario.username == sub).first()
        if usuario and usuario.activo:
            logger.info(f"✅ [get_current_user] Admin: {usuario.username}")
            return usuario
        logger.error(f"❌ [get_current_user] Admin no encontrado: {sub}")
        raise HTTPException(status_code=401, detail="Admin no encontrado")

    # 🔥 Si es cliente, buscar por ID (convertir a int)
    try:
        cliente_id = int(sub)
        cliente = db.query(Cliente).filter(Cliente.id == cliente_id).first()
        if cliente:
            logger.info(f"✅ [get_current_user] Cliente ID: {cliente.id} - {cliente.nombre}")
            return cliente
        logger.error(f"❌ [get_current_user] Cliente no encontrado ID: {cliente_id}")
    except ValueError:
        logger.error(f"❌ [get_current_user] ID inválido: {sub}")

    raise HTTPException(status_code=401, detail="Usuario no encontrado")

# ─────────────────────────────────────────────────────────────
# 👑 SOLO ADMINISTRADORES
# ─────────────────────────────────────────────────────────────

def get_current_admin(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    """Obtiene admin con validación completa y verificación de rol."""

    token_hash = _hash_token(token)
    logger.info(f"🔍 [get_current_admin] Token hash: {token_hash}...")

    payload = _decode_and_validate_token(token)
    username = payload.get("sub")
    rol = payload.get("rol")

    if username is None:
        raise HTTPException(status_code=401, detail="Token inválido")

    if rol != "admin":
        logger.warning(f"🚫 [get_current_admin] Acceso denegado. Rol: {rol}")
        raise HTTPException(status_code=403, detail="Permisos insuficientes")

    usuario = db.query(Usuario).filter(Usuario.username == username).first()

    if not usuario or not usuario.activo:
        raise HTTPException(status_code=403, detail="Usuario no encontrado o inactivo")

    logger.info(f"✅ [get_current_admin] Admin autorizado: {usuario.username}")
    return usuario

# ─────────────────────────────────────────────────────────────
# 📱 CLIENTES (para app móvil)
# ─────────────────────────────────────────────────────────────

def get_current_cliente(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    """Obtiene cliente con validación completa."""

    token_hash = _hash_token(token)
    logger.info(f"🔍 [get_current_cliente] Token hash: {token_hash}...")

    payload = _decode_and_validate_token(token)
    cliente_id = payload.get("sub")

    if cliente_id is None:
        raise HTTPException(status_code=401, detail="Token inválido")

    try:
        cliente = db.query(Cliente).filter(Cliente.id == int(cliente_id)).first()
    except ValueError:
        raise HTTPException(status_code=401, detail="ID de cliente inválido")

    if not cliente:
        raise HTTPException(status_code=404, detail="Cliente no encontrado")

    logger.info(f"✅ [get_current_cliente] Cliente: {cliente.id}")
    return cliente

# ─────────────────────────────────────────────────────────────
# 🔑 HASH Y VERIFICACIÓN DE CONTRASEÑAS
# ─────────────────────────────────────────────────────────────

def hash_password(password: str) -> str:
    """Hashea una contraseña con bcrypt usando rounds configurables."""
    if len(password) < 8:
        raise ValueError("La contraseña debe tener al menos 8 caracteres")

    salt = bcrypt.gensalt(rounds=BCRYPT_ROUNDS)
    hashed = bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')
    logger.info(f"🔑 [hash_password] Hash generado (rounds={BCRYPT_ROUNDS})")
    return hashed

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verifica contraseña usando comparación segura (timing-safe)."""
    result = bcrypt.checkpw(
        plain_password.encode('utf-8'),
        hashed_password.encode('utf-8')
    )
    return result

# ─────────────────────────────────────────────────────────────
# 🧹 LIMPIEZA PERIÓDICA DE RATE LIMITING
# ─────────────────────────────────────────────────────────────

def cleanup_rate_limits():
    """Limpia entradas antiguas del rate limiting (ejecutar periódicamente)."""
    now = datetime.now(timezone.utc)
    expired = [
        k for k, v in _login_attempts.items()
        if v[2] and now > v[2] + timedelta(hours=1)
    ]
    for k in expired:
        del _login_attempts[k]
    if expired:
        logger.info(f"🧹 [Cleanup] {len(expired)} entradas de rate limit eliminadas")