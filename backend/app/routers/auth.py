# backend/app/routers/auth.py
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel
from sqlalchemy.orm import Session
from datetime import datetime
import logging

from app.database import get_db
from app.models import Usuario, Cliente
from app.auth import create_access_token, get_current_cliente, get_current_admin, hash_password, verify_password

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["Autenticación"])

# ============================================================
# ✅ MODELO PARA LOGIN DE CLIENTE (JSON body)
# ============================================================
class LoginClienteRequest(BaseModel):
    cedula: str
    pin: str

# ============================================================
# ✅ LOGIN PARA CLIENTES (APP MÓVIL) - CORREGIDO PARA JSON
# ============================================================
@router.post("/login-cliente")
def login_cliente(request: LoginClienteRequest, db: Session = Depends(get_db)):
    cedula = request.cedula
    pin = request.pin
    
    logger.info(f"🚀 [BACKEND] Login cliente - Cédula: {cedula}")
    
    cliente = db.query(Cliente).filter(Cliente.cedula == cedula).first()
    
    if not cliente:
        logger.warning(f"❌ [BACKEND] Cliente no encontrado: {cedula}")
        raise HTTPException(status_code=401, detail="Cliente no encontrado")
    
    if cliente.pin != pin:
        logger.warning(f"❌ [BACKEND] PIN incorrecto para cédula: {cedula}")
        raise HTTPException(status_code=401, detail="PIN incorrecto")
    
    # Actualizar último acceso
    cliente.ultimo_acceso = datetime.now()
    db.commit()
    
    # Crear token
    token = create_access_token(data={"sub": str(cliente.id), "rol": "cliente"})
    logger.info(f"🔑 [BACKEND] Token generado para cliente {cliente.id}")
    
    response = {
        "access_token": token,
        "token_type": "bearer",
        "cliente": {
            "id": cliente.id,
            "nombre": cliente.nombre,
            "cedula": cliente.cedula,
            "nivel": cliente.nivel,
            "score": cliente.score
        }
    }
    logger.info(f"📤 [BACKEND] Enviando respuesta exitosa")
    return response

# ============================================================
# ✅ LOGIN PARA ADMINISTRADORES (PANEL WEB) - SIN CAMBIOS
# ============================================================
@router.post("/login")
def login_admin(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    logger.info(f"🚀 [BACKEND] Login admin - Username: {form_data.username}")
    
    usuario = db.query(Usuario).filter(Usuario.username == form_data.username).first()
    
    if not usuario or not verify_password(form_data.password, usuario.password):
        logger.warning(f"❌ [BACKEND] Admin credenciales incorrectas: {form_data.username}")
        raise HTTPException(status_code=401, detail="Credenciales incorrectas")
    
    if not usuario.activo:
        logger.warning(f"❌ [BACKEND] Usuario inactivo: {form_data.username}")
        raise HTTPException(status_code=403, detail="Usuario inactivo")
    
    token = create_access_token(data={"sub": usuario.username, "rol": usuario.rol})
    logger.info(f"🔑 [BACKEND] Token admin generado para {usuario.username}")
    
    return {
        "access_token": token,
        "token_type": "bearer",
        "rol": usuario.rol,
        "username": usuario.username,
        "nombre": usuario.nombre
    }

# ============================================================
# ✅ REGISTRO DE ADMINISTRADOR
# ============================================================
@router.post("/registro")
def registrar_usuario(username: str, password: str, rol: str = "usuario", db: Session = Depends(get_db)):
    logger.info(f"🚀 [BACKEND] Registro de usuario: {username}")
    
    existe = db.query(Usuario).filter(Usuario.username == username).first()
    if existe:
        logger.warning(f"❌ [BACKEND] Usuario ya existe: {username}")
        raise HTTPException(status_code=400, detail="El usuario ya existe")
    
    nuevo = Usuario(
        username=username,
        password=hash_password(password),
        rol=rol,
        nombre=username
    )
    db.add(nuevo)
    db.commit()
    
    logger.info(f"✅ [BACKEND] Usuario creado: {username}")
    return {"mensaje": "Usuario creado", "username": username, "rol": rol}

# ============================================================
# ✅ VERIFICAR TOKEN
# ============================================================
@router.get("/verificar")
def verificar_token(current_user: Usuario = Depends(get_current_admin)):
    logger.info(f"🔍 [BACKEND] Verificando token para: {current_user.username}")
    return {"valid": True, "username": current_user.username, "rol": current_user.rol}