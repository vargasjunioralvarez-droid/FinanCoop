"""
🔒 FinanCoop - Sistema de Autenticación Ultra-Seguro
Soporte dual: Admin (Frontend Vue) + Cliente (App Móvil)
Multi-tienda: admin_central ve todo, admin_tienda ve su tienda, cajero ve su tienda
"""

from fastapi import Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from jose.exceptions import ExpiredSignatureError
from sqlalchemy.orm import Session
from datetime import datetime, timedelta, timezone
from app.core.database import get_db
from app.modules.users.models import Cliente, Usuario
from app.modules.auth.models import TokenBlacklist
import os
import bcrypt
import logging
import secrets
import hashlib
import hmac
import redis
from typing import Optional, Union

# Configurar logger
logger = logging.getLogger(__name__)

# ──────────────────────────────────────────────────────────────
# 🛡️ CONFIGURACIÓN DE SEGURIDAD (ahora desde config central)
# ──────────────────────────────────────────────────────────────

from app.core.config import settings

SECRET_KEY = settings.JWT_SECRET_KEY
ALGORITHM = settings.JWT_ALGORITHM
ACCESS_TOKEN_EXPIRE_MINUTES = settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES
REFRESH_TOKEN_EXPIRE_DAYS = settings.REFRESH_TOKEN_EXPIRE_DAYS

BCRYPT_ROUNDS = 12
MAX_LOGIN_ATTEMPTS = 5
LOGIN_LOCKOUT_MINUTES = 15

# ──────────────────────────────────────────────────────────────
# 🔴 REDIS (Rate Limiting compartido + Recuperación de PIN)
# ──────────────────────────────────────────────────────────────

REDIS_URL = os.getenv("REDIS_URL")
USE_REDIS = REDIS_URL is not None
redis_client = None

if USE_REDIS:
    try:
        redis_client = redis.from_url(REDIS_URL, ssl=True)
        redis_client.ping()
        logger.info("✅ Redis conectado correctamente")
    except Exception as e:
        logger.warning(f"⚠️ No se pudo conectar a Redis: {e}. Usando memoria local.")
        USE_REDIS = False

# ──────────────────────────────────────────────────────────────
# 🔑 OAUTH2 SCHEMES
# ──────────────────────────────────────────────────────────────

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token", auto_error=True)
oauth2_scheme_optional = OAuth2PasswordBearer(tokenUrl="token", auto_error=False)

# ──────────────────────────────────────────────────────────────
# 🛡️ RATE LIMITING (mantenemos tu código)
# ──────────────────────────────────────────────────────────────

_login_attempts = {}

def _secure_compare(a: str, b: str) -> bool:
    return hmac.compare_digest(a.encode(), b.encode())

def _hash_token(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()[:16]

def _generate_jti() -> str:
    return secrets.token_urlsafe(32)

def _check_rate_limit(identifier: str) -> bool:
    now = datetime.now(timezone.utc)
    if USE_REDIS and redis_client:
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
    if USE_REDIS and redis_client:
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
    if USE_REDIS and redis_client:
        redis_client.delete(f"rate_limit:{identifier}")
    else:
        if identifier in _login_attempts:
            del _login_attempts[identifier]

# ──────────────────────────────────────────────────────────────
# 🎫 CREACIÓN DE TOKENS (mantenemos tu código)
# ──────────────────────────────────────────────────────────────

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

# ──────────────────────────────────────────────────────────────
# ✅ VALIDACIÓN DE TOKENS (mantenemos tu código)
# ──────────────────────────────────────────────────────────────

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
        logger.warning(f"Error de token: {str(e)}")
        raise HTTPException(status_code=401, detail="Token inválido")

# ──────────────────────────────────────────────────────────────
# 👤 OBTENER USUARIO ACTUAL (mantenemos tu código)
# ──────────────────────────────────────────────────────────────

def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    payload = _decode_and_validate_token(token, db)
    sub = payload.get("sub")
    rol = payload.get("rol", "cliente")

    if sub is None:
        raise HTTPException(status_code=401, detail="Token inválido")

    if rol in ["admin", "admin_central", "admin_tienda", "tienda", "cajero"]:
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

# ──────────────────────────────────────────────────────────────
# 👤 USUARIO OPCIONAL (mantenemos tu código)
# ──────────────────────────────────────────────────────────────

def get_current_user_optional(
    token: str = Depends(oauth2_scheme_optional), 
    db: Session = Depends(get_db)
):
    if not token:
        return None
    try:
        payload = _decode_and_validate_token(token, db)
        sub = payload.get("sub")
        rol = payload.get("rol", "cliente")

        if sub is None:
            return None

        if rol in ["admin", "admin_central", "admin_tienda", "tienda", "cajero"]:
            usuario = db.query(Usuario).filter(Usuario.username == sub, Usuario.activo == True).first()
            return usuario

        try:
            cliente_id = int(sub)
            cliente = db.query(Cliente).filter(Cliente.id == cliente_id).first()
            return cliente
        except ValueError:
            return None
    except:
        return None

# ──────────────────────────────────────────────────────────────
# 👑 OBTENER ADMIN (mantenemos tu código)
# ──────────────────────────────────────────────────────────────

def get_current_admin(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    payload = _decode_and_validate_token(token, db)
    username = payload.get("sub")
    rol = payload.get("rol")

    if rol not in ["admin_central", "admin_tienda", "cajero"]:
        raise HTTPException(status_code=403, detail="Permisos insuficientes")

    usuario = db.query(Usuario).filter(Usuario.username == username, Usuario.activo == True).first()
    if not usuario:
        raise HTTPException(status_code=403, detail="Usuario no encontrado o inactivo")
    return usuario

# ──────────────────────────────────────────────────────────────
# 📱 CLIENTES (app móvil) (mantenemos tu código)
# ──────────────────────────────────────────────────────────────

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

# ──────────────────────────────────────────────────────────────
# 🏪 OBTENER TIENDA DEL USUARIO ACTUAL (mantenemos tu código)
# ──────────────────────────────────────────────────────────────

def get_current_tienda(current_user = Depends(get_current_user)):
    if hasattr(current_user, 'rol') and current_user.rol == "admin_central":
        return None
    return getattr(current_user, 'tienda_id', None)

# ──────────────────────────────────────────────────────────────
# 🔑 HASH Y VERIFICACIÓN (mantenemos tu código)
# ──────────────────────────────────────────────────────────────

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

# ──────────────────────────────────────────────────────────────
# 🗑️ BLACKLIST DE TOKENS (mantenemos tu código)
# ──────────────────────────────────────────────────────────────

def blacklist_token(jti: str, exp: datetime, db: Session):
    blacklisted = TokenBlacklist(jti=jti, expira_en=exp)
    db.add(blacklisted)
    db.commit()