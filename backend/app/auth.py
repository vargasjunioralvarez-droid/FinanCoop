"""
🔒 FinanCoop - Sistema de Autenticación Ultra-Seguro
Soporte dual: Admin (Frontend Vue) + Cliente (App Móvil)
Hardening contra ataques JWT, fuerza bruta, timing attacks y más.
"""

from fastapi import Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from jose.exceptions import ExpiredSignatureError
from sqlalchemy.orm import Session
from datetime import datetime, timedelta, timezone
from app.database import get_db
from app.models import Cliente, Usuario, TokenBlacklist
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

if len(SECRET_KEY.encode()) < 32:
    raise ValueError("❌ SECRET_KEY debe tener al menos 32 caracteres (256 bits)")

ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "15"))
REFRESH_TOKEN_EXPIRE_DAYS = int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", "7"))
BCRYPT_ROUNDS = int(os.getenv("BCRYPT_ROUNDS", "12"))
MAX_LOGIN_ATTEMPTS = int(os.getenv("MAX_LOGIN_ATTEMPTS", "5"))
LOGIN_LOCKOUT_MINUTES = int(os.getenv("LOGIN_LOCKOUT_MINUTES", "15"))

# Intentar Redis para rate limiting distribuido
try:
    import redis
    REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    redis_client = redis.from_url(REDIS_URL, decode_responses=True)
    redis_client.ping()
    USE_REDIS = True
except (ImportError, Exception):
    USE_REDIS = False
    _login_attempts = {}

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")

# ─────────────────────────────────────────────────────────────
# 🔐 UTILIDADES CRIPTOGRÁFICAS
# ─────────────────────────────────────────────────────────────

def _secure_compare(a: str, b: str) -> bool:
    """Comparación constant-time para prevenir timing attacks."""
    return hmac.compare_digest(a.encode(), b.encode())

def _hash_token(token: str) -> str:
    """Hash SHA-256 del token para logging seguro."""
    return hashlib.sha256(token.encode()).hexdigest()[:16]

def _generate_jti() -> str:
    """Genera un JWT ID único."""
    return secrets.token_urlsafe(32)

# ─────────────────────────────────────────────────────────────
# 🛡️ RATE LIMITING (Redis o memoria)
# ─────────────────────────────────────────────────────────────

def _check_rate_limit(identifier: str) -> bool:
    """Verifica si el identificador está bloqueado."""
    now = datetime.now(timezone.utc)
    
    if USE_REDIS:
        key = f"rate_limit:{identifier}"
        attempts = redis_client.get(key)
        if attempts and int(attempts) >= MAX_LOGIN_ATTEMPTS:
            ttl = redis_client.ttl(key)
            if ttl > 0:
                logger.warning(f"🚫 [Rate Limit] {identifier} bloqueado por {ttl}s")
                return False
        return True
    else:
        if identifier in _login_attempts:
            attempts, first_attempt, locked_until = _login_attempts[identifier]
            if locked_until and now < locked_until:
                remaining = int((locked_until - now).total_seconds())
                logger.warning(f"🚫 [Rate Limit] {identifier} bloqueado por {remaining}s")
                return False
            if locked_until and now >= locked_until:
                del _login_attempts[identifier]
        return True

def _record_failed_attempt(identifier: str):
    """Registra intento fallido."""
    now = datetime.now(timezone.utc)
    
    if USE_REDIS:
        key = f"rate_limit:{identifier}"
        attempts = redis_client.incr(key)
        if attempts == 1:
            redis_client.expire(key, LOGIN_LOCKOUT_MINUTES * 60)
        if attempts >= MAX_LOGIN_ATTEMPTS:
            logger.warning(f"🔒 [Rate Limit] {identifier} bloqueado por {LOGIN_LOCKOUT_MINUTES} min")
    else:
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
    """Resetea contador tras login exitoso."""
    if USE_REDIS:
        redis_client.delete(f"rate_limit:{identifier}")
    else:
        if identifier in _login_attempts:
            del _login_attempts[identifier]

