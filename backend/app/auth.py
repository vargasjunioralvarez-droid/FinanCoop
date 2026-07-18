"""
🔒 FinanCoop - Sistema de Autenticación Ultra-Seguro
Soporte dual: Admin (Frontend Vue) + Cliente (App Móvil)
Multi-tienda: Admin ve todo, Tienda ve solo lo suyo
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
    return hmac.compare_digest(a.encode(), b.encode())

def _hash_token(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()[:16]

def _generate_jti() -> str:
    return secrets.token_urlsafe(32)

# ─────────────────────────────────────────────────────────────
# 🛡️ RATE LIMITING
# ─────────────────────────────────────────────────────────────

def _check_rate_limit(identifier: str) -> bool:
    now = datetime.now(timezone.utc)
    if USE_REDIS:
        key = f"rate_limit:{identifier}"
        attempts = redis_client.get(key)
        if attempts and int(attempts) >= MAX_LOGIN_ATTEMPTS:
            ttl = redis_client.ttl(key)
            if ttl > 0:
                return False
        return True
    else:
        if identifier in _login_attempts:
            attempts, first_attempt, locked_until = _login_attempts[identifier]
            if locked_until and now < locked_until:
                return False
            if locked_until and now >= locked_until:
                del _login_attempts[identifier]
        return True

def _record_failed_attempt(identifier: str):
    now = datetime.now(timezone.utc)
    if USE_REDIS:
        key = f"rate_limit:{identifier}"
        attempts = redis_client.incr(key)
        if attempts == 1:
            redis_client.expire(key, LOGIN_LOCKOUT_MINUTES * 60)
    else:
        if identifier not in _login_attempts:
            _login_attempts[identifier] = (1, now, None)
        else:
            attempts, first_attempt, _ = _login_attempts[identifier]
            attempts += 1
            if attempts >= MAX_LOGIN_ATTEMPTS:
                locked_until = now + timedelta(minutes=LOGIN_LOCKOUT_MINUTES)
                _login_attempts[identifier] = (attempts, first_attempt, locked_until)

def _record_successful_attempt(identifier: str):
    if USE_REDIS:
        redis_client.delete(f"rate_limit:{identifier}")
    else:
        if identifier in _login_attempts:
            del _login_attempts[identifier]

# ─────────────────────────────────────────────────────────────
# 🎫 CREACIÓN DE TOKENS
# ─────────────────────────────────────────────────────────────

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    now = datetime.now(timezone.utc)
    expire = now + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({
        "exp": expire, "iat": now, "nbf": now,
        "jti": _generate_jti(),
        "aud": "financoop-api", "iss": "financoop-backend"
    })
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def create_refresh_token(user_id: str, rol: str) -> str:
    return create_access_token(
        data={"sub": user_id, "rol": rol, "type": "refresh"},
        expires_delta=timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    )

# ─────────────────────────────────────────────────────────────
# ✅ VALIDACIÓN DE TOKENS
# ─────────────────────────────────────────────────────────────

def _decode_and_validate_token(token: str, db: Optional[Session] = None) -> dict:
    try:
        payload = jwt.decode(
            token, SECRET_KEY, algorithms=[ALGORITHM],
            audience="financoop-api", issuer="financoop-backend",
            options={
                "verify_signature": True, "verify_exp": True,
                "verify_iat": True, "verify_nbf": True,
                "verify_aud": True, "verify_iss": True,
                "require": ["exp", "iat", "sub", "jti"]
            }
        )
        if db:
            jti = payload.get("jti")
            blacklisted = db.query(TokenBlacklist).filter(TokenBlacklist.jti == jti).first()
            if blacklisted:
                raise HTTPException(status_code=401, detail="Token revocado")
        return payload
    except ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expirado")
    except JWTError as e:
        raise HTTPException(status_code=401, detail="Token inválido")

# ─────────────────────────────────────────────────────────────
# 👤 OBTENER USUARIO ACTUAL
# ─────────────────────────────────────────────────────────────

def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    payload = _decode_and_validate_token(token, db)
    sub = payload.get("sub")
    rol = payload.get("rol", "cliente")

    if sub is None:
        raise HTTPException(status_code=401, detail="Token inválido")

    if rol == "admin" or rol == "tienda" or rol == "cajero":
        usuario = db.query(Usuario).filter(Usuario.username == sub, Usuario.activo == True).first()
        if usuario:
            return usuario
        raise HTTPException(status_code=401, detail="Usuario no encontrado o inactivo")

    try:
        cliente_id = int(sub)
        cliente = db.query(Cliente).filter(Cliente.id == cliente_id).first()
        if cliente:
            return cliente
    except ValueError:
        pass

    raise HTTPException(status_code=401, detail="Usuario no encontrado")

# ─────────────────────────────────────────────────────────────
# 👑 SOLO ADMINISTRADORES (admin central)
# ─────────────────────────────────────────────────────────────

def get_current_admin(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    payload = _decode_and_validate_token(token, db)
    username = payload.get("sub")
    rol = payload.get("rol")

    if username is None:
        raise HTTPException(status_code=401, detail="Token inválido")

    if rol not in ["admin", "tienda", "cajero"]:
        raise HTTPException(status_code=403, detail="Permisos insuficientes")

    usuario = db.query(Usuario).filter(Usuario.username == username, Usuario.activo == True).first()
    if not usuario:
        raise HTTPException(status_code=403, detail="Usuario no encontrado o inactivo")

    return usuario

# ─────────────────────────────────────────────────────────────
# 📱 CLIENTES (app móvil)
# ─────────────────────────────────────────────────────────────

def get_current_cliente(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
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

    return cliente

# ─────────────────────────────────────────────────────────────
# 🏪 OBTENER TIENDA DEL USUARIO ACTUAL (NUEVO)
# ─────────────────────────────────────────────────────────────

def get_current_tienda(
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Retorna el tienda_id del usuario actual.
    - Admin (rol='admin'): retorna None (ve todo)
    - Tienda/Cajero: retorna su tienda_id (solo ve su tienda)
    """
    if hasattr(current_user, 'rol') and current_user.rol == "admin":
        return None
    return getattr(current_user, 'tienda_id', None)

# ─────────────────────────────────────────────────────────────
# 🔑 HASH Y VERIFICACIÓN
# ─────────────────────────────────────────────────────────────

def hash_password(password: str) -> str:
    if len(password) < 8:
        raise ValueError("La contraseña debe tener al menos 8 caracteres")
    salt = bcrypt.gensalt(rounds=BCRYPT_ROUNDS)
    return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')

def hash_pin(pin: str) -> str:
    if len(pin) < 4:
        raise ValueError("El PIN debe tener al menos 4 caracteres")
    salt = bcrypt.gensalt(rounds=BCRYPT_ROUNDS)
    return bcrypt.hashpw(pin.encode('utf-8'), salt).decode('utf-8')

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))

def verify_pin(plain_pin: str, hashed_pin: str) -> bool:
    return bcrypt.checkpw(plain_pin.encode('utf-8'), hashed_pin.encode('utf-8'))

# ─────────────────────────────────────────────────────────────
# 🗑️ BLACKLIST DE TOKENS
# ─────────────────────────────────────────────────────────────

def blacklist_token(jti: str, exp: datetime, db: Session):
    blacklisted = TokenBlacklist(jti=jti, expira_en=exp)
    db.add(blacklisted)
    db.commit()