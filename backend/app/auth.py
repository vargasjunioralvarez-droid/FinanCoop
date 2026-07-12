# backend/app/auth.py
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from app.database import get_db
from app.models import Cliente, Usuario
import os
import bcrypt
import logging

# Configurar logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

SECRET_KEY = os.getenv("SECRET_KEY", "supersecretkey")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24  # 24 horas

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

def create_access_token(data: dict, expires_delta: timedelta = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now() + expires_delta
    else:
        expire = datetime.now() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

# ============================================================
# ✅ FUNCIONES PARA HASH DE CONTRASEÑAS
# ============================================================
def hash_password(password: str) -> str:
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))

# ============================================================
# ✅ CUALQUIER USUARIO AUTENTICADO (admin, cajero, usuario)
# ============================================================
def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    logger.info("=" * 50)
    logger.info("🔍 [get_current_user] INICIO")
    logger.info(f"🔍 [get_current_user] Token recibido: {token[:30]}...")
    
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username = payload.get("sub")
        rol = payload.get("rol")
        
        logger.info(f"🔍 [get_current_user] Username: {username}, Rol: {rol}")
        
        if username is None:
            logger.error("❌ [get_current_user] Username es None")
            raise HTTPException(status_code=401, detail="Token inválido")
    except JWTError as e:
        logger.error(f"❌ [get_current_user] Error JWT: {e}")
        raise HTTPException(status_code=401, detail="Token inválido")
    
    # Buscar en Usuario primero (admin, cajero, usuario del sistema)
    usuario = db.query(Usuario).filter(Usuario.username == username).first()
    if usuario and usuario.activo:
        logger.info(f"✅ [get_current_user] Usuario encontrado: {usuario.username}")
        return usuario
    
    # Si no es usuario del sistema, buscar en Cliente
    try:
        cliente_id = int(username)
        cliente = db.query(Cliente).filter(Cliente.id == cliente_id).first()
        if cliente:
            logger.info(f"✅ [get_current_user] Cliente encontrado: {cliente.id}")
            return cliente
    except ValueError:
        pass
    
    logger.error(f"❌ [get_current_user] Usuario no encontrado: {username}")
    raise HTTPException(status_code=401, detail="Usuario no encontrado")

# ============================================================
# ✅ SOLO ADMINISTRADORES - CORREGIDO CON LOGS
# ============================================================
def get_current_admin(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    logger.info("=" * 50)
    logger.info("🔍 [get_current_admin] INICIO")
    logger.info(f"🔍 [get_current_admin] Token recibido: {token[:30]}...")
    
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username = payload.get("sub")
        rol = payload.get("rol")
        
        logger.info(f"🔍 [get_current_admin] Username extraído: {username}")
        logger.info(f"🔍 [get_current_admin] Rol extraído: {rol}")
        
        if username is None:
            logger.error("❌ [get_current_admin] Username es None")
            raise HTTPException(status_code=401, detail="Token inválido: username missing")
        
        if rol != "admin":
            logger.error(f"❌ [get_current_admin] Rol no es admin: {rol}")
            raise HTTPException(status_code=403, detail=f"No tienes permisos de administrador. Tu rol: {rol}")
        
        logger.info(f"✅ [get_current_admin] Rol validado: {rol}")
        
    except JWTError as e:
        logger.error(f"❌ [get_current_admin] Error JWT: {e}")
        raise HTTPException(status_code=401, detail=f"Token inválido: {str(e)}")
    except Exception as e:
        logger.error(f"❌ [get_current_admin] Error inesperado: {e}")
        raise HTTPException(status_code=401, detail=f"Error: {str(e)}")
    
    # Buscar usuario en BD
    logger.info(f"🔍 [get_current_admin] Buscando usuario: {username}")
    usuario = db.query(Usuario).filter(Usuario.username == username).first()
    
    if not usuario:
        logger.error(f"❌ [get_current_admin] Usuario no encontrado: {username}")
        raise HTTPException(status_code=403, detail="Usuario no encontrado")
    
    if not usuario.activo:
        logger.error(f"❌ [get_current_admin] Usuario inactivo: {username}")
        raise HTTPException(status_code=403, detail="Usuario inactivo")
    
    logger.info(f"✅ [get_current_admin] Usuario autorizado: {usuario.username} (rol: {usuario.rol})")
    logger.info("=" * 50)
    return usuario

# ============================================================
# ✅ CLIENTES (para la app móvil)
# ============================================================
def get_current_cliente(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        cliente_id = payload.get("sub")
        if cliente_id is None:
            raise HTTPException(status_code=401, detail="Token inválido")
    except JWTError:
        raise HTTPException(status_code=401, detail="Token inválido")
    
    cliente = db.query(Cliente).filter(Cliente.id == int(cliente_id)).first()
    if not cliente:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    return cliente