# ─────────────────────────────────────────────────────────────
# 🎫 CREACIÓN DE TOKENS
# ─────────────────────────────────────────────────────────────

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Crea JWT de acceso con claims de seguridad completos."""
    to_encode = data.copy()
    now = datetime.now(timezone.utc)
    expire = now + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    
    to_encode.update({
        "exp": expire,
        "iat": now,
        "nbf": now,
        "jti": _generate_jti(),
        "aud": "financoop-api",
        "iss": "financoop-backend"
    })
    
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def create_refresh_token(user_id: str, rol: str) -> str:
    """Crea refresh token con TTL más largo."""
    return create_access_token(
        data={"sub": user_id, "rol": rol, "type": "refresh"},
        expires_delta=timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    )

# ─────────────────────────────────────────────────────────────
# ✅ VALIDACIÓN DE TOKENS
# ─────────────────────────────────────────────────────────────

def _decode_and_validate_token(token: str, db: Optional[Session] = None) -> dict:
    """Decodifica y valida JWT con todas las verificaciones."""
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
        
        # Verificar blacklist si hay DB
        if db:
            jti = payload.get("jti")
            blacklisted = db.query(TokenBlacklist).filter(TokenBlacklist.jti == jti).first()
            if blacklisted:
                raise HTTPException(status_code=401, detail="Token revocado")
        
        return payload
    except ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expirado")
    except JWTError as e:
        logger.warning(f"❌ [JWT] Token inválido: {str(e)}")
        raise HTTPException(status_code=401, detail="Token inválido")

# ─────────────────────────────────────────────────────────────
# 👤 OBTENER USUARIO ACTUAL (Admin o Cliente)
# ─────────────────────────────────────────────────────────────

def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    """Obtiene usuario/cliente actual con validación completa."""
    token_hash = _hash_token(token)
    logger.info(f"🔍 [get_current_user] Token hash: {token_hash}...")

    payload = _decode_and_validate_token(token, db)
    sub = payload.get("sub")
    rol = payload.get("rol", "cliente")

    if sub is None:
        logger.error("❌ [get_current_user] Subject es None")
        raise HTTPException(status_code=401, detail="Token inválido")

    # Admin: buscar por username
    if rol == "admin":
        usuario = db.query(Usuario).filter(Usuario.username == sub, Usuario.activo == True).first()
        if usuario:
            logger.info(f"✅ [get_current_user] Admin: {usuario.username}")
            return usuario
        logger.error(f"❌ [get_current_user] Admin no encontrado: {sub}")
        raise HTTPException(status_code=401, detail="Usuario no encontrado o inactivo")

    # Cliente: buscar por ID
    try:
        cliente_id = int(sub)
        cliente = db.query(Cliente).filter(Cliente.id == cliente_id).first()
        if cliente:
            logger.info(f"✅ [get_current_user] Cliente ID: {cliente.id}")
            return cliente
        logger.error(f"❌ [get_current_user] Cliente no encontrado ID: {cliente_id}")
    except ValueError:
        logger.error(f"❌ [get_current_user] ID inválido: {sub}")

    raise HTTPException(status_code=401, detail="Usuario no encontrado")

# ─────────────────────────────────────────────────────────────
# 👑 SOLO ADMINISTRADORES
# ─────────────────────────────────────────────────────────────

def get_current_admin(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    """Obtiene admin con validación y verificación de rol."""
    token_hash = _hash_token(token)
    logger.info(f"🔍 [get_current_admin] Token hash: {token_hash}...")

    payload = _decode_and_validate_token(token, db)
    username = payload.get("sub")
    rol = payload.get("rol")

    if username is None:
        raise HTTPException(status_code=401, detail="Token inválido")

    if rol != "admin":
        logger.warning(f"🚫 [get_current_admin] Acceso denegado. Rol: {rol}")
        raise HTTPException(status_code=403, detail="Permisos insuficientes")

    usuario = db.query(Usuario).filter(Usuario.username == username, Usuario.activo == True).first()
    if not usuario:
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

    payload = _decode_and_validate_token(token, db)
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
# 🔑 HASH Y VERIFICACIÓN DE CONTRASEÑAS Y PIN
# ─────────────────────────────────────────────────────────────

def hash_password(password: str) -> str:
    """Hashea contraseña con bcrypt."""
    if len(password) < 8:
        raise ValueError("La contraseña debe tener al menos 8 caracteres")
    salt = bcrypt.gensalt(rounds=BCRYPT_ROUNDS)
    return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')

def hash_pin(pin: str) -> str:
    """Hashea PIN con bcrypt (misma seguridad que contraseña)."""
    if len(pin) < 4:
        raise ValueError("El PIN debe tener al menos 4 caracteres")
    salt = bcrypt.gensalt(rounds=BCRYPT_ROUNDS)
    return bcrypt.hashpw(pin.encode('utf-8'), salt).decode('utf-8')

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verifica contraseña con comparación timing-safe."""
    return bcrypt.checkpw(
        plain_password.encode('utf-8'),
        hashed_password.encode('utf-8')
    )

def verify_pin(plain_pin: str, hashed_pin: str) -> bool:
    """Verifica PIN con comparación timing-safe."""
    return bcrypt.checkpw(
        plain_pin.encode('utf-8'),
        hashed_pin.encode('utf-8')
    )

# ─────────────────────────────────────────────────────────────
# 🗑️ BLACKLIST DE TOKENS (Logout real)
# ─────────────────────────────────────────────────────────────

def blacklist_token(jti: str, exp: datetime, db: Session):
    """Agrega token a blacklist para prevenir reuso después de logout."""
    blacklisted = TokenBlacklist(jti=jti, expira_en=exp)
    db.add(blacklisted)
    db.commit()

def is_token_blacklisted(jti: str, db: Session) -> bool:
    """Verifica si un token está en blacklist."""
    return db.query(TokenBlacklist).filter(TokenBlacklist.jti == jti).first() is not None

# ─────────────────────────────────────────────────────────────
# 🧹 LIMPIEZA DE RATE LIMITING
# ─────────────────────────────────────────────────────────────

def cleanup_rate_limits():
    """Limpia entradas antiguas del rate limiting."""
    if USE_REDIS:
        return  # Redis maneja expiración automáticamente
    now = datetime.now(timezone.utc)
    expired = [
        k for k, v in _login_attempts.items()
        if v[2] and now > v[2] + timedelta(hours=1)
    ]
    for k in expired:
        del _login_attempts[k]
    if expired:
        logger.info(f"🧹 [Cleanup] {len(expired)} entradas de rate limit eliminadas")